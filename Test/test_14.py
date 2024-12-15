'''

COPYRIGHT:
Copyright (c) 2015-2024, California Institute of Technology ("Caltech").
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

import dawgie
import dawgie.db.shelve.util
import unittest


class Version(unittest.TestCase):
    def test_asstring(self):
        v1 = dawgie.db.shelve.util.LocalVersion('1.1.2')
        self.assertEqual('1.1.2', v1.asstring())
        return

    def test_eq(self):
        v1 = dawgie.db.shelve.util.LocalVersion('1.1.2')
        v2 = dawgie.db.shelve.util.LocalVersion('1.1.10')
        self.assertEqual(v1, v1)
        self.assertFalse(v1 == v2)
        return

    def test_ge(self):
        v1 = dawgie.db.shelve.util.LocalVersion('2.1.1')
        v2 = dawgie.db.shelve.util.LocalVersion('10.1.1')
        self.assertGreaterEqual(v2, v2)
        self.assertGreaterEqual(v2, v1)
        v1 = dawgie.db.shelve.util.LocalVersion('1.2.1')
        v2 = dawgie.db.shelve.util.LocalVersion('1.10.1')
        self.assertGreaterEqual(v2, v2)
        self.assertGreaterEqual(v2, v1)
        v1 = dawgie.db.shelve.util.LocalVersion('1.1.2')
        v2 = dawgie.db.shelve.util.LocalVersion('1.1.10')
        self.assertGreaterEqual(v2, v2)
        self.assertGreaterEqual(v2, v1)
        return

    def test_gt(self):
        v1 = dawgie.db.shelve.util.LocalVersion('2.1.1')
        v2 = dawgie.db.shelve.util.LocalVersion('10.1.1')
        self.assertGreater(v2, v1)
        v1 = dawgie.db.shelve.util.LocalVersion('1.2.1')
        v2 = dawgie.db.shelve.util.LocalVersion('1.10.1')
        self.assertGreater(v2, v1)
        v1 = dawgie.db.shelve.util.LocalVersion('1.1.2')
        v2 = dawgie.db.shelve.util.LocalVersion('1.1.10')
        self.assertGreater(v2, v1)
        return

    def test_le(self):
        v1 = dawgie.db.shelve.util.LocalVersion('2.1.1')
        v2 = dawgie.db.shelve.util.LocalVersion('10.1.1')
        self.assertLessEqual(v1, v1)
        self.assertLessEqual(v1, v2)
        v1 = dawgie.db.shelve.util.LocalVersion('1.2.1')
        v2 = dawgie.db.shelve.util.LocalVersion('1.10.1')
        self.assertLessEqual(v1, v1)
        self.assertLessEqual(v1, v2)
        v1 = dawgie.db.shelve.util.LocalVersion('1.1.2')
        v2 = dawgie.db.shelve.util.LocalVersion('1.1.10')
        self.assertLessEqual(v1, v1)
        self.assertLessEqual(v1, v2)
        return

    def test_lt(self):
        v1 = dawgie.db.shelve.util.LocalVersion('2.1.1')
        v2 = dawgie.db.shelve.util.LocalVersion('10.1.1')
        self.assertLess(v1, v2)
        v1 = dawgie.db.shelve.util.LocalVersion('1.2.1')
        v2 = dawgie.db.shelve.util.LocalVersion('1.10.1')
        self.assertLess(v1, v2)
        v1 = dawgie.db.shelve.util.LocalVersion('1.1.2')
        v2 = dawgie.db.shelve.util.LocalVersion('1.1.10')
        self.assertLess(v1, v2)
        return

    def test_ne(self):
        v1 = dawgie.db.shelve.util.LocalVersion('1.1.2')
        v2 = dawgie.db.shelve.util.LocalVersion('1.1.10')
        self.assertNotEqual(v1, v2)
        return

    def test_newer(self):
        v1 = dawgie.db.shelve.util.LocalVersion('1.1.2')
        v2 = dawgie.db.shelve.util.LocalVersion('1.1.10')
        self.assertLess('1.1.10', '1.1.2')  # show strings do not behave
        self.assertFalse(v1.newer(v1._get_ver()))
        self.assertFalse(v1.newer(v2._get_ver()))
        return

    def test_sort(self):
        v1 = dawgie.db.shelve.util.LocalVersion('1.1.1')
        v2 = dawgie.db.shelve.util.LocalVersion('1.1.2')
        v3 = dawgie.db.shelve.util.LocalVersion('1.1.7')
        v4 = dawgie.db.shelve.util.LocalVersion('1.1.8')
        v5 = dawgie.db.shelve.util.LocalVersion('1.1.10')
        ordered = sorted([v3, v1, v2, v5, v4])
        for ver in ordered:
            print('ver:', ver.asstring())
        self.assertEqual(v1, ordered[0])
        self.assertEqual(v2, ordered[1])
        self.assertEqual(v3, ordered[2])
        self.assertEqual(v4, ordered[3])
        self.assertEqual(v5, ordered[4])
        return

    pass
