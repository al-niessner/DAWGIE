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

import unittest

from dawgie.db.search import PARAMS, Facade, Range


class DbSearchFacadeScrub(unittest.TestCase):
    '''verify parameter scrubbing'''

    def test_runids(self):
        kwds = {
            key: None for key in ['targets', 'tasks', 'algs', 'svs', 'vals']
        }
        self.assertEqual(
            PARAMS([-1], **kwds), Facade._scrub(PARAMS('-1', **kwds))
        )
        self.assertEqual(
            PARAMS([1, 6, 9], **kwds), Facade._scrub(PARAMS('9,1,6', **kwds))
        )
        self.assertEqual(
            PARAMS([Range(1, 10)], **kwds),
            Facade._scrub(PARAMS('1:10', **kwds)),
        )
        self.assertEqual(
            PARAMS([Range(1, 10)], **kwds),
            Facade._scrub(PARAMS('6,1:10,9', **kwds)),
        )
        self.assertEqual(
            PARAMS([Range(1, 10), 10], **kwds),
            Facade._scrub(PARAMS('6,1:10,9, 10', **kwds)),
        )
        self.assertEqual(
            PARAMS([Range(2, 20)], **kwds),
            Facade._scrub(PARAMS('6,,13:20,10,2:15', **kwds)),
        )
        self.assertEqual(
            PARAMS([Range(2, None)], **kwds),
            Facade._scrub(PARAMS('6,,13:,10,2:15', **kwds)),
        )
        self.assertEqual(
            PARAMS([Range(0, 20)], **kwds),
            Facade._scrub(PARAMS('6,,13:20,10,:15', **kwds)),
        )
        self.assertEqual(
            PARAMS([Range(0, None)], **kwds),
            Facade._scrub(PARAMS('6,,13:,10,:15', **kwds)),
        )
        self.assertEqual(
            PARAMS([Range(0, None)], **kwds),
            Facade._scrub(PARAMS('6,,13:20,10,2:15,:', **kwds)),
        )
