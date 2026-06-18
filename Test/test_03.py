'''

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

import dawgie.context
import dawgie.pl.logger
import dawgie.pl.logger.chronicle
import dawgie.util.args
import io
import json
import logging
import os
import shutil
import tempfile
import types
import twisted.internet
import unittest

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

RECORD = {
    "changeset": "f2b2db7fa9979c3bfbc22b5dadf163335b1e6be5",
    "runid": 1540,
    "status": "success",
    "target": "HD 15337",
    "task": "transit.spectrum",
    "timing": {
        "scheduled": datetime.fromisoformat("2026-06-06 05:25:50.950738+00:00"),
        "started": datetime.fromisoformat("2026-06-06 05:25:52.477235+00:00"),
        "completed": datetime.fromisoformat("2026-06-06 05:26:05.075088+00:00"),
    },
    "version": "1.3.2",
}


class Chronicles(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.tempdir = tempfile.TemporaryDirectory()
        dawgie.context.data_dbs = self.tempdir.name

    @classmethod
    def tearDownClass(self):
        self.tempdir.cleanup()

    def test_append(self):
        completed = datetime(2017, 3, 5, 13, 7, 37, tzinfo=UTC)
        offset = timedelta(seconds=11)
        for i in range(5):
            record = deepcopy(RECORD)
            record['runid'] = 1540 + i // 3
            record['status'] = 'failure' if i % 2 else 'success'
            record['timing']['completed'] = completed + (offset * i)
            dawgie.pl.logger.chronicle.append(record)
        path = os.path.join(
            dawgie.context.data_dbs, 'chronicles', '2017', '03', '05'
        )
        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isdir(path))
        self.assertEqual(['1540.json', '1541.json'], sorted(os.listdir(path)))
        fn = os.path.join(path, '1540.json')
        self.assertTrue(os.path.isfile(fn))
        with open(fn, 'rt', encoding='utf-8') as file:
            entries = json.load(file)
        self.assertEqual(3, len(entries))
        fn = os.path.join(path, '1541.json')
        self.assertTrue(os.path.isfile(fn))
        with open(fn, 'rt', encoding='utf-8') as file:
            entries = json.load(file)
        self.assertEqual(2, len(entries))

    def test_find(self):
        shutil.rmtree(
            os.path.join(dawgie.context.data_dbs, 'chronicles', '2017'),
            ignore_errors=True,
        )
        completed = datetime(2017, 7, 5, 13, 3, 37, tzinfo=UTC)
        offset = timedelta(seconds=11)
        for i in range(13):
            record = deepcopy(RECORD)
            record['runid'] = 1550 + i // 3
            record['status'] = 'failure' if i % 2 else 'success'
            record['timing']['completed'] = completed + (offset * i)
            dawgie.pl.logger.chronicle.append(record)
        completed = datetime(2017, 3, 7, 11, 13, 37, tzinfo=UTC)
        offset = timedelta(seconds=11)
        for i in range(11):
            record = deepcopy(RECORD)
            record['runid'] = 1540 + i // 3
            record['status'] = 'failure' if i % 2 else 'success'
            record['timing']['completed'] = completed + (offset * i)
            dawgie.pl.logger.chronicle.append(record)
        completed = datetime(2017, 3, 5, 13, 7, 37, tzinfo=UTC)
        offset = timedelta(seconds=11)
        for i in range(7):
            record = deepcopy(RECORD)
            record['runid'] = 1540 + i // 3
            record['status'] = 'failure' if i % 2 else 'success'
            record['timing']['completed'] = completed + (offset * i)
            dawgie.pl.logger.chronicle.append(record)
        completed = datetime(2011, 3, 5, 13, 7, 37, tzinfo=UTC)
        offset = timedelta(seconds=11)
        for i in range(5):
            record = deepcopy(RECORD)
            record['runid'] = 1540 + i // 3
            record['status'] = 'failure' if i % 2 else 'success'
            record['timing']['completed'] = completed + (offset * i)
            dawgie.pl.logger.chronicle.append(record)
        entries = dawgie.pl.logger.chronicle.find(
            after=datetime(2017, 7, 1, tzinfo=UTC)
        )
        self.assertEqual(7, len(entries))
        entries = dawgie.pl.logger.chronicle.find(
            after=datetime(2017, 7, 1, tzinfo=UTC), succeeded=False
        )
        self.assertEqual(6, len(entries))
        entries = dawgie.pl.logger.chronicle.find(before=datetime.now(UTC))
        self.assertEqual(20, len(entries))
        entries = dawgie.pl.logger.chronicle.find(limit=10)
        self.assertEqual(10, len(entries))
        entries = dawgie.pl.logger.chronicle.find(
            after=datetime(2017, 1, 1, tzinfo=UTC),
            before=datetime(2018, 1, 1, tzinfo=UTC),
        )
        self.assertEqual(17, len(entries))
        entries = dawgie.pl.logger.chronicle.find(
            after=datetime(2017, 1, 1, tzinfo=UTC),
            before=datetime(2018, 1, 1, tzinfo=UTC),
            succeeded=False,
        )
        self.assertEqual(14, len(entries))
        entries = dawgie.pl.logger.chronicle.find(
            after=datetime(2017, 1, 1, tzinfo=UTC),
            before=datetime(2018, 1, 1, tzinfo=UTC),
            limit=10,
        )
        self.assertEqual(17, len(entries))


class Logger(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        fid, self.log_path = tempfile.mkstemp()
        os.close(fid)
        with open(self.log_path, 'tw') as file:
            file.write('yup\n')
        self.aborted = False

    @classmethod
    def tearDownClass(self):
        os.unlink(self.log_path)

    def _abort(self):
        self.aborted = True
        self._stop()

    def _log_msg(self):
        self.mylog.warning('some text %s', ', more text')
        twisted.internet.reactor.callLater(1, self._stop)

    def _start_logger(self):
        dawgie.pl.logger.start(self.log_path, dawgie.context.log_port)
        self.handler = dawgie.pl.logger.TwistedHandler(
            host='localhost', port=dawgie.context.log_port
        )
        logging.basicConfig(level=logging.INFO)
        logging.captureWarnings(True)
        self.mylog = logging.getLogger(__name__)
        self.mylog.addHandler(self.handler)

    def _stop(self):
        twisted.internet.reactor.stop()

    def test_issue_45(self):
        twisted.internet.reactor.callLater(0, self._start_logger)
        twisted.internet.reactor.callLater(1, self._log_msg)
        twisted.internet.reactor.callLater(11, self._abort)
        twisted.internet.reactor.run()
        self.assertFalse(self.aborted)
        self.assertTrue(os.path.isfile(self.log_path))
        with open(self.log_path, 'rt') as f:
            text = f.read()
        self.assertTrue(text)
        self.assertLess(text.find('%s'), 0)

    def test_issue_236(self):
        self.assertEqual(10, dawgie.util.args.log_level('10'))
        self.assertEqual(
            logging.INFO, dawgie.util.args.log_level('logging.INFO')
        )

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_issue_370_pre(self, mock_stderr):
        '''Verifies dawgie.pl.worker.LogManager captures logs and echoes warnings.'''
        logging.getLogger().handlers.clear()
        test_manager = dawgie.pl.worker.LogManager()
        logger = logging.getLogger('dawgie.pl.worker.startup')
        logger.info('This info diagnostic should sit silently in the deque.')
        logger.warning('This warning must break through immediately to stderr.')
        console_output = mock_stderr.getvalue()
        self.assertIn(
            'This warning must break through immediately to stderr.',
            console_output,
        )
        self.assertNotIn(
            'This info diagnostic should sit silently in the deque.',
            console_output,
        )
        self.assertEqual(len(test_manager._log_queue), 2)
        logging.getLogger().handlers.clear()

    def test_issue_370_post(self):
        '''Verifies the global manager deque filters records and dumps cleanly to the server handler.'''
        logging.getLogger().handlers.clear()
        dawgie.context.log_level = logging.INFO
        dawgie.context.log_port = 8089
        test_manager = dawgie.pl.worker.LogManager()
        logger = logging.getLogger('dawgie.pl.worker.exec')
        logger.debug('Bypassed: Below the INFO threshold.')
        logger.info('Captured: Matches the INFO threshold.')
        logger.warning('Captured: Above the INFO threshold.')
        with patch(
            'dawgie.pl.logger.TwistedHandler',
            return_value=MagicMock(spec=logging.Handler),
        ) as mock_class:
            mock_handler_instance = mock_class.return_value
            mock_handler_instance.level = logging.INFO
            test_manager.reassign(host='localhost')
            self.assertEqual(logging.getLogger().level, logging.INFO)
            self.assertEqual(len(test_manager._log_queue), 0)
            handled_calls = mock_handler_instance.handle.call_args_list
            handled_messages = [
                call.args[0].getMessage() for call in handled_calls
            ]
            self.assertIn(
                'Captured: Matches the INFO threshold.', handled_messages
            )
            self.assertIn(
                'Captured: Above the INFO threshold.', handled_messages
            )
            self.assertNotIn(
                'Bypassed: Below the INFO threshold.', handled_messages
            )
        logging.getLogger().handlers.clear()
