'''

COPYRIGHT:
Copyright (c) 2015-2020, California Institute of Technology ("Caltech").
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
import dawgie.pl.promotion
import unittest

class PromotionEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.promote = dawgie.pl.promotion.Engine()
        dawgie.context.allow_promotion = True
        return

    def test_call(self):
        with self.assertLogs ('dawgie.pl.promotion', level=0) as al:
            self.assertFalse (self.promote ([('a.b.c',True)]))
            pass
        print (al.output)
        self.assertEqual (al.output, ['ERROR:dawgie.pl.promotion:Inconsistent arguments. Ignoring request.'])
        self.assertFalse (self.promote ([('a.b.c',True)], 'a.b', 1))
        self.assertTrue (self.promote ([('a.b.c',True), ('a.b.d',False)],
                                       'a.b', 1))
        self.promote.clear()
        self.assertFalse (self.promote.more())
        return

    def test_do_allows(self):
        '''test allow to run conditions
        1. dawgie.context.allow_promotion is False
        2. No AE
        3. No organizer
        '''
        self.promote.clear()
        self.assertFalse (self.promote.more())
        with self.assertRaises (ValueError): self.promote.do()
        self.promote.ae = 1
        with self.assertRaises (ValueError): self.promote.do()
        ac = dawgie.context.allow_promotion
        dawgie.context.allow_promotion = False
        self.assertTrue (self.promote ([('a.b.c',True), ('a.b.d',False)],
                                       'a.b', 1))
        self.assertFalse (self.promote.do())
        dawgie.context.allow_promotion = ac
        return
    pass
