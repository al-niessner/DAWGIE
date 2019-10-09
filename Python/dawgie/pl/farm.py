'''
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

NTR:
'''

# pylint: disable=import-self

import datetime
import dawgie.context
import dawgie.db
import dawgie.pl.farm
import dawgie.pl.message
import dawgie.pl.schedule
import dawgie.pl.start
import dawgie.security
import dawgie.util
import importlib
import logging; log = logging.getLogger(__name__)
import math
import struct
import twisted.internet.task

archive = False

class Hand(twisted.internet.protocol.Protocol):
    def __init__ (self, address):
        twisted.internet.protocol.Protocol.__init__(self)
        self._abort = dawgie.pl.message.make(typ=dawgie.pl.message.Type.response, suc=False)
        self.__blen = len (struct.pack ('>I', 0))
        self.__buf = b''
        self.__len = None
        log.info ('work application submission from %s', str(address))
        self.__handshake = dawgie.security.TwistedWrapper(self, address)
        self.__proceed = dawgie.pl.message.make(typ=dawgie.pl.message.Type.response, suc=True)
        self.__wait = dawgie.pl.message.make()
        return

    def _process (self, msg):
        if msg.type == dawgie.pl.message.Type.register: self._reg(msg)
        elif msg.type == dawgie.pl.message.Type.response: self._res(msg)
        elif msg.type == dawgie.pl.message.Type.status:
            if msg.revision != dawgie.context.git_rev or \
                   not dawgie.pl.start.sdp.is_pipeline_active():
                dawgie.pl.message.send (self._abort, self)
                log.warning ('Worker and pipeline revisions are not the same.')
            else: dawgie.pl.message.send (self.__proceed, self)
            self.transport.loseConnection()
        else:
            log.error ('Unexpected message type: %s', str(msg.type))
            self.transport.loseConnection()
            pass
        return

    def _reg (self, msg):
        if msg.revision != dawgie.context.git_rev:
            dawgie.pl.message.send (self._abort, self)
            log.warning ('Worker and pipeline revisions are not the same.')
            self.transport.loseConnection()
        else:
            _workers.append (self)
            log.info ('Registered a worker for its %d incarnation.',
                      msg.incarnation)
            pass
        return

    def _res (self, msg):
        # pylint: disable=no-self-use
        done = (msg.jobid + '[' +
                (msg.incarnation if msg.incarnation else '__all__') + ']')
        while 0 < _busy.count (done):
            _busy.remove (done)
            if done in _time: del _time[done]
            pass
        try:
            job = dawgie.pl.schedule.find (msg.jobid)
            dawgie.pl.schedule.complete (job,
                                         msg.runid,
                                         msg.incarnation if msg.incarnation else '__all__',
                                         msg.timing,
                                         (dawgie.pl.schedule.State.success
                                          if msg.success else dawgie.pl.schedule.State.failure))

            if msg.success:
                dawgie.pl.farm.archive |= any(msg.values)
                dawgie.pl.schedule.update (msg.values, job, msg.runid)
                pass
        except IndexError: log.error('Could not find job with ID: ' + msg.jobid)
        return

    # pylint: disable=signature-differs
    def connectionLost (self, reason):
        while 0 < _workers.count (self): _workers.remove (self)
        return

    def dataReceived (self, data):
        self.__buf += data
        length = self.__blen if self.__len is None else self.__len
        while length <= len (self.__buf):
            if self.__len is None:
                self.__len = struct.unpack ('>I', self.__buf[:length])[0]
                self.__buf = self.__buf[length:]
            else:
                msg = dawgie.pl.message.loads (self.__buf[:length])
                self.__buf = self.__buf[length:]
                self.__len = None
                self._process (msg)
                pass

            length = self.__blen if self.__len is None else self.__len
            pass
        return

    def do (self, task):
        _busy.append (task.jobid + '[' +
                      (task.target if task.target else '__all__') + ']')
        _time[_busy[-1]] = datetime.datetime.now()
        return dawgie.pl.message.send (task, self)

    def notify (self, keep=dawgie.pl.start.sdp.is_pipeline_active()):
        if not keep:
            dawgie.pl.message.send (self._abort, self)
            self.transport.loseConnection()
        else: dawgie.pl.message.send (self.__wait, self)

        return keep

    def sendall (self, b:bytes): return self.transport.write (b)
    pass

class Foreman(twisted.internet.protocol.Factory):
    def buildProtocol (self, addr): return Hand(addr)
    pass

_agency = None
_busy = []
_cloud = []
_cluster = []
_time = {}
_workers = []

_reject = []
_repeat = []
def _move (job, try_again)->None:
    if try_again: _repeat.append (job)
    else: _reject.append (job)
    return

