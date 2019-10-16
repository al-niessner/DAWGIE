'''
--
COPYRIGHT:
Copyright (c) 2015-2019, California Institute of Technology ("Caltech").
U.S. Government sponsorship acknowledged.

All rights reserved.

LICENSE:
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

- Neither the name of Caltech nor its operating division, the Jet
Propulsion Laboratory, nor the names of its contributors may be used to
endorse or promote products derived from this software without specific prior
written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

NTR: 49811
'''

import collections
import datetime
import enum
import getpass
import logging
import os
import resource

# pylint: disable=attribute-defined-outside-init,no-self-use,protected-access,too-many-arguments

# factory : the task factory that would normally create this algorithm
# impl : an instance of the algorithm
ALG_REF = collections.namedtuple ('ALG_REF', ['factory', 'impl'])

# factory : the task/analysis factory
# name : name of the algorithm within related to the factory
EVENT = collections.namedtuple ('EVENT', ['algref', 'moment'])

# see resource.getrusage()
# input  : number of times the filesystem had to perform input  [ru_inblock]
# mem    : maximum resident set size used (in kilobytes)        [ru_maxrss]
# output : number of times the filesystem had to perform output [ru_oublock]
# pages  : number of page faults serviced that required I/O     [ru_majflt]
# sys    : total amount of time spent executing in kernel mode  [ru_stime]
# user   : total amount of time spent executing in user mode    [ru_utime]
METRIC = collections.namedtuple ('METRICS', ['input', 'mem', 'output',
                                             'pages', 'sys', 'user'])
# day : an instance of an object that describes a calendar date
#       known working instances are:
# dom : day-of-month or int from 1-31
# dow : day-of-week from calendar
# time: an instance of datetime.time and tzone will be assigned UTC if None
#
# Only one of boot, date, dom, or dow should be defined
MOMENT = collections.namedtuple ('MOMENT', ['boot','day','dom','dow','time'])

def schedule(factory, impl,
             boot:bool=None,
             day:datetime.date=None, dom:int=None,
             dow:int=None, time:datetime.time=None):
    not_defined = [boot is None, day is None, dom is None, dow is None]

    if sum (not_defined) != len (not_defined)-1:
        raise ValueError('One and only one of boot, day, dom, or dow ' +
                         'should be defined.')
    if day and not isinstance (day, datetime.date):
        raise ValueError('day must be of datetime.date')
    if dom and not isinstance (dom, int):
        raise ValueError('dom must be an integer')
    if dow and not isinstance (dow, int):
        raise ValueError('dow must be an integer')
    if not boot and (time and not isinstance (time, datetime.time)):
        raise ValueError('time must be of datetime.time')

    return EVENT(ALG_REF(factory, impl), MOMENT(boot, day, dom, dow, time))

# factory : the task factory that would normally create this algorithm
# impl : an instance of the algorithm
# item : an instance of the state vector from the algorithm
SV_REF = collections.namedtuple ('SV_REF', ['factory', 'impl', 'item'])

# factory : the task factory that would normally create this algorithm
# impl : an instance of the algorithm
# item : an instance of the state vector from the algorithm
# feat : a string to use as the key in the state vector
V_REF = collections.namedtuple ('V_REF', ['factory', 'impl', 'item', 'feat'])


#
# The tuple for versioning that survives pickling correctly.
#
VERSION = collections.namedtuple('VERSION', ['design', 'impl', 'bugfix'])


# An exception to abort processing order that is initiated from anywhere deep
# in the AE.
class AbortAEError(RuntimeError): pass

# These two exceptions are used to help the pipeline understand the data flow.
# The appropriate exception should be used to terminate processing at the
# current task/algorithm.
class NoValidInputDataError(ValueError): pass
class NoValidOutputDataError(ValueError): pass

# This exception is for the pipeline to signal that the AE is not complaint
# with the architecture since not all checks can be done statically with
# tools/compliant.py
class NotValidImplementationError(ValueError): pass

