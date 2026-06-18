'''

dawgie.context.cloud_data = "api-key@https_url@sqs-name@scale-name@cluster-name@task-name"

--
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

NTR: 49811
'''

import datetime
import dawgie.context
import dawgie.pl.logger
import dawgie.pl.message
import dawgie.pl.version
import dawgie.security
import dawgie.util
import logging
import logging.handlers
import os
import sys

from collections import deque

LOG = logging.getLogger(__name__)
LOGGING = None
OVERRIDES = {
    'DAWGIE_CFE_PORT': 'cfe_port',
    'DAWGIE_CLOUD_PORT': 'cloud_port',
    'DAWGIE_DB_HOST': 'db_host',
    'DAWGIE_DB_PORT': 'db_port',
    'DAWGIE_FARM_PORT': 'farm_port',
    'DAWGIE_FE_PORT': 'fe_port',
    'DAWGIE_LOG_PORT': 'log_port',
}


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


class LogManager(logging.Handler):
    '''Manages the two-phase worker logging lifecycle.'''

    def __init__(self) -> None:
        super().__init__()
        self._log_queue: deque = deque()
        self._fallback_console_handler: logging.StreamHandler | None = None
        logging.getLogger().setLevel(logging.NOTSET)
        logging.getLogger().addHandler(self)
        self._fallback_console_handler = logging.StreamHandler(sys.stderr)
        self._fallback_console_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(dawgie.pl.logger.FORMAT)
        self._fallback_console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self._fallback_console_handler)
        logging.captureWarnings(True)

    def emit(self, record: logging.LogRecord) -> None:
        '''Intercepts and stores records into the internal deque during Phase 1.'''
        self._log_queue.append(record)

    def reassign(self, host: str) -> None:
        '''Flushes queued logs and routes all future logs to the server.

        Uses parameters from the updated dawgie.context module.
        '''
        logging.getLogger().handlers.clear()
        self._fallback_console_handler.close()
        handler = dawgie.pl.logger.TwistedHandler(
            host=host, port=dawgie.context.log_port
        )
        handler.setLevel(dawgie.context.log_level)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(dawgie.context.log_level)
        while self._log_queue:
            record = self._log_queue.popleft()
            if record.levelno >= dawgie.context.log_level:
                handler.handle(record)


def load_context_with_overrides(context: bytes):
    dawgie.context.loads(context)
    for envkey, varname in OVERRIDES.items():
        value = os.environ.get(envkey, '')
        if value:
            try:
                setattr(dawgie.context, varname, int(value))
            except ValueError:
                LOG.exception('the value "%s" is not an integer', value)
