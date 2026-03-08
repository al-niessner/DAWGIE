'''Define a deferred rendering of a state vector

COPYRIGHT:
Copyright (c) 2015-2026, California Institute of Technology ("Caltech").
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

# 3.0.0 remove - when dawgie.fe.submit is removed the can cleanup line below
# pylint: disable=duplicate-code

from dawgie.fe.basis import DeferContainer, Status, build_return_object

import dawgie.context
import dawgie.tools.submit
import logging
import os
import twisted.internet.reactor
import twisted.web.server

LOG = logging.getLogger(__name__)


class Defer(DeferContainer):
    def __call__(self, changeset: [str], submission: [str]):
        if changeset[0].lower().strip():
            if not self.__busy:
                self.__busy = True
                process = Process(
                    changeset[0], self.clear, self.request, submission[0]
                )
                process.step_0()
                return twisted.web.server.NOT_DONE_YET
            return build_return_object(
                None, Status.FAILURE, 'Submission already in progress'
            )
        return build_return_object(
            None, Status.FAILURE, 'Cannot submit a blank changeset'
        )

    def __init__(self):
        DeferContainer.__init__(self)
        self.__busy = False
        return

    def clear(self):
        self.__busy = False


class Process:
    def __init__(self, changeset, clear, request, submission):
        object.__init__(self)
        LOG.debug('Process.__changeset %s', str(changeset))
        LOG.debug('Process.__clear %s', str(clear))
        LOG.debug('Process.__request %s', str(request))
        LOG.debug('Process.__submission %s', str(submission))
        self.__changeset = changeset
        self.__clear = clear
        self.__failed = False
        self.__msg = 'unspecified'
        self.__request = request
        self.__repo = dawgie.context.ae_base_path
        self.__submission = submission
        while not os.path.isdir(os.path.join(self.__repo, '.git')):
            self.__repo = os.path.dirname(self.__repo)
        return

    def failure(self, _fail):
        if self.__request is not None:
            if dawgie.context.fsm.state == 'gitting':
                dawgie.context.fsm.running_trigger()
            else:
                LOG.debug(
                    'Process.failure() state is not gitting: %s',
                    str(dawgie.context.fsm.state),
                )

            LOG.error(
                'Failed to complete user submit request: %s',
                self.__msg,
            )
            self.__request.write(
                build_return_object(None, Status.FAILURE, self.__msg)
            )
            try:
                self.__request.finish()
            except:  # pylint: disable=bare-except # noqa: E722
                LOG.exception('Failed to respond to caller.')
            self.__clear()
            self.__failed = True
            self.__request = None
            dawgie.tools.submit.mail_out(self.__msg)
        else:
            LOG.debug('Process.failure() self.__request is None')
        return None

    def step_0(self):
        '''setup the Defer steps to be run asynchronously'''
        dawgie.tools.submit.mail_list = dawgie.context.email_alerts_to
        d = twisted.internet.defer.Deferred()
        d.addCallback(self.step_1)
        d.addCallbacks(self.step_2, self.failure)
        d.addCallbacks(self.step_3, self.failure)
        d.addErrback(self.failure)
        twisted.internet.reactor.callLater(0, d.callback, None)
        return

    def step_1(self, _result):
        '''transition pipeline state to gitting

        1. check that the pipeline is active and return failure message if not
        2. check that the revision has not been applied already returning a
           failure message if it has
        3. call gitting_trigger() to move the FSM state to gitting
           no other code is run during the trigger
        '''
        if not dawgie.context.fsm.is_pipeline_active():
            LOG.warning("submit: pipeline is not active, cannot submit.")
            self.__msg = 'The pipeline is not active so cannot submit.'
            return twisted.python.failure.Failure(Exception())

        if dawgie.tools.submit.already_applied(self.__changeset, self.__repo):
            LOG.warning(
                "submit: changeset %s already in history", self.__changeset
            )
            self.__msg = f'The changeset {self.__changeset} is in history.'
            return twisted.python.failure.Failure(Exception())

        # Go To: gitting state
        dawgie.context.fsm.gitting_trigger()
        return None

    def step_2(self, _result):
        '''prepare branch for deployment

        The desire is that the stable branch is updated to the revision, dawgie
        compliance is then used to validate the code should be successful, then
        the operational branch is updated to the revision.

        There should be no change of state out of gitting.
        '''
        if self.__failed:
            return None
        self.__msg = f'The submit tool could not prepare {dawgie.context.ae_repository_branch_test}.'
        status = dawgie.tools.submit.automatic(
            changeset=self.__changeset,
            loc=dawgie.context.ae_repository_remote,
            ops=dawgie.context.ae_repository_branch_ops,
            repo=self.__repo,
            spawn=VerifyHandler(self).spawn_off,
            stable=dawgie.context.ae_repository_branch_stable,
            test=dawgie.context.ae_repository_branch_test,
        )
        result = (
            None
            if status == dawgie.tools.submit.State.SUCCESS
            else twisted.python.failure.Failure(Exception())
        )
        return result

    def step_3(self, _result):
        '''go back to running and respond with status'''
        if self.__failed:
            return None
        dawgie.context.fsm.running_trigger()
        LOG.debug("Going to the crossroads.")
        self.__request.write(
            build_return_object('Submission successful scheduling update.')
        )
        try:
            self.__request.finish()
        except:  # pylint: disable=bare-except # noqa: E722
            LOG.exception('Failed to complete a successful message')
            pass
        self.__clear()
        dawgie.context.fsm.set_submit_info(self.__changeset, self.__submission)
        dawgie.context.fsm.submit_crossroads()
        return None


class VerifyHandler(twisted.internet.protocol.ProcessProtocol):
    def __init__(self, process: Process):
        self.__command = 'unknown'
        self.__process = process
        return

    def childDataReceived(self, childFD, data):
        LOG.debug('VerifyHandler.childDataReceived() %s', str(data))
        return

    def processEnded(self, reason):
        if isinstance(reason.value, twisted.internet.error.ProcessTerminated):
            LOG.critical(
                'Error while running compliant.py.    EXIT CODE: %s   SIGNAL: %s    STATUS: %s   COMMAND: "%s"',
                str(reason.value.exitCode),
                str(reason.value.signal),
                str(reason.value.status),
                self.__command,
            )
            self.__process.failure(twisted.python.failure.Failure(Exception()))
        else:
            d = twisted.internet.defer.Deferred()
            d.addCallbacks(self.__process.step_3)
            twisted.internet.reactor.callLater(0, d.callback, None)
            pass
        return

    def spawn_off(self, cmd: [str]):
        self.__command = ' '.join(cmd)
        LOG.debug('VerifyHandler.spawn_off (%s)', self.__command)
        twisted.internet.reactor.spawnProcess(
            self, cmd[0], args=cmd, env=os.environ, usePTY=True
        )
        return True