# An enumeration of allowable ways to distribute an algorithm, analyzer,
# or regression
@enum.unique
class Distribution(enum.Enum):
    auto = None      # Place holder for default where()
    cloud = True     # No IO other than the db (db can access S3)
    cluster = False  # Allows IO (could be a mirrored cluster)
    pass

# An enumeration of allowable factories in ae/<task>/__init__.py
class Factories(enum.Enum):
    analysis = enum.auto()  # create an dawgie.Analysis for all targets
    events = enum.auto()    # list of dawgie.EVENT
    regress = enum.auto()   # create an dawgie.Regression for a target
    task = enum.auto()      # create an dawgie.Task for a target

    @staticmethod
    def resolve (reference): return Factories[reference.factory.__name__]
    pass

###
# Below are the interfaces that developers must use
###

class _Metric(object):
    '''Interface used internally to measure process resource usage'''
    def __init__(self):
        self.__history = []
        self.msv = None
        return

    @staticmethod
    def diff (a, b)->METRIC:
        '''compute a - b'''
        return METRIC(input=a.ru_inblock - b.ru_inblock,
                      mem=a.ru_maxrss - b.ru_maxrss,
                      output=a.ru_oublock - b.ru_oublock,
                      pages=a.ru_majflt - b.ru_majflt,
                      sys=a.ru_stime - b.ru_stime,
                      user=a.ru_utime - b.ru_utime)

    def measure (self, func, args=(), ds:'Dataset'=None):
        c0 = resource.getrusage (resource.RUSAGE_CHILDREN)
        s0 = resource.getrusage (resource.RUSAGE_SELF)
        value = func (*args)
        c1 = resource.getrusage (resource.RUSAGE_CHILDREN)
        s1 = resource.getrusage (resource.RUSAGE_SELF)
        child = _Metric.diff (c1, c0)
        task = _Metric.diff (s1, s0)
        self.__history.append ({'child':child, 'task':task})

        if ds:
            import dawgie.db
            import dawgie.util

            db = ds.sum()
            task = self.sum()
            ds._update_msv (dawgie.util.MetricStateVector(db,task))
            pass
        return value

    def sum (self):
        '''return the sum of all collected metrics'''
        s = METRIC(input=0, mem=0, output=0, pages=0, sys=0.0, user=0.0)
        for h in self.__history:\
            s = METRIC(input=s.input + h['child'].input + h['task'].input,
                       mem=s.mem + h['child'].mem + h['task'].mem,
                       output=s.output + h['child'].output + h['task'].output,
                       pages=s.pages + h['child'].pages + h['task'].pages,
                       sys=s.sys + h['child'].sys + h['task'].sys,
                       user=s.user + h['child'].user + h['task'].user)
        return s
    pass

class Version(object):
    '''Define what a version number is the context of DAWGIE

    Unfortunately, this is where Python gets a little weird. It would be nicer
    if it was possible to have Python enforce some typing rules because any
    version number is a set of non-negative integer values. However, all of the
    implementers are going to have to behave and make sure that the three
    abstract methods: bugfix(), design(), and implementation() always return
    non-negative integer values.

    A version number in the context of DAWGIE is a tuple of 3 digit that specify
    the temporal location of the design, implementation, and bug fix states.
    When represented as a string, it is D.I.BF. Incrementing any counter will
    reset all counters to the right of it to zero. For instance, incrementing
    the implementation will reset the bugfix to 0. Incrementing the design will
    reset the implementation and bugfix to 0.

    The design counter shuold be incremented when new features are added.
    For instance, if an algorithm adds a new state vector to its return list,
    then the design should be incremented. It should not be incremented if the
    code is restructured but the functional block diagram remains unchanged.

    The implementation counter should be incremented when the code is altered
    to produce different results in already expected returns. For instance,
    if an algorithm corrects a computation mistake and the Temperature state
    vector has a different value from the same input but the code prior and post
    change indicates an implementation change.

    The bugfix counter should be incremented anytime there is a change to the
    code but there should not be any change to the output. For instance, if a
    logging message was changed, then it is a bug fix.

    Typically, the first version number should always be 1.1.0. The version
    number 0.0.0 is special and should not be used because it causes the
    state vector to become a singleton. Other than the data ingestion from
    an archive, there should be no singleton versions.

    All implementers of dawgie.Version must have an attribute self._version_
    that is of the type dawgie.VERSION.

    In the event of a possible conflict, the implementation may override
    self._get_ver() and self._set_ver(). However, this should be done with
    extreme caution.
    '''
    def _get_ver(self)->VERSION: return self._version_
    def _set_ver(self, ver:VERSION): self._version_ = ver
    def asstring(self)->str: return '.'.join ([str(self.design()),
                                               str(self.implementation()),
                                               str(self.bugfix())])
    def bugfix(self)->int: return self._get_ver().bugfix
    def design(self)->int: return self._get_ver().design
    def implementation(self)->int: return self._get_ver().impl
    def newer (self, than:VERSION)->bool:
        return (than.design < self.design() or
                (than.design == self.design() and than.impl < self.implementation()) or
                (than.design == self.design() and than.impl == self.implementation() and than.bugfix < self.bugfix()))
    pass

