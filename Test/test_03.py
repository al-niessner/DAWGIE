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
import dawgie.util.args
import logging
import os
import tempfile
import twisted.internet
import unittest


class Logger(unittest.TestCase):
    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)
        fid, self.log_path = tempfile.mkstemp()
        os.close(fid)
        with open(self.log_path, 'tw') as file:
            file.write('yup\n')
        self.aborted = False
        pass

    def _abort(self):
        self.aborted = True
        self._stop()
        return

    def _log_msg(self):
        self.mylog.warning('some text %s', ', more text')
        twisted.internet.reactor.callLater(1, self._stop)
        return

    def _start_logger(self):
        dawgie.pl.logger.start(self.log_path, dawgie.context.log_port)
        self.handler = dawgie.pl.logger.TwistedHandler(
            host='localhost', port=dawgie.context.log_port
        )
        logging.basicConfig(level=logging.INFO)
        logging.captureWarnings(True)
        self.mylog = logging.getLogger(__name__)
        self.mylog.addHandler(self.handler)
        return

    def _stop(self):
        twisted.internet.reactor.stop()
        return

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
        return

    def test_issue_236(self):
        self.assertEqual(10, dawgie.util.args.log_level('10'))
        self.assertEqual(
            logging.INFO, dawgie.util.args.log_level('logging.INFO')
        )
        return

    pass
