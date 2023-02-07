'''PipeLine

The pipeline system has N goals:

  1. Provide a GUI display of what is currently happending.
  2. Discover tasks that are available.
  3. Schedule required work.
  4. Distribute work across cores and nodes.

COPYRIGHT:
Copyright (c) 2015-2023, California Institute of Technology ("Caltech").
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

import logging; log = logging.getLogger(__name__)
import twisted.internet.defer
import twisted.python.failure

class LogFailure:
    # pylint: disable=too-few-public-methods
    def __init__ (self, label, name):
        self.__label = f'co: {name} -- {label}'
        return

    def log (self, err):
        if isinstance (err, (Exception,twisted.python.failure.Failure)):
            log.exception (self.__label, exc_info=err)
        else: log.error (self.__label)
        return
    pass

class DeferWithLogOnError(LogFailure):
    def __init__ (self, cb, label, name):
        LogFailure.__init__ (self, label, name)
        self.__cb = cb
        self.__deferred = twisted.internet.defer.Deferred()
        self.__deferred.addCallback (self.run).addErrback (self.log)
        return

    @property
    def callback (self): return self.__deferred.callback
    @property
    def deferred (self): return self.__deferred

    def run (self, *_args, **_kwds): return self.__cb()
    pass

def _merge (old:int, new:int, offset:int, req:int):
    return req if (old + offset) != req else (new + offset)