class Algorithm(Version):
    '''Define what an algorithm means in the context of DAWGIE

    An algorithm is a computational process that generates the smallest logical
    set of state vectors. Knowing where and how to separate the entire
    computational process is based solely on the granule of reprocessing that
    one wants to do when a state vector changes. For instance, if an algorithm
    is defined to return ALL of the state vectors, then the entire process must
    be re-run when ANY of the state vectors change. The counter example would be
    if all algorithms return one and only one state vector. In that case, the
    absolute minimum of processing must be done when any of the state vector
    change.

    There are five abstract methods that require implementation:

    abort() -> returns a boolean indicating if the pipeline has requested that
               the current algorithm abort its operation immediately. When it
               returns True, the algorithm should clean up and do-do files, then
               `raise dawgie.AbortAEError()`.
    feedback() -> list of algorithms references [SV_REF, V_REF] that will be
                  generated in the future but whose current values should be
                  used. This capability adds cycles to an DAG which is fraught
                  with peril. The best way to avoid all of the peril is to have
                  dedicated (only used for feedback) state vectors. Cannot
                  required the dedication of state vectors forcing their use
                  to convention with a warning.
    name() -> the unique algorithm name
    previous() -> list of algorithms references [ALG_REF, SV_REF, V_REF] that
                  must run before this algorihtm with an empty list meaning it
                  operates directly on instrument data
    run(ds,ps) -> run the algorithm against the given dataset (ds) and suggested
                  multiprocessing pool size (ps)
    state_vectors() -> a list of state vectors:
       - when called prior to run() Values should be the base Value
       - when called post to run() Values should contain current Value
    '''
    def abort(self)->bool: return False
    def feedback(self)->[SV_REF, V_REF]: return []
    def name(self)->str: raise NotImplementedError()
    def previous(self)->[SV_REF, V_REF]: raise NotImplementedError()
    def run(self, ds, ps): raise NotImplementedError()
    def state_vectors(self)->'[StateVector]': raise NotImplementedError()
    def sv_as_dict(self)->'{str:StateVector}':
        return dict([(sv.name(), sv) for sv in self.state_vectors()])
    def where(self)->Distribution: return Distribution.auto
    pass

