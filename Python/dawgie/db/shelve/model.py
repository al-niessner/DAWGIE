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

import dawgie.util
import logging;  log = logging.getLogger(__name__)

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

    def __refs2indices (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->{(int,int,int,int):(str,str)}:
        '''convert references into tuple of index stored in the primary table

        return a dictionary of (tskid,algid,svid,vid):("tskn.algn.svn",vn)
        '''
        reftable = {}
        for vref in dawgie.util.as_vref (refs):
            task = dawgie.util.task_name (vref.factory)
            algn = vref.impl.name()
            svn = vref.item.name()
            vn = vref.feat
            # pylint: disable=protected-access
            tid = self._update_cmd (task, None, Table.task, None, None)
            aid = self._update_cmd (algn, tid, Table.alg, None,
                                    vref.impl._get_ver())
            sid = self._update_cmd (svn, aid, Table.state, None,
                                    vref.item._get_ver())
            vid = self._update_cmd (vn, sid, Table.value, None,
                                    vref.item[vn]._get_ver())
            # pylint: enable=protected-access
            reftable[(tid,aid,sid,vid)] = ('.'.join([task,algn,svn]),vn)
            pass
        return reftable

    # pylint: disable=protected-access,too-many-arguments
    def __to_key (self, runid:int, tn:str, task:str, alg:dawgie.Algorithm,
                  sv:dawgie.StateVector, vn:str):
        if any(arg is None for arg in [runid, tn, task, alg, sv, vn]):
            raise ValueError('cannot be None')
        trgtid = self._update_cmd (tn, None, Table.target, None, None)[1]
        tid = self._update_cmd (task, None, Table.task, None, None)[1]
        aid = self._update_cmd (alg.name(),tid,Table.alg,None,alg._get_ver())[1]
        sid = self._update_cmd (sv.name(),aid,Table.state,None,sv._get_ver())[1]
        vid = self._update_cmd (vn, sid, Table.value, None, sv[vn]._get_ver())[1]
        return (runid, trgtid, tid, aid, sid, vid)
    # pylint: enable=protected-access,too-many-arguments

    def _collect (self, refs:[(dawgie.SV_REF, dawgie.V_REF)])->None:
        self.__span = {}
        refis = self.__refs2indices (refs)
        tnis = {index:name for name,index in self._table (Table.target).items()}
        for pk in self._prime_keys():
            if pk[2:] in refis:
                tn = tnis[pk[1]]
                fsvn,vn = refis[pk[2:]]
                if tn not in self.__span: self.__span[tn] = {}
                if fsvn not in self.__span[tn]: self.__span[tn][fsvn] = {}
                if vn not in self.__span[tn][fsvn]:\
                   self.__span[tn][fsvn][vn] = pk
                if self.__span[tn][fsvn][vn][0] < pk[0]:\
                   self.__span[tn][fsvn][vn] = pk
            pass
        for fsvn in self.__span.values():
            for vn,val in fsvn.items(): fsvn[vn] = self._get_prime (val)
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
                pks = self._prime_keys()
                for sv in self._alg().state_vectors() + [msv]:
                    for vn in sv:
                        # need to get some private information
                        # pylint: disable=protected-access
                        pk = self.__to_key (self._bot()._runid(), self._tn(),
                                            self._task(), self._alg(), sv, vn)
                        # pylint: enable=protected-access

                        if pk not in pks:
                            spks = list(filter (lambda k,K=pk:k[1:] == K[1:],
                                                pks))
                            spks.sort (key=lambda t:t[0])
                            pk = spks[-1]
                            pass

                        sv[vn] = self._get_prime (pk)
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
        self.__span = {}
        refis = self.__refs2indices (refs)
        tni = self._table (Table.target)[self._tn()]
        for pk in filter (lambda t,k=tni:t[1] == k, self._prime_keys()):
            if pk[2:] in refis:
                fsvn,vn = refis[pk[2:]]
                if pk[0] not in self.__span: self.__span[pk[0]] = {}
                if fsvn not in self.__span[pk[0]]: self.__span[fsvn] = {}
                self.__span[pk[0]][fsvn][vn] = self._get_prime (pk)
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
