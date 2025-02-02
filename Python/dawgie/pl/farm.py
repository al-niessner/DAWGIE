'''
COPYRIGHT:
Copyright (c) 2015-2025, California Institute of Technology ("Caltech").
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

import datetime
import dawgie.context
import dawgie.db
import dawgie.pl.message
import dawgie.pl.schedule
import dawgie.security
import dawgie.util
import importlib
import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import math
import struct
import twisted.internet.task

ARCHIVE = False


class Hand(twisted.internet.protocol.Protocol):
    # need to retain state for string representation so
    # pylint: disable=too-many-instance-attributes
    @staticmethod
    def _res(msg):
        done = (
            msg.jobid
            + '['
            + (msg.incarnation if msg.incarnation else '__all__')
            + ']'
        )
        while 0 < _busy.count(done):
            _busy.remove(done)
            if done in _time:
                del _time[done]
            pass
        log.debug('msg: %s', msg)
        log.debug('suc: %s', Hand._translate(msg.success))
        try:
            job = dawgie.pl.schedule.find(msg.jobid)
            inc = msg.incarnation if msg.incarnation else '__all__'
            state = Hand._translate(msg.success)
            dawgie.pl.schedule.complete(job, msg.runid, inc, msg.timing, state)

            if state == dawgie.pl.schedule.State.success:
                dawgie.pl.farm.ARCHIVE |= any(msg.values)
                dawgie.pl.schedule.update(msg.values, job, msg.runid)
            else:
                dawgie.pl.schedule.purge(job, inc)

        except IndexError:
            log.error('Could not find job with ID: %s', msg.jobid)
        return

    @staticmethod
    def _translate(state):
        if state is None:
            return dawgie.pl.schedule.State.invalid
        if state:
            return dawgie.pl.schedule.State.success
        return dawgie.pl.schedule.State.failure

    def __init__(self, address):
        twisted.internet.protocol.Protocol.__init__(self)
        self._abort = dawgie.pl.message.make(
            typ=dawgie.pl.message.Type.response, suc=False
        )
        self.__address = address
        self.__blen = len(struct.pack('>I', 0))
        self.__buf = b''
        self.__incarnation = None
        self.__len = None
        log.debug('work application submission from %s', str(address))
        if not dawgie.security.use_tls():
            # really is used so pylint: disable=unused-private-member
            self.__handshake = dawgie.security.TwistedWrapper(self, address)
        self.__proceed = dawgie.pl.message.make(
            typ=dawgie.pl.message.Type.response, suc=True
        )
        self.__wait = dawgie.pl.message.make()
        return

    def __str__(self):
        addr = str(self.__address)
        incr = str(self.__incarnation)
        return f'dawgie.pl.farm.Hand from {addr} incarnation {incr}'

    def _process(self, msg):
        if msg.type == dawgie.pl.message.Type.register:
            self._reg(msg)
        elif msg.type == dawgie.pl.message.Type.response:
            Hand._res(msg)
        elif msg.type == dawgie.pl.message.Type.status:
            if (
                msg.revision != dawgie.context.git_rev
                or not dawgie.context.fsm.is_pipeline_active()
            ):
                dawgie.pl.message.send(self._abort, self)
                # long msg more readable so pylint: disable=logging-not-lazy
                log.warning(
                    'Worker and pipeline revisions are not the same. '
                    + 'Sever version %s and worker version %s.',
                    str(msg.revision),
                    str(dawgie.context.git_rev),
                )
            else:
                dawgie.pl.message.send(self.__proceed, self)
            self.transport.loseConnection()
        else:
            log.error('Unexpected message type: %s', str(msg.type))
            self.transport.loseConnection()
            pass
        return

    def _reg(self, msg):
        if msg.revision != dawgie.context.git_rev:
            dawgie.pl.message.send(self._abort, self)
            log.warning('Worker and pipeline revisions are not the same.')
            self.transport.loseConnection()
        else:
            _workers.append(self)
            self.__incarnation = msg.incarnation
            log.debug(
                'Registered a worker for its %d incarnation.', msg.incarnation
            )
            pass
        return

    # pylint: disable=signature-differs
    def connectionLost(self, reason):
        while 0 < _workers.count(self):
            _workers.remove(self)
        return

    def dataReceived(self, data):
        # protocols are independent even if similar today
        # pylint: disable=duplicate-code
        self.__buf += data
        length = self.__blen if self.__len is None else self.__len
        while length <= len(self.__buf):
            if self.__len is None:
                self.__len = struct.unpack('>I', self.__buf[:length])[0]
                self.__buf = self.__buf[length:]
            else:
                msg = dawgie.pl.message.loads(self.__buf[:length])
                self.__buf = self.__buf[length:]
                self.__len = None
                self._process(msg)
                pass

            length = self.__blen if self.__len is None else self.__len
            pass
        return

    def do(self, task):
        _busy.append(
            task.jobid + '[' + (task.target if task.target else '__all__') + ']'
        )
        _time[_busy[-1]] = datetime.datetime.now()
        return dawgie.pl.message.send(task, self)

    def notify(self, keep=None):
        if keep is None:
            keep = dawgie.context.fsm.is_pipeline_active()
        if not keep:
            dawgie.pl.message.send(self._abort, self)
            self.transport.loseConnection()
        else:
            dawgie.pl.message.send(self.__wait, self)

        return keep

    def sendall(self, b: bytes):
        return self.transport.write(b)

    pass


class Foreman(twisted.internet.protocol.Factory):
    def buildProtocol(self, addr):
        return Hand(addr)

    pass


_agency = [None]
_busy = []
_cloud = []
_cluster = []
_time = {}
_workers = []

_reject = []
_repeat = []


def _move(job, try_again) -> None:
    if try_again:
        _repeat.append(job)
    else:
        _reject.append(job)
    return


def _put(job, runid: int, target: str, where: dawgie.Distribution):
    if where == dawgie.Distribution.auto:
        key = '.'.join([target if target else '__all__', job.tag])
        where = (
            insights[key].summary
            if key in insights
            else dawgie.Distribution.cluster
        )
        pass

    now = datetime.datetime.now(datetime.UTC)
    fac = job.get('factory')
    msg = dawgie.pl.message.make(
        ctxt=dawgie.context.dumps(),
        fac=(fac.__module__, fac.__name__),
        jid=job.tag,
        rid=runid,
        target=target,
        tim={'scheduled': now},
        typ=dawgie.pl.message.Type.task,
    )
    (
        _cloud
        if _agency[0] and where == dawgie.Distribution.cloud
        else _cluster
    ).append(msg)
    return


def clear():
    log.info('clearing the entire estate')
    _busy.clear()
    _cloud.clear()
    _cluster.clear()
    _jobs.clear()
    _time.clear()
    _workers.clear()
    return


def crew():
    # string is complicated so pylint: disable=consider-using-f-string
    return {
        'busy': [
            b
            + " duration: %s"
            % delta_time_to_string(datetime.datetime.now() - _time[b])
            for b in _busy
        ],
        'idle': str(len(_workers)),
    }


def delta_time_to_string(diff):
    mins = diff.seconds / 60
    # string is complicated so pylint: disable=consider-using-f-string
    return "%02d:%02d:%02d" % (
        diff.days * 24 + math.floor(mins / 60),
        mins % 60,
        diff.seconds % 60,
    )


insights = {}
_jobs = []


def dispatch():
    # pylint: disable=too-many-branches
    if not something_to_do():
        return

    _jobs.extend(dawgie.pl.schedule.next_job_batch())

    if (
        ARCHIVE
        and not dawgie.pl.schedule.promote.more()
        and not sum([len(_jobs), len(_busy), len(_cluster), len(_cloud)])
    ):
        dawgie.context.fsm.archiving_trigger()
        pass

    # allow db impl to throw an exception via rerunid() which means exception
    # class name is unknowable so pylint: disable=bare-except
    try:
        for j in _jobs.copy():
            runid = rerunid(j)
            j.set('status', dawgie.pl.schedule.State.running)
            fm = j.get('factory').__module__
            fn = j.get('factory').__name__
            factory = getattr(importlib.import_module(fm), fn)
            where = dawgie.Distribution.auto
            for alg in factory(dawgie.util.task_name(factory)).list():
                if alg.name() == j.tag.split('.')[-1]:
                    where = alg.where()
                pass

            if fn == dawgie.Factories.analysis.name:
                _put(job=j, runid=runid, target=None, where=where)
            elif fn == dawgie.Factories.task.name:
                for t in sorted(list(j.get('do'))):
                    _put(job=j, runid=runid, target=t, where=where)
                    pass
            elif fn == dawgie.Factories.regress.name:
                for t in sorted(list(j.get('do'))):
                    _put(job=j, runid=0, target=t, where=where)
                    pass
                pass
            else:
                log.error('Unknown factory name: %s', str(fn))

            j.get('do').clear()
            _jobs.remove(j)
    except:  # noqa: E722
        log.exception("Error processing from next_job_batch()")
    # pylint: enable=bare-except

    if _agency[0]:
        _cloud.extend(_repeat)
        _repeat.clear()
        for cloud_job in _cloud:
            _agency[0].do(
                cloud_job._replace(type=dawgie.pl.message.Type.cloud), _move
            )
            pass
        _cloud.clear()
        pass

    _cluster.extend(_reject)
    _reject.clear()
    for dummy in range(min(len(_cluster), len(_workers))):
        _workers.pop(0).do(_cluster.pop(0))
    notify_all()
    return


def notify_all():
    keep = dawgie.context.fsm.is_pipeline_active()
    cclist = list(filter(lambda w: w.notify(keep), _workers))
    _workers.clear()
    _workers.extend(cclist)
    return


def plow():
    if dawgie.context.cloud_provider == dawgie.context.CloudProvider.aws:
        _agency[0] = importlib.import_module('dawgie.pl.worker.aws')
        _agency[0].initialize()
        pass

    if dawgie.security.use_tls():
        controller = dawgie.security.authority().options(
            *dawgie.security.certificates()
        )
        twisted.internet.reactor.listenSSL(
            int(dawgie.context.farm_port),
            Foreman(),
            controller,
            dawgie.context.worker_backlog,
        )
    else:
        # protocols are independent even if similar today
        # pylint: disable=duplicate-code
        log.critical('PGP support is deprecated and will be removed')
        twisted.internet.reactor.listenTCP(
            int(dawgie.context.farm_port),
            Foreman(),
            dawgie.context.worker_backlog,
        )
    twisted.internet.task.LoopingCall(dispatch).start(5).addErrback(
        dawgie.pl.LogFailure(
            'dispatching scheduled jobs to workers on the farm', __name__
        ).log
    )
    return


def rerunid(job):
    runid = job.get('runid', None)

    if runid is None:
        runid = dawgie.db.next()
        log.critical(
            'New run ID (%d) for algorithm %s trigger by the event: %s',
            runid,
            job.tag,
            job.get('event', 'Not Specified'),
        )
        pass
    return runid


def something_to_do():
    # pylint: disable=too-many-branches,too-many-statements
    if dawgie.context.fsm.waiting_on_crew() and not _agency:
        log.debug("farm.dispatch: Waiting for crew to finish...")
        return False
    if not dawgie.context.fsm.is_pipeline_active():
        log.debug("Pipeline is not active. Returning from farm.dispatch().")
        return False
    return True
