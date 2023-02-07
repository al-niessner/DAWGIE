'''Common utilities for the pipeline

--
COPYRIGHT:
Copyright (c) 2015-2023, California Institute of Technology ("Caltech").
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

import dawgie
import dawgie.context
import logging

class MetricStateVector(dawgie.StateVector):
    def __init__ (self, db, task):
        dawgie.StateVector.__init__(self)
        self._version_ = dawgie.VERSION(1,1,1)
        self['db_input'] = MetricValue(db.input)
        self['db_memory'] = MetricValue(db.mem)
        self['db_output'] = MetricValue(db.output)
        self['db_pages'] = MetricValue(db.pages)
        self['db_system'] = MetricValue(db.sys)
        self['db_user'] = MetricValue(db.user)
        self['task_input'] = MetricValue(task.input)
        self['task_memory'] = MetricValue(task.mem)
        self['task_output'] = MetricValue(task.output)
        self['task_pages'] = MetricValue(task.pages)
        self['task_system'] = MetricValue(task.sys)
        self['task_user'] = MetricValue(task.user)
        return
    def name(self): return '__metric__'
    def view (self, visitor:dawgie.Visitor)->None:
        table = visitor.add_table (['', 'DB', 'Task'],
                                   rows=6, title='Process Metrics')
        for r,k in enumerate (sorted (filter (lambda k:k.startswith ('db_'),
                                              self))):
            k = k.split ('_')[1]
            table.get_cell (r,0).add_primitive (k)
            table.get_cell (r,1).add_primitive (self['db_' + k].value())
            table.get_cell (r,2).add_primitive (self['task_' + k].value())
            pass
        return
    pass

class MetricValue(dawgie.Value):
    def __init__ (self, content=None):
        dawgie.Value.__init__ (self)
        self.__content = content
        self._version_ = dawgie.VERSION(1,1,0)
        return
    def features(self)->[dawgie.Feature]: return []
    def value(self): return self.__content
    pass

def algref2svref (ref:dawgie.ALG_REF)->[dawgie.SV_REF]:
    return [dawgie.SV_REF(factory=ref.factory, impl=ref.impl, item=sv)
            for sv in ref.impl.state_vectors()]

def as_vref (references:[dawgie.ALG_REF, dawgie.SV_REF, dawgie.V_REF]):
    for reference in references:
        if isinstance (reference, dawgie.V_REF): yield reference
        if isinstance (reference, dawgie.SV_REF):
            for vref in svref2vref (reference): yield vref
            pass
        if isinstance (reference, dawgie.ALG_REF):
            for svref in algref2svref (reference):
                for vref in svref2vref (svref): yield vref
                pass
            pass
        pass
    return

def log_level (l):
    """Allow log level to be symbolic or a plain integer
    """
    # pylint: disable=bare-except,eval-used
    try: ll = int(l)
    except: ll = eval (l)
    return ll

def set_ports (fe_port:int)->None:
    fep = int(fe_port)
    dawgie.context.cloud_port = fep + dawgie.context.PortOffset.cloud.value
    dawgie.context.db_port = fep + dawgie.context.PortOffset.shelve.value
    dawgie.context.farm_port = fep + dawgie.context.PortOffset.farm.value
    dawgie.context.fe_port = fep + dawgie.context.PortOffset.frontend.value
    dawgie.context.log_port = fep + dawgie.context.PortOffset.log.value
    return

def svref2vref (ref:dawgie.SV_REF)->[dawgie.V_REF]:
    return [dawgie.V_REF(factory=ref.factory, impl=ref.impl, item=ref.item,
                         feat=key) for key in ref.item]

def task_name (factory):
    '''Compute the pipeline specified prefix for any dawgie.Task

    Given the factory function for a list of dawgie.Task, compute the prefix
    to allow algorithms to share names sensibly. The rest of the name is just
    the index of the task in the list.
    '''
    cnt = len(dawgie.context.ae_base_package.split('.'))
    return '.'.join (factory.__module__.split ('.')[cnt:])

def verify_name (o, err=False):
    '''Check the name of an object meets the naming convention

    The architecture generate a full name by ".".join (elements). Hence, the
    name cannot contain the special character ".". This function checks the
    dawgie.Algorithm.name() and dawgie.StateVector.name(). In the case
    of dawgie.StateVector, it also checks all of the keys(). Details of
    failures will be sent to logging.critical().

    o : the object to check
    err : if True, then raise a ValueError otherwise when check fails

    return True when o.name().find (".") < 0 and same for
                dawgie.StateVector.keys()
    '''
    log = logging.getLogger (__file__)
    result = o.name().find (".") < 0

    if not result: \
       log.critical ('The name "%s" contains the special character "."', o.name)
    if isinstance (o, dawgie.StateVector):
        for name,state in [(k,k.find ('.') < 0) for k in o.keys()]:
            result &= state
            if not state: \
               log.critical ('The name "%s" contains the special character "."',
                             name)
            pass
        pass
    if err and not result: raise ValueError('The name(s) contains the special character "."')
    return result

def vref_as_name (vref:dawgie.V_REF)->str:
    return '.'.join ([task_name (vref.factory), vref.impl.name(),
                      vref.item.name(), vref.feat])
