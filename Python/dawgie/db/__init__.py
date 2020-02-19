'''The package is a factory interface to the database implementations

The database interface has N goals:

  1. Divorce the Algorithm Engines and PipeLine from how the data is stored.
  2. Divorce the Algorithm Engines and PipeLine from where the data is stored.
  3. Provide fast gathering of the data for State Vectors or Values.

--
COPYRIGHT:
Copyright (c) 2015-2020, California Institute of Technology ("Caltech").
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

# pylint: disable=protected-access,redefined-builtin,too-many-arguments

import collections
import dawgie.context
import dawgie.util
import importlib
import logging; log = logging.getLogger(__name__)

METRIC_DATA = collections.namedtuple('METRIC_DATA', ['alg_name','alg_ver','sv',
                                                     'run_id','target','task'])

def _db_in_use():
    '''Internal function to select which database backend that is in use'''
    m = importlib.import_module ('dawgie.db.' + dawgie.context.db_impl)
    return m

def _prime_keys():
    return _db_in_use()._prime_keys()

def _prime_values():
    return _db_in_use()._prime_values()

def archive (done): return _db_in_use().archive (done)

def close():
    '''Close the database'''
    return _db_in_use().close()

def connect (alg, bot, tn):
    '''Connect an dawgie.Dataset to the database backend

    Separates the user from the database implementation.

    alg - the instance of dawgie.Algorithm that will be using the Dataset
    bot - the instance of dawgie.Task that will be calling alg
    tn  - the target name
    '''
    return _db_in_use().connect (alg, bot, tn)

def copy (dst, method, gateway):
    '''Copy database to destination.'''
    return _db_in_use().copy(dst, method, gateway)

def gather (anz, ans):
    '''Gather an dawgie.Aspect to the database backend

    anz : instance of dawgie.Analyzer that will be using the Aspect
    ans : instance of dawgie.Analysis that creates the anz
    '''
    return _db_in_use().gather (anz, ans)

def metrics()->[METRIC_DATA]:
    return _db_in_use().metrics()

def next():
    '''Return the next run ID'''
    return _db_in_use().next()

def open():
    '''Open the database'''
    return _db_in_use().open()

def remove(runid, tn, taskn, algn, svn, vn):
    '''Remove the specified key from the primary table'''
    return _db_in_use().remove (runid, tn, taskn, algn, svn, vn)

def reopen():
    '''open an already open database

    Used by modules outside of the pipeline but still wish to access the
    data contained within the database. When a reopen is closed, the pipeline
    will keep the database open for its own use.
    '''
    return _db_in_use().reopen()  # may only be needed in db/shelf.py

def retreat (reg, ret):
    '''Get a dawgie.Timeline from the database backend

    reg : instance of dawgie.Regression that will be using the Timeline
    ret : instance of dawgie.Regress that creates the ret
    '''
    return _db_in_use().retreat (reg, ret)

def targets (fulllist:bool=False):
    return [tn for tn in filter (lambda s:fulllist or not
                                 (s.startswith ('__') and s.endswith ('__')),
                                 _db_in_use().targets())]

def trace (task_alg_names):
    return _db_in_use().trace (task_alg_names)

def update (tsk, alg, sv, vn, v):
    '''Update the database with version information

    updates all elements if current version is not in the database (slow)

    tsk
    alg - instance of dawgie.Algorithm
    sv  - instance of dawgie.StateVector
    vn  - value name
    v   - instance of dawgie.Value
    '''
    return _db_in_use().update (tsk, alg, sv, vn, v)

def versions():
    '''Collate all of the known versions

    Returns alg, sv, and v dictionaries that are name:[versions as string].
    '''
    return _db_in_use().versions()

def view (visitor, runid, tn, tskn, algn, svn):
    '''Given a specific state vector, create a view for it

    visitor : instance of dawgie.Visitor
    runid   : the run id
    tn      : target name
    tskn    : task name
    algn    : algorithm nme
    svn     : state vector name
    '''
    import matplotlib
    import matplotlib.pyplot

    path = '.'.join ([str(runid), tn, tskn, algn, svn])
    visitor.add_declaration ('View of ' + path, title=None)
    visitor.add_declaration ('Viewing State Vector:', tag='h1')
    visitor.add_declaration ('Run ID:    ' + str(runid), tag='h3')
    visitor.add_declaration ('Target:    ' + str(tn), tag='h3')
    visitor.add_declaration ('Task:      ' + str(tskn), tag='h3')
    visitor.add_declaration ('Algorithm: ' + str(algn), tag='h3')
    visitor.add_declaration ('State Vec: ' + str(svn), tag='h3')
    try:
        mod = importlib.import_module ('.'.join([dawgie.context.ae_base_package,
                                                 tskn]).replace ('..', '.'))
        bot = mod.regress (tskn, 1, tn) if runid == 0 else \
              (mod.analysis (tskn, 1, runid) if tn == '__all__'
               else mod.task (tskn, 1, runid, tn))
    except ImportError:
        msg = 'Could not create the bot for task "' + tskn + '".'
        log.error (msg)
        visitor.add_declaration (msg)
        return

    alg = [a for a in filter (lambda x:x.name() == algn, bot.list())]

    if len (alg) == 1: alg = alg[0]
    else:
        msg = 'Could not find the algorithm "' + algn + \
              '" for task "' + tskn + '".'
        log.error (msg)
        visitor.add_declaration (msg)
        return

    sv = [sv for sv in filter (lambda x:x.name() == svn, alg.state_vectors())]

    if len (sv) == 1: sv = sv[0]
    elif svn == '__metric__':
        sv = dawgie.util.MetricStateVector(dawgie.METRIC(0,0,0,0,0,0),
                                           dawgie.METRIC(0,0,0,0,0,0))
    else:
        msg = 'Could not find the state vector "' + svn + \
              '" within algorithm "' + algn + '" for task "' + tskn + '".'
        log.error (msg)
        visitor.add_declaration (msg)
        return

    _db_in_use().reset (runid, tn, tskn, alg)
    ds = connect (alg, bot, tn)
    ds.load()

    if svn == '__metric__' and ds.msv: sv = ds.msv

    try: sv.view (visitor)
    except NotImplementedError:
        msg = 'view() is not implemented for the state vector "' + svn + \
              '" within algorithm "' + algn + '" for task "' + tskn + '".'
        log.error (msg)
        visitor.add_declaration (msg)
        pass
    matplotlib.pyplot.close ('all')
    return

def view_locks():
    return _db_in_use().view_locks()