class Analysis(_Metric):
    '''The Analysis is the base for all bots that analyze data across targets

    Abstract functions that all bots need to implement:

    list() -> return a list of all analyzers
    '''
    def __init__(self, name, ps_hint, runid):
        _Metric.__init__(self)
        self.__name = name
        self.__nv = []
        self.__ps_hint = ps_hint
        self.__runid = runid
        self.__timing = {}
        return

    def _name(self)->str: return self.__name
    def _ps_hint(self)->int: return self.__ps_hint
    def _runid(self)->int: return self.__runid
    def _target(self)->str: return '__all__'

    def abort(self)->bool:
        '''Check with the pipeline to see if system should abort.

        The default implementation is to always return False. This will allow
        the bots to run in debug mode without modification. However, if in
        computationally expensive AE algorithms, the algorithm can ask the
        bot or itself if it should abort.
        '''
        return False

    def do(self, goto:str=None)->None:
        import dawgie.db

        log = logging.getLogger (__name__ + '.Analysis')
        for step in filter (lambda s:goto is None or s.name() == goto,
                            self.list()):
            if self.abort(): raise AbortAEError()
            else: setattr (step, 'abort', self.abort)

            self.__timing['gather_' + step.name()] = datetime.datetime.utcnow()
            aspect = dawgie.db.gather (step, self)
            self.__timing['collect_' + step.name()] = datetime.datetime.utcnow()
            aspect.collect (step.feedback())
            aspect.collect (step.traits())
            self.__timing['start_' + self._name()] = datetime.datetime.utcnow()
            log.info ('Stepping into ' + step.name())
            self.measure (step.run, args=(aspect,), ds=aspect.ds())
        return

    def list(self)->'[Analyzer]': raise NotImplementedError()

    def new_values (self, name:str=None)->[str]:
        if name: self.__nv.append (name)
        return self.__nv

    def timing (self): return self.__timing
    pass

class Analyzer(Version):
    '''Define what an analyzer means in the context of DAWGIE

    An analyzer is a computational process that extracts information based on
    traits common to all targets. Knowing where and how to separate the entire
    computational process is based solely on the granule of reprocessing that
    one wants to do when a traits change.

    There are five abstract methods that require implementation:

    abort() -> returns a boolean indicating if the pipeline has requested that
               the current algorithm abort its operation immediately. When it
               returns True, the algorithm should clean up and do-do files, then
               `raise dawgie.AbortAEError()`.
    name() -> the unique algorithm name
    feedback() -> list of algorithms references [SV_REF, V_REF] that will be
                  generated in the future but whose current values should be
                  used. This capability adds cycles to an DAG which is fraught
                  with peril. The best way to avoid all of the peril is to have
                  dedicated (only used for feedback) state vectors. Cannot
                  required the dedication of state vectors forcing their use
                  to convention with a warning.
    run(aspect)-> run the algorithm against the given dataset (ds) and suggested
                  multiprocessing pool size (ps)
    state_vectors() -> a list of state vectors:
       - when called prior to run() Values should be the base Value
       - when called post to run() Values should contain current Value
    traits() -> list of traits to provide within an Aspect
    '''
    def abort(self)->bool: return False
    def feedback(self)->[SV_REF, V_REF]: return []
    def name(self)->str: raise NotImplementedError()
    def run (self, aspects:'Aspect')->None: raise NotImplementedError()
    def state_vectors(self)->'[StateVector]': raise NotImplementedError()
    def sv_as_dict(self)->'{str:StateVector}':
        return dict([(sv.name(), sv) for sv in self.state_vectors()])
    def traits(self)->[ALG_REF, SV_REF, V_REF]: raise NotImplementedError()
    def where(self)->Distribution: return Distribution.auto
    pass

class Aspect(object):
    '''The Aspect is the data pertaining to all targets

    Implementations are done in dawgie.db.
    '''
    def __iter__(self): raise NotImplementedError()

    def _collect (self, refs:[(SV_REF,V_REF)])->None:
        raise NotImplementedError()

    def collect (self, refs:[(SV_REF,V_REF)])->None:
        self.ds().measure (self._collect, (refs,))
        return

    def ds(self)->'Dataset': raise NotImplementedError()
    pass

