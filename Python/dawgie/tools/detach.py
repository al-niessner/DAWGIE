'''
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

NTR:
'''

import argparse
import dawgie
import dawgie.context
import dawgie.db
import dawgie.db.util
import dawgie.util
import importlib
import logging
import os
import shelve
import shutil

def _algorithm (task, algorithm):
    dataset = dawgie.db.connect (algorithm, task, args.target)
    for f in algorithm.feedback(): dataset.load (f)
    for p in algorithm.previous(): dataset.load (p)
    return algorithm.feedback() + algorithm.previous()

def _analyzer (analysis, analyzer):
    aspect = dawgie.db.gather (analyzer, analysis)
    aspect.collect (analyzer.feedback())
    aspect.collect (analyzer.traits())
    return analyzer.feedback() + analyzer.traits()

def _copy (references):
    for vr in dawgie.util.as_vref (references):
        fn,nn = dawgie.db.util.encode (vr.impl.sv_as_dict()[vr.item][vr.feat])
        nfn = os.path.join (args.output_dir, nn)

        if not os.path.isfile (nfn): shutil.move (fn, nfn)
        if args.private_database:
            vn = '.'.join ([dawgie.util.task_name (vr.factory),
                            vr.impl.name(), vr.item, vr.feat])
            for k in args.private_database:
                if k.endswith (vn):
                    fn = args.private_database[k]
                    nfn = os.path.join (args.output_dir, fn)
                    ofn = os.path.join (dawgie.context.data_dbs, fn)

                    if os.path.isfile (ofn) and not os.path.isfile (nfn):\
                       shutil.copy (ofn, nfn)
                    pass
                pass
            pass
        pass
    return

def _dir (dn:str):
    if not os.path.isdir (dn):
        raise ValueError(f'The specified value {dn} is not a directory')
    return dn

def _regression (regress, regression):
    timeline = dawgie.db.retreat (regression, regress)
    timeline.recede (regression.feedback())
    timeline.recede (regression.variables())
    return regression.feedback() + regression.variables()

def _shelve (fn): return shelve.open (fn) if fn else fn

ap = argparse.ArgumentParser(description='Replicate a small part of the DAWGIE data stored by DAWGIE into --output-dir. The output can then be used by private pipelines detached from the original DAWGIE system.')
ap.add_argument ('-DB', '--private-database', default=None, required=False,
                 type=_shelve, help='when the database contains old data')
ap.add_argument ('-O', '--output-dir', required=True, type=_dir,
                 help='directory to write the value files to')
ap.add_argument ('-r', '--runid', default=1 << 30, required=False, type=int,
                 help='runID to use for loading [%(default)s]')
ap.add_argument ('-R', '--runnables', nargs='+', required=True, type=str,
                 help='list of analysis.analyzer, regress.regression, task.algorithm')
ap.add_argument ('-t', '--target', required=True, type=str,
                 help='specific known target')
load = {dawgie.Factories.analysis:_analyzer,
        dawgie.Factories.regress:_regression,
        dawgie.Factories.task:_algorithm}
dawgie.context.add_arguments (ap)
args = ap.parse_args()
dawgie.context.override (args)
dawgie.db.open()
ARGS = {dawgie.Factories.analysis:(0, args.runid),
        dawgie.Factories.regress:(0, args.target),
        dawgie.Factories.task:(0, args.runid, args.target)}
for runnable in args.runnables:
    try:
        instance = None
        mod_name,runnable_name = runnable.split('.')
        mod = importlib.import_module ('.'.join
                                       ([dawgie.context.ae_base_package,
                                         mod_name]))
        for factory_method in dawgie.Factories:
            if factory_method.name in dir(mod):
                instance = getattr (mod, factory_method.name)\
                           (mod_name, *ARGS[factory_method])
                for r in instance.list():
                    if r.name() == runnable_name:\
                       _copy (load[factory_method](instance, r))
                    pass
                pass
            pass

        if instance is None:\
           logging.warning ('Could not locate runnable %s', runnable)
    except ImportError as ie:\
           logging.exception ("Could not import runnable's module %s", runnable)
    pass

if args.private_database: args.private_database.close()