def _put (job, runid:int, target:str, where:dawgie.Distribution):
    if where == dawgie.Distribution.auto:
        key = '.'.join ([target if target else '__all__', job.tag])
        where = insights[key].summary if key in insights else \
                dawgie.Distribution.cluster
        pass

    now = datetime.datetime.utcnow()
    fac = job.get ('factory')
    msg = dawgie.pl.message.make (ctxt=dawgie.context.dumps(),
                                  fac=(fac.__module__, fac.__name__),
                                  jid=job.tag,
                                  rid=runid,
                                  target=target,
                                  tim={'scheduled':now},
                                  typ=dawgie.pl.message.Type.task)
    (_cloud if _agency and where == dawgie.Distribution.cloud
     else _cluster).append (msg)
    return

def clear():
    _busy.clear()
    _cloud.clear()
    _cluster.clear()
    _time.clear()
    _workers.clear()
    return

def crew(): return {'busy':[b+" duration: %s" % delta_time_to_string(datetime.datetime.now() - _time[b]) for b in _busy], 'idle':str (len (_workers))}

def delta_time_to_string(diff):
    mins = diff.seconds/60
    return "%02d:%02d:%02d" % (diff.days * 24 + math.floor (mins/60),
                               mins % 60,
                               diff.seconds % 60)

insights = {}
def dispatch():
    # pylint: disable=too-many-branches,too-many-statements
    if dawgie.pl.start.sdp.waiting_on_crew() and not _agency:
        log.info("farm.dispatch: Waiting for crew to finish...")
        return
    if not dawgie.pl.start.sdp.is_pipeline_active():
        log.info("Pipeline is not active. Returning from farm.dispatch().")
        return

    jobs = dawgie.pl.schedule.next_job_batch()

    if archive and not sum ([len(jobs),len(_busy),len(_cluster),len(_cloud)]):
        dawgie.pl.start.sdp.archiving_trigger()
        pass

    for j in jobs:
        runid = j.get ('runid', None)

        if not runid:
            runid = dawgie.db.next()
            log.critical (('New run ID ({0:d}) for algorithm {1:s} ' +
                           'trigger by the event: ').format (runid, j.tag) +
                          j.get ('event', 'Not Specified'))
            pass

        j.set ('status', dawgie.pl.schedule.State.running)
        fm = j.get ('factory').__module__
        fn = j.get ('factory').__name__
        factory = getattr (importlib.import_module (fm), fn)
        where = dawgie.Distribution.auto
        for alg in factory (dawgie.util.task_name (factory)).list():
            if alg.name() == j.tag.split('.')[-1]: where = alg.where()
            pass

        if fn == dawgie.Factories.analysis.name:
            _put (job=j, runid=runid, target=None, where=where)
        elif fn == dawgie.Factories.task.name:
            for t in sorted(list(j.get ('do'))):
                _put (job=j, runid=runid, target=t, where=where)
                pass
        elif fn == dawgie.Factories.regress.name:
            for t in sorted(list(j.get ('do'))):
                _put (job=j, runid=0, target=t, where=where)
                pass
            pass
        else: log.error ('Unknown factory name: ' + str(fn))

        j.get ('do').clear()
        pass

    if _agency:
        _cloud.extend (_repeat)
        _repeat.clear()
        for cloud_job in _cloud:
            _agency.do (cloud_job._replace (type=dawgie.pl.message.Type.cloud),
                        _move)
            pass
        _cloud.clear()
        pass

    _cluster.extend (_reject)
    _reject.clear()
    for dummy in range (min (len (_cluster), len (_workers))): \
        _workers.pop (0).do (_cluster.pop (0))
    notifyAll()
    return

def notifyAll():
    # pylint: disable=protected-access
    keep = dawgie.pl.start.sdp.is_pipeline_active()
    dawgie.pl.farm._workers = [w for w in filter (lambda w:w.notify(keep),
                                                  _workers)]
    return

def plow():
    # necessary to do import here because items in dawgie.pl.aws depend on
    # classes defined in this module. Therefore, have to turn off some pylint.
    # pylint: disable=redefined-outer-name
    import dawgie.pl.aws

    if dawgie.context.cloud_provider == dawgie.context.CloudProvider.aws:
        # pylint: disable=protected-access
        dawgie.pl.farm._agency = dawgie.pl.aws
        _agency.initialize()
        pass

    twisted.internet.reactor.listenTCP(int(dawgie.context.farm_port),
                                       Foreman(), dawgie.context.worker_backlog)
    twisted.internet.task.LoopingCall(dispatch).start(5).addErrback (dawgie.pl.LogDeferredException(None, 'dispatching scheduled jobs to workers on the farm').log)
    return