class Dataset(_Metric):
    '''Define what a dataset means in the context of DAWGIE

    A dataset s the entire collection of information known to the DAWGIE system
    related to a specific target name. However the dataset is always rooted to
    the original files from an instrument.

    Implementations are done in dawgie.db.
    '''
    def __init__ (self, alg, bot, tn):
        '''Generate a helper to move data between an algorithm and the database

        alg - an instance of dawgie.Algorithm
        bot - an instance of dawgie.Task
        tn  - the target name being worked upon
        '''
        _Metric.__init__ (self)
        self.__alg = alg
        self.__bot = bot
        self.__tn = tn
        pass

    def _alg(self)->Algorithm: return self.__alg
    def _algn(self)->str: return self.__alg.name()
    def _bot(self)->'Task': return self.__bot

    def _compare_insensitive (self, l, r) -> bool:
        '''Compare two target names ignoring case'''
        return l.lower() == r.lower()

    def _compare_sensitive (self, l, r) -> bool:
        '''Compare two target names using case as a discriminator'''
        return l == r

    def _load(self, algref=None, err=True, ver=None)->None:
        '''see load() of this class'''
        raise NotImplementedError()

    def _runid(self)->int: return self.__bot._runid()
    def _task(self)->str: return self.__bot._name()
    def _tn(self)->str: return self.__tn

    def _update(self)->None:
        '''see update() of this class'''
        raise NotImplementedError()

    def _update_msv (self, msv)->None: raise NotImplementedError()

    def load(self, algref=None, err=True, ver=None)->None:
        '''Load the most recent database values

        algref - specify which state vectors to load with None being the
                 currently defined algorithm allowing both the current
                 algorithm and all dependents to load their latest state
                 vectors
        err - raise a KeyError when True and if the algorithm state vector
              value does not exist
        ver - version of the value to obtain with None being most recent

        Read all the values from the database that match those in the
        state vectors generated during the algorithm execution defined
        in the constructor.
        '''
        self.measure (self._load, args=(algref, err, ver))
        return

    def update(self)->None:
        '''Update intermediate data in the database

        Writes all the values contained in all of state vectors that the
        algorithm given at construction generates.
        '''
        self.measure (self._update)
        return
    pass

class Feature(object):
    # pylint: disable=too-few-public-methods
    pass

class Regress(_Metric):
    '''The Regress is the base for all bots that analyze data across runids

    Abstract functions that all bots need to implement:

    list() -> return a list of all analyzers
    '''
    def __init__(self, name, ps_hint, target):
        _Metric.__init__(self)
        self.__name = name
        self.__nv = []
        self.__ps_hint = ps_hint
        self.__target = target
        self.__timing = {}
        return

    def _name(self)->str: return self.__name
    def _ps_hint(self)->int: return self.__ps_hint
    def _runid(self)->int: return 0
    def _target(self)->str: return self.__target

    def abort(self)->bool:
        '''Check with the pipeline to see if system should abort.

        The default implementation is to always return False. This will allow
        the bots to run in debug mode without modification. However, if in
        computationally expensive AE algorithms, the algorithm can ask the
        bot or itself if it should abort.
        '''
        return False

    def do(self, goto:str=None)->None:
        import dawgie.db

        log = logging.getLogger (__name__ + '.Regress')
        for step in filter (lambda s:goto is None or s.name() == goto,
                            self.list()):
            if self.abort(): raise AbortAEError()
            else: setattr (step, 'abort', self.abort)

            self.__timing['retreat_' + step.name()] = datetime.datetime.utcnow()
            timeline = dawgie.db.retreat (step, self)
            self.__timing['recede_' + step.name()] = datetime.datetime.utcnow()
            timeline.recede (step.feedback())
            timeline.recede (step.variables())
            self.__timing['start_' + self._name()] = datetime.datetime.utcnow()
            log.info ('Stepping into ' + step.name())
            self.measure (step.run,
                          args=(self._ps_hint(), timeline), ds=timeline.ds())
        return

    def list(self)->'[Regression]': raise NotImplementedError()

    def new_values (self, name:str=None)->[str]:
        if name: self.__nv.append (name)
        return self.__nv

    def timing (self): return self.__timing
    pass

