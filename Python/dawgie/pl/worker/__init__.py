'''

dawgie.context.cloud_data = "api-key@https_url@sqs-name@scale-name@cluster-name@task-name"

--
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

NTR: 49811
'''

import datetime
import dawgie.pl.logger
import dawgie.pl.message
import dawgie.pl.version
import dawgie.security
import dawgie.util


class Context:
    def __init__(self, address: (str, int), revision: str):
        self.__address = address
        self.__revision = revision
        pass

    def _communicate(self, msg):
        s = dawgie.security.connect(self.__address)
        dawgie.pl.message.send(msg, s)
        m = dawgie.pl.message.receive(s)
        s.close()
        return m

    def abort(self) -> bool:
        m = self._communicate(
            dawgie.pl.message.make(
                typ=dawgie.pl.message.Type.status, rev=self.__revision
            )
        )
        return m.type == dawgie.pl.message.Type.response and not m.success

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def run(self, factory, ps_hint, jobid, runid, target, timing) -> [str]:
        task = (
            factory(dawgie.util.task_name(factory), ps_hint, runid, target)
            if runid and target
            else (
                factory(dawgie.util.task_name(factory), ps_hint, runid)
                if runid
                else factory(dawgie.util.task_name(factory), ps_hint, target)
            )
        )
        setattr(task, 'abort', self.abort)
        dawgie.pl.version.record(task, only=jobid.split('.')[1])
        timing['started'] = datetime.datetime.now(datetime.UTC)
        task.do(goto=jobid.split('.')[1])
        timing.update(task.timing())
        return task.new_values()

    pass
