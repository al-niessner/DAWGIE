'''

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

import dawgie.util.fifo
import unittest


class UniqueFiFo(unittest.TestCase):
    def test_new(self):
        todo = dawgie.util.fifo.Unique()
        self.assertIsNotNone(todo, 'should have an instance')
        self.assertEqual(0, len(todo), 'should be empty')
        todo = dawgie.util.fifo.Unique('abadfabcfdadf')
        self.assertIsNotNone(todo, 'should have an instance')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')

    def test_contains(self):
        todo = dawgie.util.fifo.Unique('abadfabcfdadf')
        self.assertIsNotNone(todo, 'should have an instance')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')
        self.assertTrue('d' in todo)
        self.assertFalse('z' in todo)

    def test_eq(self):
        todo_a = dawgie.util.fifo.Unique('abadfabcfdadf')
        self.assertIsNotNone(todo_a, 'should have an instance')
        self.assertEqual(5, len(todo_a), 'should be 5 unique character abdfc')
        order = ['a', 'b', 'd', 'f', 'c']
        self.assertEqual(todo_a, order, 'should be the same')
        self.assertEqual(todo_a, set(order), 'should be the same')
        self.assertNotEqual(todo_a, sorted(order), 'order changes it')
        todo_b = dawgie.util.fifo.Unique('abbdfcfffdadf')
        self.assertIsNotNone(todo_b, 'should have an instance')
        self.assertEqual(5, len(todo_b), 'should be 5 unique character abdfc')
        self.assertEqual(todo_a, todo_b, 'should be the same')
        todo_c = dawgie.util.fifo.Unique('abbdeceeedade')
        self.assertIsNotNone(todo_b, 'should have an instance')
        self.assertEqual(5, len(todo_b), 'should be 5 unique character abdfc')
        self.assertNotEqual(todo_b, todo_c)
        todo_d = dawgie.util.fifo.Unique('babdfcfffdadf')
        self.assertIsNotNone(todo_d, 'should have an instance')
        self.assertEqual(5, len(todo_d), 'should be 5 unique character abdfc')
        self.assertNotEqual(todo_a, todo_d, 'should not be the same')

    def test_iter(self):
        todo = dawgie.util.fifo.Unique('abadfabcfdadf')
        self.assertIsNotNone(todo, 'should have an instance')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')
        expected = ['a', 'b', 'd', 'f', 'c']
        for a, b in zip(todo, expected):
            self.assertEqual(a, b, 'each element should be the same')

    def test_add(self):
        todo = dawgie.util.fifo.Unique('abadfabcfdadf')
        self.assertIsNotNone(todo, 'should have an instance')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')
        todo.add('a')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')
        todo.add('e')
        self.assertEqual(6, len(todo), 'should be 5 unique character abdfc')
        self.assertEqual(todo, ['a', 'b', 'd', 'f', 'c', 'e'])

    def test_discard(self):
        todo = dawgie.util.fifo.Unique('abadfabcfdadf')
        self.assertIsNotNone(todo, 'should have an instance')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')
        todo.discard('z')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')
        todo.discard('d')
        self.assertEqual(4, len(todo), 'should be 5 unique character abdfc')
        self.assertEqual(todo, ['a', 'b', 'f', 'c'])

    def test_update(self):
        todo = dawgie.util.fifo.Unique()
        todo.update('abadfabcfdadf')
        self.assertIsNotNone(todo, 'should have an instance')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')
        todo.update(None)
        self.assertIsNotNone(todo, 'should have an instance')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')
        todo = todo.copy()
        self.assertIsNotNone(todo, 'should have an instance')
        self.assertEqual(5, len(todo), 'should be 5 unique character abdfc')