class Regression(Version):
    '''Define what a regression means in the context of DAWGIE

    A regression is a computational process that extracts information based on
    variables across runids for a specific target. Knowing where and how to
    separate the entire computational process is based solely on the granule
    of reprocessing that one wants to do when a variable changes.

    There are five abstract methods that require implementation:

    abort() -> returns a boolean indicating if the pipeline has requested that
               the current algorithm abort its operation immediately. When it
               returns True, the algorithm should clean up and do-do files, then
               `raise dawgie.AbortAEError()`.
    feedback() -> list of algorithms references [SV_REF, V_REF] that will be
                  generated in the future but whose current values should be
                  used. This capability adds cycles to an DAG which is fraught
                  with peril. The best way to avoid all of the peril is to have
                  dedicated (only used for feedback) state vectors. Cannot
                  required the dedication of state vectors forcing their use
                  to convention with a warning.
    name() -> the unique algorithm name
    run(timeline)-> run the algorithm against the given dataset (ds) and suggested
                  multiprocessing pool size (ps)
    state_vectors() -> a list of state vectors:
       - when called prior to run() Values should be the base Value
       - when called post to run() Values should contain current Value
    variables() -> list of variables to provide within a Timeline
    '''
    def abort(self)->bool: return False
    def feedback(self)->[SV_REF, V_REF]: return []
    def name(self)->str: raise NotImplementedError()
    def run (self, ps:int, timeline:'Timeline')->None:
        raise NotImplementedError()
    def state_vectors(self)->'[StateVector]': raise NotImplementedError()
    def sv_as_dict(self)->'{str:StateVector}':
        return dict([(sv.name(), sv) for sv in self.state_vectors()])
    def variables(self)->[ALG_REF, SV_REF, V_REF]: raise NotImplementedError()
    def where(self)->Distribution: return Distribution.auto
    pass

class StateVector(Version, dict):
    '''Define what a state vector means in the context of DAWGIE

    A state vector is a collection of Values. It is important to notice that
    the state vector is being defined to be a dictionary and the dictionary
    functions mean the following:

    clear() -> no-op
    copy() -> a shallow copy of self
    fromkeys(K) -> new dict with keys from self and values equal to v
                   where v defaults to None when key is not present in self
    get(obj) -> same as dict
    has_keys(k) -> True if self has Value named k else False
    items() -> list of (Values.name(), Values) contained within self
    iteritems() -> same as dict
    iterkeys() -> same as dict
    keys() -> a list Value.name() contained within self
    pop() -> no-op
    popitem(i) -> no-op
    setdefault(k,d) -> no-op
    update (sv) -> if self maintains history, then self should update
                   its history and record itself otherwise it is a no-op
    values() -> list of Values contained within self
    viewitems() -> same as dict
    viewkeys() -> same as dict
    viewvalues() -> same as dict

    With respect to extending Version:

       Increment the design counter when new Values are added.
       Increment the implementation if its history behavior changes

    Each state vector contained within an algorithm must have a unique name
    and this name is immutable. The implementer defines this name through
    the implementation of the abstract method:

    name() -> the unique name of the state vector
    view() -> use the visitor to convert the content to a nice view
    '''
    # pylint: disable=unused-argument
    def clear(self): return
    def name(self)->str: raise NotImplementedError()
    def pop(self): return
    def popitem (self,i): return
    def setdefault (self,k,d=None): return
    def view(self, visitor:'Visitor')->None: raise NotImplementedError()
    pass

