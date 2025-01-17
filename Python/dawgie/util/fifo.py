'''FIFO not supported by queue that has only unique content

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

import collections.abc


class Unique(collections.abc.MutableSet):
    def __init__(self, it: collections.abc.Iterable = None):
        self.__order = []
        self.__unique = set()
        if it:
            self |= it
        pass

    def __contains__(self, value):
        return value in self.__unique

    def __iter__(self):
        return self.__order.copy().__iter__()

    def __len__(self):
        return len(self.__unique)

    def __eq__(self, other):
        if isinstance(other, (list, Unique)):
            return self.__order == list(other)
        return set(self) == set(other)

    def __repr__(self):
        if not self:
            return f'{self.__class__.__name__}()'
        return f'{self.__class__.__name__}({self.__order})'

    def add(self, value):
        if value not in self.__unique:
            self.__unique.add(value)
            self.__order.append(value)

    def copy(self):
        return Unique(self.__order)

    def difference(self, other):
        return self.__unique.difference(other)

    def discard(self, value):
        if value in self.__unique:
            self.__order.remove(value)
            self.__unique.remove(value)

    def update(self, it: collections.abc.Iterable):
        for value in it if it else []:
            self.add(value)

    pass
