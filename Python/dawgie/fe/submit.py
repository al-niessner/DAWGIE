'''Define a deferred rendering of a state vector

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

from dawgie.fe.basis import Defer as absDefer

import dawgie.context
import dawgie.tools.submit
import json
import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import os
import twisted.internet.reactor
import twisted.web.server


class Defer(absDefer):
    def __call__(self, changeset: [str], submission: [str]):
        if changeset[0].lower() != '':
            if not self.__busy:
                self.__busy = True
                process = Process(
                    changeset[0], self.clear, self.request, submission[0]
                )
                process.step_0()
                return twisted.web.server.NOT_DONE_YET

            result = {
                'alert_status': 'danger',
                'alert_message': 'Submission already in progress',
            }
        else:
            result = {
                'alert_status': 'danger',
                'alert_message': 'Cannot submit a blank changeset',
            }
        return json.dumps(result).encode()

    def __init__(self):
        absDefer.__init__(self)
        self.__busy = False
        return

    def clear(self):
        self.__busy = False

    pass


class Process:
    def __init__(self, changeset, clear, request, submission):
        object.__init__(self)
        log.debug('Process.__changeset %s', str(changeset))
        log.debug('Process.__clear %s', str(clear))
        log.debug('Process.__request %s', str(request))
        log.debug('Process.__submission %s', str(submission))
        self.__changeset = changeset
        self.__clear = clear
        self.__msg = {
            'alert_status': 'danger',
            'alert_message': 'unspecified',
        }
        self.__request = request
        self.__submission = submission
        return

    def failure(self, fail):
        if self.__request is not None:
            if dawgie.context.fsm.state == 'gitting':
                dawgie.context.fsm.running_trigger()
            else:
                log.debug(
                    'Process.failure() state is not gitting: %s',
                    str(dawgie.context.fsm.state),
                )

            self.__request.write(json.dumps(self.__msg).encode())
            try:
                self.__request.finish()
            except:  # pylint: disable=bare-except # noqa: E722
                log.exception(
                    'Failed to complete an error message: %s',
                    str(self.__msg['alert_message']),
                )
                pass
            self.__clear()
            self.__request = None
            dawgie.tools.submit.mail_out(self.__msg['alert_message'])
        else:
            log.debug('Process.failure() self.__request is None')
        return fail

    def step_0(self):
        dawgie.tools.submit.mail_list = dawgie.context.email_alerts_to
        d = twisted.internet.defer.Deferred()
        d.addCallback(self.step_1)
        d.addCallbacks(self.step_2, self.failure)
        d.addCallbacks(self.step_3, self.failure)
        twisted.internet.reactor.callLater(0, d.callback, None)
        return

    def step_1(self, _result):
        '''transition pipeline state to gitting'''
        if not dawgie.context.fsm.is_pipeline_active():
            log.warning("submit: pipeline is not active, cannot submit.")
            self.__msg = {
                'alert_status': 'danger',
                'alert_message': 'The pipeline is not active so cannot submit.',
            }
            return twisted.python.failure.Failure(Exception())

        if dawgie.context.ae_base_path.endswith(dawgie.context.ae_base_package):
            repo = os.path.dirname(dawgie.context.ae_base_path)
        else:
            repo = dawgie.context.ae_base_path
        if dawgie.tools.submit.already_applied(self.__changeset, repo):
            log.warning(
                "submit: changeset %s already in history", self.__changeset
            )
            self.__msg = {
                'alert_status': 'danger',
                'alert_message': f'The changeset {self.__changeset} is already in history.',
            }
            return twisted.python.failure.Failure(Exception())

        # Go To: gitting state
        dawgie.context.fsm.gitting_trigger()
        return None

    def step_2(self, _result):
        '''prepare_pre_ops'''
        self.__msg = {
            'alert_status': 'danger',
            'alert_message': 'The submit tool could not prepare pre_ops.',
        }
        status = dawgie.tools.submit.automatic(
            changeset=self.__changeset,
            loc=dawgie.context.ae_repository_remote,
            ops=dawgie.context.ae_repository_branch_ops,
            repo=dawgie.context.ae_base_path,
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
        dawgie.context.fsm.running_trigger()
        result = {
            'alert_status': 'success',
            'alert_message': 'Submission successful scheduling update.',
        }
        log.debug("Going to the crossroads.")
        self.__request.write(json.dumps(result).encode())
        try:
            self.__request.finish()
        except:  # pylint: disable=bare-except # noqa: E722
            log.exception(
                'Failed to complete a successful message: %s', str(result)
            )
            pass
        self.__clear()
        dawgie.context.fsm.set_submit_info(self.__changeset, self.__submission)
        dawgie.context.fsm.submit_crossroads()
        return
