#! /usr/bin/env python3
'''Rules for making sure code is compliant with the architecture.

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

# pylint: disable=import-self,protected-access,too-many-arguments,too-many-branches,too-many-locals,unused-argument

import argparse
import datetime
import importlib
import inspect
import logging
import os
import pickle
import sys

def _get_rules():
    for r in filter (lambda k:k.startswith ('rule_'),
                     sorted (dir (dawgie.tools.compliant))): yield r
    return

def _rules():
    for r in _get_rules():
        rule = getattr (dawgie.tools.compliant, r)
        print (inspect.cleandoc (r + ":\n" + inspect.getdoc (rule)))
        print()
        print()
        pass
    return

def _scan():
    factories = dawgie.pl.scan.for_factories (dawgie.context.ae_base_path,
                                              dawgie.context.ae_base_package)
    all_factories = []
    for v in factories.values(): all_factories.extend (v)
    tasks = list ({f.__module__ for f in all_factories})
    tasks.sort()
    return tasks

def _t (*args, **kwds): return True

def _verify (tasks, silent, verbose):
    passed = True
    for t in tasks:
        result = []
        logging.info ('Verifying %s', t)

        if not silent and verbose: print (f'Verifying {t}')

        for r in _get_rules():
            # pylint: disable=bare-except
            status = False
            try: status = getattr (dawgie.tools.compliant, r) (t)
            except: logging.exception ('Could not process %s', r)
            result.append (status)
            logging.info ('%s:%s', r, str(result[-1]))

            if not silent and verbose: print ('   ' + r + ': ' +
                                              str (result[-1]))
            pass
        logging.info ('Verified %s:%s', t, str (all (result)))

        if not silent: print ('Verified ' + t + ': ' + str (all (result)))
        if not all(result): passed = False
        pass
    return passed

def _walk (task, ifbot=_t, ifalg=_t, ifsv=_t, ifv=_t,
           ifanl=_t, ifanz=_t, ifret=_t, ifrec=_t, ifref=_t,
           ifmom=_t):
    fargs = {dawgie.Factories.analysis:('test', 1, -1),
             dawgie.Factories.task:('test', 1, -1, 'TEST'),
             dawgie.Factories.events:(),
             dawgie.Factories.regress:('test', 1, 'TEST')}
    mod = importlib.import_module (task)
    names = dir (mod)
    for e in filter (lambda e:e.name in names, dawgie.Factories):
        f = getattr (mod, e.name)
        bot = f (*fargs[e])

        if e == dawgie.Factories.analysis:
            ifanl (bot)
            for a in bot.list():
                ifanz (a)
                for ref in a.feedback(): ifref (ref)
                for ref in a.traits(): ifref (ref)
                for sv in a.state_vectors():
                    ifsv (sv)
                    for i in sv.items(): ifv (i)
                    pass
                pass
        elif e == dawgie.Factories.task:
            ifbot (bot)
            for a in bot.list():
                ifalg (a)
                for ref in a.feedback(): ifref (ref)
                for ref in a.previous(): ifref (ref)
                for sv in a.state_vectors():
                    ifsv (sv)
                    for i in sv.items(): ifv (i)
                    pass
                pass
        elif e == dawgie.Factories.events:
            for m in bot: ifmom (m)
        elif e == dawgie.Factories.regress:
            ifret (bot)
            for r in bot.list():
                ifrec (r)
                for ref in a.feedback(): ifref (ref)
                for ref in r.variables(): ifref (ref)
                for sv in r.state_vectors():
                    ifsv (sv)
                    for i in sv.items(): ifv (i)
                    pass
                pass
        else: print (e)
        pass
    return

def main():
    ap = argparse.ArgumentParser(description='Encode rules that the architecture requires but I cannot enforce because the language does not allow for enforcement. Use -r or --rules to see the current rules that  are being enforced.')
    ap.add_argument ('--ae-dir', required=True,
                     help='the complete path to the AE directory')
    ap.add_argument ('--ae-pkg', required=True,
                     help='the package prefix for the AE')
    ap.add_argument ('-l', '--log-file', default=None, required=False,
                     help='a filename to put all of the log messages into [%(default)s]')
    ap.add_argument ('-L', '--log-level', default=logging.ERROR, required=False,
                     type=dawgie.util.log_level,
                     help='set the verbosity that you want where a smaller number means more verbose [logging.INFO]')
    ap.add_argument ('-r', '--rules', action='store_true', default=False,
                     help='display all of the rules and then exit')
    ap.add_argument ('-s', '--silent', action='store_true', default=False,
                     help='turn off the text indicating success or failure')
    ap.add_argument ('-t', '--task-list', default=[], nargs='*',
                     help='list specific tasks to verify compliance (like "dawgie.ae.deroo") or if none are given search for all available and verify their compliance')
    ap.add_argument ('-v', '--verbose', action='store_true', default=False,
                     help='display verbose information of verification')
    args = ap.parse_args()
    dawgie.context.ae_base_path = args.ae_dir
    dawgie.context.ae_base_package = args.ae_pkg
    sys.path.insert (0, '/'.join (args.ae_dir.split ('/')[:-len(args.ae_pkg.split ('.'))]))
    yes = True

    if args.log_file and args.log_file.startswith ('::') and args.log_file.endswith ('::'):
        host,port,gpghome = args.log_file.split ('::')[1:-1]
        print (args.log_file, host, port, gpghome)
        dawgie.security.initialize (gpghome)
        print ('dawgie.security.initialize')
        handler = dawgie.pl.logger.TwistedHandler (host=host, port=int(port))
        print ('dawgie.pl.logger.TwistedHandler')
        logging.basicConfig (handlers=[handler], level=args.log_level)
        print ('logging.basicConfig')
        logging.captureWarnings (True)
        print ('logging.captureWarnings')
    else: logging.basicConfig (filename=args.log_file, level=args.log_level)

    if args.rules: _rules()
    else:
        yes =_verify (_scan() if not args.task_list else args.task_list,
                      args.silent, args.verbose)

    print ('returning', yes)
    return yes

def rule_01 (task):
    '''Verify that there is at least one factory function.

    The architecture requires that AE packages either have ignore=True attribute
    or one of the abstract factory names defined by dawgie.Factories. Each of
    these abstract factories requires some number of parameters and some have
    default values. They should look like:

        analysis (prefix:str, ps_hint:int=0, runid:int=-1)
        events()
        regression (prefix:str, ps_hint:int=0, target:str='__none__')
        task (prefix:str, ps_hint:int=0, runid:int=-1, target:str='__none__')

    where
        prefix must be supplied
        ps_hint is a pool size hint for multiprocessing and should default to 0
        runid is the data to retrieve and should default to -1
        target is the name to be used for look up and should default to __none__
    '''
    fargs = {dawgie.Factories.analysis:(3, [inspect.Parameter.empty, 0, -1],
                                        [str,int,int]),
             dawgie.Factories.events:(0, [], []),
             dawgie.Factories.regress:(3,[inspect.Parameter.empty,0,'__none__'],
                                       [str,int,str]),
             dawgie.Factories.task:(4,[inspect.Parameter.empty,0,-1,'__none__'],
                                    [str,int,int,str])}
    findings = []
    mod = importlib.import_module (task)
    names = dir (mod)
    findings.append (any((e.name in names for e in dawgie.Factories)))

    if not findings[-1]: logging.error ('No factory method in package %s', task)

    for e in filter (lambda e:e.name in names, dawgie.Factories):
        f = getattr (mod, e.name)
        findings.append (inspect.isfunction (f) and
                         len (inspect.signature (f).parameters.keys()) ==
                         fargs[e][0])

        if findings[-1]:
            findings.append (True)
            for d,v in zip (fargs[e][1],
                            inspect.signature (f).parameters.values()):
                findings[-1] &= v.default == d
                pass

            if findings[-1]:
                findings.append (True)
                for a,v in zip (fargs[e][2],
                                inspect.signature (f).parameters.values()):
                    findings[-1] &= v.annotation == a
                    pass
                if not findings[-1]:
                    logging.error ('Args not typed of factory %s in package %s',
                                   e.name, task)
                    pass
            else: logging.error ('Missing defaults of factory %s in package %s',
                                 e.name, task)
        else: logging.error ('Number of arguments for factory %s in package %s',
                             e.name, task)
        pass
    return all (findings)

def rule_02 (task):
    '''Verify that all of the types are correct.

    The architecture requires that the bot returned from the factory verified in
    rule_01 inherits from dawgie.Task. The algorithms returned from the bot
    must inherit from dawgie.Algorithm. The state vectors returned by the
    algorithm must inherit from dawgie.StateVector. All keys in the state
    vectors must resolve to values that inherit from dawgie.Value.
    '''
    def _signal (state, t, name='??'):
        findings.append (state)

        if not state: logging.error ('failed to inherit correctly within package ' + task + ' because item ' + name + ' is does not inherit from dawgie.' + t)
        return

    findings = []
    _walk (task,
           ifbot=lambda b:_signal (isinstance (b, dawgie.Task), 'Task'),
           ifalg=lambda a:_signal (isinstance (a, dawgie.Algorithm),
                                   'Algorithm'),
           ifsv=lambda sv:_signal (isinstance (sv, dawgie.StateVector),
                                   'StateVector'),
           ifv=lambda i:_signal (isinstance (i[1], dawgie.Value),
                                 'Value', i[0]),
           ifanl=lambda a:_signal (isinstance (a, dawgie.Analysis),
                                   'Analysis'),
           ifanz=lambda a:_signal (isinstance (a, dawgie.Analyzer),
                                   'Analyzer'),
           ifret=lambda a:_signal (isinstance (a, dawgie.Regress),
                                   'Regress'),
           ifrec=lambda a:_signal (isinstance (a, dawgie.Regression),
                                   'Regression'),
           ifref=lambda ref:_signal (isinstance (ref, (dawgie.ALG_REF,
                                                       dawgie.SV_REF,
                                                       dawgie.V_REF)),
                                     'Aspect Reference'),
           ifmom=lambda mom:_signal (isinstance (mom, dawgie.EVENT),
                                     'Periodic Event'))
    return all (findings)

def rule_03 (task):
    '''Verify that all of the abstract methods are overriden correctly.

    The architecture requires that algorithm engine elements implement all of
    the methods that raise NotImplementedError. All of the methods are checked
    and failure occurs if any of them are not extended correctly.
    '''

    def _signal (i, func, name):
        try: findings.append (func (i))
        except NotImplementedError: findings.append (False)

        if not findings[-1]: logging.error ('Item %s does not override all of the elements it needs to or does not return the correct types.', name)
        return

    def _verify_analysis (a): return (all ((isinstance (az, dawgie.Analyzer)
                                            for az in a.list()))
                                      if a.list() else False)

    def _verify_analyzer (a):
        if a.traits(): tl = all((isinstance (p, (dawgie.SV_REF, dawgie.V_REF))
                                 for p in a.traits()))
        else: tl = True

        if a.state_vectors():
            svl = all((isinstance (sv, dawgie.StateVector)
                       for sv in a.state_vectors()))
            pass
        else: svl = True
        return all ([svl, tl, _verify_version (a),
                     isinstance (a.name(), str),
                     isinstance (a.traits(), list),
                     isinstance (a.state_vectors(), list)])

    def _verify_alg (a):
        if a.previous(): pl = all((isinstance (p, (dawgie.ALG_REF,
                                                   dawgie.SV_REF,
                                                   dawgie.V_REF))
                                   for p in a.previous()))
        else: pl = True

        if a.state_vectors():
            svl = all((isinstance (sv, dawgie.StateVector)
                       for sv in a.state_vectors()))
            pass
        else: svl = True
        return all ([pl, svl, _verify_version (a),
                     isinstance (a.name(), str),
                     isinstance (a.previous(), list),
                     isinstance (a.state_vectors(), list)])

    def _verify_regress (r): return (all ((isinstance (reg, dawgie.Regression)
                                           for reg in r.list()))
                                     if r.list() else False)

    def _verify_regression (r):
        if r.variables(): tl = all((isinstance (v, (dawgie.SV_REF,dawgie.V_REF))
                                    for v in r.variables()))
        else: tl = True

        if r.state_vectors():
            svl = all((isinstance (sv, dawgie.StateVector)
                       for sv in r.state_vectors()))
            pass
        else: svl = True
        return all ([svl, tl, _verify_version (r),
                     isinstance (r.name(), str),
                     isinstance (r.variables(), list),
                     isinstance (r.state_vectors(), list)])

    def _verify_state_vector (sv): return _verify_version (sv)

    def _verify_task (t): return (all ((isinstance (a, dawgie.Algorithm)
                                        for a in t.list()))
                                  if t.list() else False)

    def _verify_value (v): return all ([_verify_version (v)])

    def _verify_version (item):
        result = isinstance (item._get_ver(), dawgie.VERSION)
        item._set_ver (dawgie.VERSION (-1,-2,-3))
        return result and item.design() == -1 and item.implementation() == -2 \
                      and item.bugfix() == -3

    findings = []
    _walk (task,
           ifbot=lambda b:_signal (b, _verify_task, 'main task'),
           ifalg=lambda a:_signal (a, _verify_alg, a.name()),
           ifsv=lambda sv:_signal (sv, _verify_state_vector, sv.name()),
           ifv=lambda i:_signal (i[1], _verify_value, i[0]),
           ifanl=lambda a:_signal (a, _verify_analysis, 'main aspect'),
           ifanz=lambda a:_signal (a, _verify_analyzer, a.name()),
           ifret=lambda a:_signal (a, _verify_regress, 'main regression'),
           ifrec=lambda a:_signal (a, _verify_regression, a.name()))
    return all (findings)

def rule_04 (task):
    '''Verify that all of the name() returns do not contain a ".".

    The architecture uses uses the name() to generate complete full names for
    all items that require persistence. It uses the character "." to join the
    elements together to form the full name. Hence, the character "." becomes
    special in the context of the architecture and cannot be used in the return
    of name().
    '''
    def _signal (state, name):
        findings.append (state)

        if not state: logging.error ('the package ' + task + ' contains a name with the special character ".": ' + name)
        return

    findings = []
    _walk (task,
           ifbot=lambda b:_signal (True, ''),
           ifalg=lambda a:_signal (a.name().find ('.') < 0, a.name()),
           ifsv=lambda sv:_signal (sv.name().find ('.') < 0, sv.name()),
           ifv=lambda i:_signal (i[0].find ('.') < 0, i[0]),
           ifanl=lambda a:_signal (True, ''),
           ifanz=lambda a:_signal (a.name().find ('.') < 0, a.name()),
           ifret=lambda a:_signal (True, ''),
           ifrec=lambda a:_signal (a.name().find ('.') < 0, a.name()))
    return all (findings)

def rule_05 (task):
    '''Verify that the state vector has predefined keys.

    The pipeline is designed to track changes in algorithm, state vector, and
    value but when an algorithm holds a state vector with now a prior value
    containers, the pipeline cannot track the versions correctly.
    '''
    def _signal (sv):
        findings.append (0 < len (sv))

        if not findings[-1]: logging.error ('the package %s contains state vector %s with no predefined keys', task, sv.name())
        return

    findings = []
    _walk (task, ifsv=_signal)
    return all (findings)

def rule_06 (task):
    '''Verify that tasks previous ALG_REF[factory] is consistent with
       ALG_REF[previous_alg].
    '''
    findings = [True]
    mod = importlib.import_module (task)

    if 'task' in dir (mod):
        f = getattr (mod, 'task')
        bot = f('test', -1, 1, 'TEST')
        for step in bot.list():
            for prev in step.previous():
                findings.append (prev.impl.__module__.startswith
                                 (prev.factory.__module__))

                if not findings[-1]: logging.error ('the previous implementation %s does not start with the factory package %s', prev.impl.__module__, prev.factory.__module__)
                pass
            pass
        pass
    return all (findings)

def rule_07 (task):
    '''Verify all known values are pickle-able

    The pipeline only records dawgie.Value and it does so using pickle. Need
    to verify that all of the used (known) extensions of dawgie.Value are
    pickle-able. There is some unique version handling that requires a little
    more to the dawgie.Value extensions to make them pickle-able. Namely, they
    must have default values for all arguments so that the current version
    can be picked up during the unpicking.
    '''
    def test (val):
        # pylint: disable=bare-except,unused-variable
        vn,v = val
        try:
            s = pickle.dumps (v)
            vp = pickle.loads (s)
            findings.append (True)
        except:
            findings.append (False)
            logging.error ('dawgie.Value subclass named "%s" cannot be pickled.', vn)
            pass
        return

    findings = [True]
    _walk (task, ifv=test)
    return all (findings)

def rule_08 (task):
    '''Verify elements of *_REF are the correct types

    The documentation states what each of the elements should be.
       factory - a function with 4 or 3 params depending on Analysis/Regressor/Task
       impl - an Analyzer, Algorithm, or Regression
       item - a StateVector
       feat - a string
    '''
    def _check_ref_types (ref):
        findings.append (inspect.isfunction (ref.factory) or
                         inspect.ismethod (ref.factory))
        if not findings[-1]: logging.error ('ref.factory is not a function')

        findings.append (isinstance (ref.impl, (dawgie.Algorithm,
                                                dawgie.Analyzer,
                                                dawgie.Regression)))
        if not findings[-1]: logging.error ('ref.impl not an instance of Algorithm, Analyzer, or Ressions')

        if isinstance (ref, (dawgie.SV_REF, dawgie.V_REF)):
            findings.append (isinstance (ref.item, dawgie.StateVector))
            if not findings[-1]: logging.error ('ref.item not an instance of StateVector')
            pass

        if isinstance (ref, dawgie.V_REF):
            findings.append (isinstance (ref.feat, str))
            if not findings[-1]: logging.error ('ref.feat is not a string')
            pass
        return

    findings = []
    _walk (task, ifref=_check_ref_types)
    return all(findings)

def rule_09 (task):
    '''Verify it has state vectors

    The scheduler is *smart* in the sense that it will ignore items (Analyzer,
    Algorithms, and Regression) that have an empty list of state vectors. The
    concept is that if it does not output a state vector, it must not have any
    affect on the world it knows. Or, side-effects are not supported.
    '''
    def non_zero (tsk): findings.append (0 < len (tsk.state_vectors()))

    findings = []
    _walk (task, ifalg=non_zero, ifanz=non_zero, ifrec=non_zero)
    return all(findings)

def rule_10 (task):
    '''Verify moments are built correctly

    When using the factory periodic, it requires that dawgie.MOMENT be
    constructed in a specific way where some values are mutually exclusive.
    '''
    findings = []
    mod = importlib.import_module (task)

    if 'events' in dir (mod):
        for e in mod.events():
            not_defined = [e.moment.boot is None,
                           e.moment.day is None,
                           e.moment.dom is None,
                           e.moment.dow is None]
            findings.append (sum (not_defined) == len (not_defined) - 1)
            findings.append (e.moment.day is None or
                             isinstance (e.moment.day, datetime.date))
            findings.append (e.moment.dom is None or
                             isinstance (e.moment.dom, int))
            findings.append (e.moment.dow is None or
                             isinstance (e.moment.dow, int))

            if e.moment.boot is None:\
               findings.append (isinstance (e.moment.time, datetime.time))
            pass
    else: findings.append (True)
    return all(findings)

def verify (repo:str, silent:bool, verbose:bool, spawn):
    '''verify a repo meets DAWGIEs needs

    Spawn a subprocess and run the rules over the repo. A subprocess is used to
    remove any potential confusion from the current environment. However, how
    a subprocess is spawned is left to the caller. Typically, the function spawn
    (see arguments) would simply look like this:

        def spawn (cmd:[str]):
            return subprocess.call (cmd) == 0

    When using twisted, however, it is not nearly so simple (see twisted docs
    for twisted.internet.reactor.spawnProcess). Twisted and subprocess do not
    play well together.

    repo : the working repository
    silent : when True, do not print the the screen
    verbose : when True, print more details about what is happening
    spawn : a function pointer that takes one argument that is a list of strings

    Function returns what spawn returns.
    '''
    # format() is more readable so pylint: disable=consider-using-f-string
    cmd = ['python3', '-m', 'dawgie.tools.compliant',
           '--ae-dir={0}/{1}'.format (repo, dawgie.context.ae_base_package.replace ('.', '/')),
           '--ae-pkg={0}'.format (dawgie.context.ae_base_package),
           '--log-file=::{0}::{1}::{2}::'.format (dawgie.context.db_host,
                                                  dawgie.context.log_port,
                                                  dawgie.context.gpg_home),
           '--log-level={}'.format (dawgie.context.log_level)]
    # pylint: enable=consider-using-f-string
    silent = False
    verbose = True
    if silent: cmd.append ('--silent')
    if verbose: cmd.append ('--verbose')

    logging.getLogger(__name__).info ('spawn off compliant check: %s', str(cmd))
    return spawn (cmd)

if __name__ == '__main__':
    # main blocks always look the same; pylint: disable=duplicate-code
    root = os.path.dirname (__file__)
    for gi in range(2): root = os.path.join (root, '..')
    root = os.path.abspath (root)
    sys.path.insert (0,root)

    import dawgie
    import dawgie.context
    import dawgie.pl.logger
    import dawgie.pl.scan
    import dawgie.security
    import dawgie.tools.compliant
    import dawgie.util

    gpassed = main()

    if gpassed: sys.exit (0)
    else: sys.exit (-1)
else:
    import dawgie
    import dawgie.context
    import dawgie.pl.logger
    import dawgie.pl.scan
    import dawgie.security
    import dawgie.tools.compliant
    import dawgie.util
    pass
