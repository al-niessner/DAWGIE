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

import dawgie


class Container(dawgie.Aspect):
    def __init__(self, l1=None, l2=None, parent=None):
        self.__l1 = l1
        self.__l2 = l2
        self.__parent = parent if parent else self
        return

    def __contains__(self, item):
        return item in self.keys()

    def __getitem__(self, key):
        # pylint: disable=protected-access
        if self.__l1 is None:
            result = Container(key, self.__l2, self.__parent)
        elif self.__l2 is None:
            result = Container(self.__l1, key, self.__parent)
        else:
            result = self.__parent._fill_item(self.__l1, self.__l2, key)
        return result

    def __iter__(self):
        # pylint: disable=protected-access
        yield from self.__parent._ckeys(self.__l1, self.__l2)
        return

    def __len__(self):
        return len(list(self.__parent._ckeys(self.__l1, self.__l2)))

    def _ckeys(self, l1k, l2k):
        raise NotImplementedError()

    def _fill_item(self, l1k, l2k, l3k):
        raise NotImplementedError()

    def items(self):
        '''genrator of current (key,value) pairs'''
        yield from zip(self.keys(), self.values())
        return

    def keys(self):
        '''generator of current level of keys'''
        yield from self
        return

    def values(self):
        '''generator of current level of values'''
        # not a full dict so pylint: disable=consider-using-dict-items
        for k in self.keys():
            yield self[k]
        return

    pass
