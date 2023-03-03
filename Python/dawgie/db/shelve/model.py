'''dawgie element model(s)

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

NTR:
'''

import logging;  log = logging.getLogger(__name__)
import pickle

from dawgie import Dataset, Timeline
from dawgie.db.util.aspect import Container

from . import comms
from .comms import Connector
from .enums import Table

import dawgie.db.util.aspect

class Interface(Connector, Container, Dataset, Timeline):
    def __init__(self, *args):
        dawgie.Dataset.__init__(self, *args)
        dawgie.db.util.aspect.Container.__init__(self)
        self.__span = {}
        null_metric = dawgie.METRIC(-1,-1,-1,-1,-1,-1)
        self._log = log.getChild(self.__class__.__name__)
        self.msv = dawgie.util.MetricStateVector(null_metric, null_metric)
        return

    # pylint: disable=protected-access,too-many-arguments
    def __to_key (self, runid:int, tn:str, task:str, alg:dawgie.Algorithm,
                  sv:dawgie.StateVector, vn:str):
        if any(arg is None for arg in [runid, tn, task, alg, sv, vn]):
            raise ValueError('cannot be None')
        trgtid = self._update_cmd (tn, None, Table.target, None, None)
        tid = self._update_cmd (task, None, Table.task, None, None)
        if isinstance (alg, dawgie.Algorithm): raise ValueError('Should be dawgie.Algorithm')
        if isinstance (sv, dawgie.StateVector): raise ValueError('Should be dawgie.StateVector')
        if isinstance (vn, str): raise ValueError('Should be dawgie.Value')
        aid = self._update_cmd (alg.name(), tid, Table.alg, None, alg._get_ver())
        sid = self._update_cmd (sv.name(), aid, Table.state, None, sv._get_ver())
        vid = self._update_cmd (vn, sid, Table.value, None, sv[vn]._get_ver())
        return (runid, trgtid, tid, aid, sid, vid)
    # pylint: enable=protected-access,too-many-arguments

    def _collect (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->None:
        self.__span = {}
        pk = {}
        span = {}
        tnl = [keyset.name for keyset in self._keys (Table.target)]
        for k in filter (lambda k:k[0] != '-', self._keys (Table.prime)):
            runid = int(k.split ('.')[0])
            sk = '.'.join (k.split ('.')[1:])
            pk['.'.join (k.split ('.')[1:])] = max (runid, pk.get (sk, -1))
            pass
        pk = ['.'.join ([str (i[1])] + i[0].split ('.')) for i in pk.items()]
        for ref in refs:
            clone = pickle.dumps (ref.item)
            fsvn = '.'.join ([dawgie.util.task_name (ref.factory),
                              ref.impl.name(),
                              ref.item.name()])

            if fsvn not in span: span[fsvn] = {}

            span[fsvn].update ({tn:pickle.loads (clone) for tn in tnl})
            for vn in ref.item.keys():
                if isinstance (ref, dawgie.V_REF) and vn != ref.feat: continue

                for k in filter (lambda k,a=fsvn,b=vn:k.endswith ('.'.join (['',a,b])), pk):
                    tn = k.split ('.')[1]
                    span[fsvn][tn][vn] = self._get (k, Table.prime)
                    pass
                pass
            pass
        for tn in tnl:
            for fsvn,fsv in span.items():
                if tn in fsv:
                    for vn in fsv[tn]:
                        if tn not in self.__span: self.__span[tn] = {}
                        if fsvn not in self.__span[tn]:\
                           self.__span[tn][fsvn] = {}

                        self.__span[tn][fsvn][vn] = span[fsvn][tn][vn]
                        pass
                    pass
                pass
            pass
        return

    def _ckeys (self, l1k, l2k):
        if l2k: keys = self.__span[l1k][l2k].keys()
        elif l1k: keys = self.__span[l1k].keys()
        else: keys = self.__span.keys()
        return keys

    def _fill_item (self, l1k, l2k, l3k): return self.__span[l1k][l2k][l3k]

    def _load (self, algref=None, err=True, ver=None, lok=None):
        # pylint: disable=too-many-branches,too-many-nested-blocks,too-many-locals,too-many-statements
        if self._alg().abort(): raise dawgie.AbortAEError()

        parent= False
        if lok is None:
            name = '.'.join ([self._tn(), self._task(), self._algn()])
            parent= True
            self._log.debug("load: Acquiring for %s", name)
            lok = comms.acquire ('load: ' + name)
            pass

        try:
            if algref:
                ft = dawgie.Factories.resolve (algref)
                tn = self._tn()

                # need to get some private information
                # pylint: disable=protected-access
                if ft == dawgie.Factories.analysis:
                    args = (dawgie.util.task_name (algref.factory),
                            self._bot()._ps_hint(),
                            self._bot()._runid())
                    tn = '__all__'
                elif ft == dawgie.Factories.regress:
                    args = (dawgie.util.task_name (algref.factory),
                            self._bot()._ps_hint(),
                            tn)
                elif ft == dawgie.Factories.task:
                    args = (dawgie.util.task_name (algref.factory),
                            self._bot()._ps_hint(),
                            self._bot()._runid(),
                            tn)
                else:
                    raise KeyError(f'Unknown factory type {algref.factory.__name__}')
                # pylint: enable=protected-access

                child = Interface(algref.impl, algref.factory(*args), tn)
                child._load (err=err, ver=ver, lok=lok)  # pylint: disable=protected-access
                pass
            else:
                msv = dawgie.util.MetricStateVector(dawgie.METRIC(-1,-1,-1,-1,-1,-1),
                                                    dawgie.METRIC(-1,-1,-1,-1,-1,-1))
                for sv in self._alg().state_vectors() + [msv]:
                    # need to get some private information
                    # pylint: disable=protected-access
                    base = self.__to_key (self._bot()._runid(), self._tn(),
                                          self._task(), self._alg(), sv,
                                          None) + '.'
                    # pylint: enable=protected-access

                    if not list(filter (lambda n,base=base:n.startswith (base),
                                        self._keys (Table.prime))):
                        base = self.__to_key (None, self._tn(), self._task(),
                                              self._alg(), sv, None) + '.'
                        prev = -1
                        for k in self._keys (Table.prime):
                            runid = int(k.split ('.')[0])
                            if '.'.join (k.split ('.')[1:]).startswith (base):
                                prev = max (prev, runid)
                                pass
                            pass
                        pass
                    else: prev = self._bot()._runid()  # pylint: disable=protected-access

                    base = self.__to_key (prev, self._tn(), self._task(),
                                          self._alg(), sv, None) + '.'
                    for k in filter (lambda n,b=base:n.startswith (b),
                                     self._keys (Table.prime)):
                        sv[k.split ('.')[-1]] = self._get (k, Table.prime)
                        pass
                    pass
                self.msv = msv
                pass
        finally:
            if parent:
                self._log.debug("load: Releaseing for %s", name)
                comms.release (lok)
                pass
            pass
        return

    def ds (self): return self

    def _recede (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->None:
        span = {}
        pk = sorted (set (filter (lambda k:k.split('.')[1] == self._tn(),
                                  self._keys (Table.prime))))
        rids = sorted ({int(k.split ('.')[0]) for k in pk})
        for ref in refs:
            clone = pickle.dumps (ref.item)
            fsvn = '.'.join ([dawgie.util.task_name (ref.factory),
                              ref.impl.name(),
                              ref.item.name()])

            if fsvn not in span: span[fsvn] = {}

            span[fsvn].update ({rid:pickle.loads (clone) for rid in rids})
            for vn in filter (lambda n,ref=ref:(not isinstance
                                                (ref,dawgie.V_REF) or
                                                n == ref.feat),
                              ref.item.keys()):
                for k in filter (lambda k,a=fsvn,b=vn:k.endswith ('.'.join (['',a,b])), pk):
                    rid = int(k.split ('.')[0])
                    span[fsvn][rid][vn] = self._get (k, Table.prime)
                    pass
                pass
            pass
        self.__span = {}
        for rid in rids:
            for fsvn,fsv in span.items():
                if rid in fsv:
                    for vn in fsv[rid]:
                        if rid not in self.__span: self.__span[rid] = {}
                        if fsvn not in self.__span[rid]:\
                           self.__span[rid][fsvn] = {}
                        self.__span[rid][fsvn][vn] = fsv[rid][vn]
                        pass
                    pass
                pass
            pass
        return

    def _retarget (self,subname:str,upstream:[dawgie.ALG_REF])->dawgie.Dataset:
        return Interface(self._alg(), self._bot(), subname)

    def _update (self):
        if self._alg().abort(): raise dawgie.AbortAEError()

        name = '.'.join ([self._tn(), self._task(), self._algn()])
        self._log.debug("update: Acquiring for %s", name)
        lok = comms.acquire ('update: ' + name)
        valid = True
        try:
            for sv in self._alg().state_vectors():
                for k in sv.keys():
                    if not dawgie.db.util.verify (sv[k]):
                        self._log.critical('offending item is %s',
                                           '.'.join ([self._task(), self._algn(),
                                                      sv.name(), k]))
                        valid = False
                        continue
                    pass
                pass

            if not valid:
                # exceptions always look the same; pylint: disable=duplicate-code
                raise dawgie.NotValidImplementationError\
                      ('StateVector contains data that does not extend ' +
                       'dawgie.Value correctly. See log for details.')

            for sv in self._alg().state_vectors():
                for k in sv.keys():
                    runid, tn, task = self._runid(), self._tn(), self._task()
                    alg, vn = self._alg(), k
                    vname = self.__to_key (runid, tn, task, alg, sv, vn)
                    isnew = self._set_prime (vname, sv[k])
                    self._bot().new_values ((vname, isnew))
                    pass
                pass
        finally:
            self._log.debug("update: Releaseing for %s", name)
            comms.release (lok)
            pass
        return

    def _update_msv (self, msv):
        if self._alg().abort(): raise dawgie.AbortAEError()

        name = '.'.join ([self._tn(), self._task(), self._algn()])
        self._log.debug("update: Acquiring for %s", name)
        lok = comms.acquire ('update: ' + name)
        valid = True
        try:
            for k in msv.keys():
                if not dawgie.db.util.verify (msv[k]):
                    self._log.critical('offending item is %s',
                                       '.'.join ([self._task(), self._algn(),
                                                  msv.name(), k]))
                    valid = False
                    continue
                pass

            if not valid:
                # exceptions always look the same; pylint: disable=duplicate-code
                raise dawgie.NotValidImplementationError\
                      ('MetricStateVector contains data that does not extend ' +
                       'dawgie.Value correctly. See log for details.')

            for k in msv.keys():
                runid, tn, task = self._runid(), self._tn(), self._task()
                alg = self._alg()
                vname = self.__to_key (runid, tn, task, alg, msv, k)
                isnew = self._set_prime (vname, msv[k])
                self._bot().new_values ((vname, isnew))
                pass
        finally:
            self._log.debug("update: Releaseing for %s", name)
            comms.release (lok)
            pass
        return
    pass
