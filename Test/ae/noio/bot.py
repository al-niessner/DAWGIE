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

# test code so who cares; pylint: disable=duplicate-code

import ae
import ae.disk
import ae.disk.bot
import dawgie
import logging

log = logging.getLogger(__name__)
import numpy
import scipy.optimize


class Actor(dawgie.Task):
    def list(self):
        return [Engine()]

    pass


class Engine(dawgie.Algorithm):
    def __init__(self):
        dawgie.Algorithm.__init__(self)
        self.__base = ae.disk.bot.Engine()
        self.__clean = ae.StateVector()
        self._version_ = dawgie.VERSION(1, 0, 0)
        return

    @staticmethod
    def _model(p, shape):
        C, R = numpy.meshgrid(range(shape[1]), range(shape[0]))
        return numpy.sin(R / p[0] + p[1]) * numpy.cos(C / p[2] + p[3])

    @staticmethod
    def _opt(p, known):
        return numpy.abs(Engine._model(p, known.shape) - known).sum()

    def name(self):
        return 'engine'

    def previous(self):
        return [dawgie.ALG_REF(factory=ae.disk.task, impl=self.__base)]

    def run(self, ds, ps):
        image = self.__base.sv_as_dict()['test']['image'].array()
        p = [750, 0, 500, 0]
        res = scipy.optimize.minimize(Engine._opt, p, (image,), bounds=[(100, 1000), (-3.2, 3.2), (100, 1000), (-3.2, 3.2)])
        log.critical('Coefficients: %s', str(res.x))
        self.__clean['image'] = ae.Value(Engine._model(res.x, image.shape))
        ds.update()
        return

    def state_vectors(self):
        return [self.__clean]

    def where(self):
        return dawgie.Distribution.cloud

    pass
