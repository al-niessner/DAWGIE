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

import bokeh.embed
import bokeh.model
import bokeh.plotting
import dawgie
import numpy


class StateVector(dawgie.StateVector):
    def __init__(self):
        dawgie.StateVector.__init__(self)
        self['image'] = Value(None)
        self._version_ = dawgie.VERSION(1, 0, 0)
        return

    def name(self):
        return 'test'

    def view(self, visitor: dawgie.Visitor):
        fig = bokeh.plotting.figure(
            title='Current state of the data',
            x_range=[0, self['image'].array().shape[1]],
            y_range=[0, self['image'].array().shape[0]],
        )
        fig.image(
            image=[self['image'].array()],
            x=[0],
            y=[0],
            dw=[self['image'].array().shape[1]],
            dn=[self['image'].array().shape[0]],
            palette='Greys256',
        )
        js, div = bokeh.embed.components(fig)
        visitor.add_declaration(None, div=div, js=js)
        return

    pass


class Value(dawgie.Value):
    def __init__(self, array: numpy.ndarray = None, uid: int = 0):
        dawgie.Value.__init__(self)
        self.__array = array
        self.__uid = uid
        self._version_ = dawgie.VERSION(1, 0, 0)
        return

    def array(self) -> numpy.ndarray:
        return self.__array

    def features(self):
        return []

    def uid(self) -> int:
        return self.__uid

    pass
