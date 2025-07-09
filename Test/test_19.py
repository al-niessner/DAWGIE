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

import dawgie.db.post
import dawgie.db.shelve.model
import unittest

KEYS = ['a','b','c']

class Container:
    @property
    def container(self):
        return self._container

    def test_items(self):
        self.assertTrue(False,'implement me')

    def test_keys(self):
        self.assertEqual(KEYS, sorted(self.container),
                         'primary keys - target or runid')
        for k1 in self.container:
            keys = ['.'.join([k1,k]) for k in KEYS]
            self.assertEqual(keys, sorted(self.container[k1]),
                             'secondary keys - alg.sv')
            for k2 in self.container[k1]:
                keys = ['.'.join([k2,k]) for k in KEYS]
                self.assertEqual(keys, sorted(self.container[k1][k2]),
                                 'tertiary keys - val')
                for i,k3 in enumerate(sorted(self.container[k1][k2])):
                    self.assertEqual(i,self._container[k1][k2][k3],'value')

    def test_values(self):
        self.assertTrue(False, 'implement me')

class Post(Container,unittest.TestCase):
    def setUp(self):
        self._container = dawgie.db.post.Interface(None, None, None)
        self._container._Interface__span['table'] = fill()

class Shelve(Container,unittest.TestCase):
    def setUp(self):
        self._container = dawgie.db.shelve.model.Interface(None, None, None)
        self._container._Interface__span.update(fill())

def fill():
    result = {}
    for k1 in KEYS:
        result[k1] = {}
        for k2 in KEYS:
            result[k1]['.'.join([k1,k2])] = {}
            for k3,v in zip(KEYS,range(len(KEYS))):
                result[k1]['.'.join([k1,k2])]['.'.join([k1,k2,k3])] = v
    return result