class Task(_Metric):
    '''The Task is the base class for all bots which are to complete a task

    Abstract functions that all bots need to implement:

    list() -> return a list of all algorithms
    '''
    def __init__(self, name, ps_hint, runid, target='__all__'):
        _Metric.__init__(self)
        self.__name = name
        self.__nv = []
        self.__ps_hint = ps_hint
        self.__runid = runid
        self.__target = target
        self.__timing = {}
        return

    def _make_ds (self, alg) -> Dataset:
        '''Make a Dataset with the minimal help from self.do()'''
        import dawgie.db
        return dawgie.db.connect (alg, self, self.__target)

    def _name(self)->str: return self.__name
    def _ps_hint(self)->int: return self.__ps_hint
    def _runid(self)->int: return self.__runid
    def _target(self)->str: return self.__target

    def abort(self)->bool:
        '''Check with the pipeline to see if system should abort.

        The default implementation is to always return False. This will allow
        the bots to run in debug mode without modification. However, if in
        computationally expensive AE algorithms, the algorithm can ask the
        bot or itself if it should abort.
        '''
        return False

    def do(self, goto:str=None)->None:
        log = logging.getLogger (__name__ + '.Task')
        log.info ('Starting %s for %s', self.__name, self._target())
        for step in filter (lambda s:goto is None or s.name() == goto,
                            self.list()):
            if self.abort(): raise AbortAEError()
            else: setattr (step, 'abort', self.abort)

            sname = "%s.%s.%s" % (self._target(), self._name(), step.name())
            log.info ('Loading into %s', sname)
            self.__timing['load_' + step.name()] = datetime.datetime.utcnow()
            ds = self._make_ds (step)
            for f in step.feedback(): ds.load (f)
            for p in step.previous(): ds.load (p)
            log.info ('Loaded into %s', sname)
            self.__timing['start_' + step.name()] = datetime.datetime.utcnow()
            log.info ('Stepping into %s', sname)
            self.measure (step.run, args=(ds, self._ps_hint()), ds=ds)
            log.info ('Returned from %s', sname)
            pass
        log.info ('Completed %s for %s', self.__name, self._target())
        return

    def list(self)->[Algorithm]: raise NotImplementedError()

    def new_values (self, name:str=None)->[str]:
        if name: self.__nv.append (name)
        return self.__nv

    def timing (self): return self.__timing
    pass

class Timeline(object):
    '''The Aspect is the data pertaining to all targets

    Implementations are done in dawgie.db.
    '''
    def __iter__(self): raise NotImplementedError()
    def _recede (self, data:Regression)->None: raise NotImplementedError()
    def ds(self)->'Dataset': raise NotImplementedError()

    def recede (self, data:Regression)->None:
        self.ds().measure (self._recede, (data,))
        return
    pass

class Value(Version):
    '''Define what a value means in the context of DAWGIE

    A value is a collection of measurements of a single source. For instance,
    it may be a time series, where the single source is a particular sensor
    and the collection is over time.

    There are two abstract methods that require implementation:

    features() -> return an iterable or be a generator
    view()  -> add self to a viewable visitor
    '''
    # pylint: disable=too-few-public-methods
    def __getstate__(self)->dict:
        state = self.__dict__.copy()
        state['_version_seal_'] = state['_version_']
        del state['_version_']
        return state

    def __setstate__ (self, state:dict)->None:
        self.__dict__.update (state)
        empty = self.__new__(self.__class__)
        empty.__init__()
        self._version_ = empty._version_
        return

    def features(self)->[Feature]: raise NotImplementedError()
    pass


class Visitor(object):
    def add_declaration (self, text:str, **kwds)->None:
        raise NotImplementedError()
    def add_image (self, alternate:str, label:str, img:bytes)->None:
        raise NotImplementedError()
    def add_primitive (self, value, label:str=None)->None:
        raise NotImplementedError()
    def add_table (self, clabels:[str], rows:int=0, title:str=None)->'TableVisitor':
        raise NotImplementedError()
    pass

class TableVisitor(object):
    # pylint: disable=too-few-public-methods
    def get_cell (self, r:int, c:int)->Visitor:
        raise NotImplementedError()
    pass

def _version():
    result = '0.0.0'
    v = os.path.basename (os.path.abspath
                          (os.path.join (os.path.dirname (__file__), '..')))

    if v.startswith ('dawgie-') and v.endswith ('.egg'): \
       result = v[7:v.find ('-', 7)]

    return result

__version__ = _version()

def resolve_username()->str:
    try: name = getpass.getuser()
    except KeyError:
        if 'USER' in os.environ: name = os.environ['USER']
        elif 'USERNAME' in os.environ: name = os.environ['USERNAME']
        else: raise KeyError ('Neither getpass.getuser(), os.environ[USER], ' +
                              'nor os.environ[USERNAME] would resolve to a ' +
                              'users name.')
    return name
