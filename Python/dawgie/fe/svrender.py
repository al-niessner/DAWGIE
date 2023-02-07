'''Define a deferred rendering of a state vector

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

from dawgie.fe import Defer as absDefer

import dawgie
import logging; log = logging.getLogger(__name__)
import twisted.internet.threads

class Defer(absDefer):
    @staticmethod
    def _db_item (display:dawgie.Visitor, path:str)->None:
        runid,tn,task,alg,sv = path[0].split ('.')
        dawgie.db.view (display, int(runid), tn, task, alg, sv)
        return

    def __call__ (self, path:str):
        display = dawgie.de.factory()
        d = twisted.internet.threads.deferToThread(self._db_item,
                                                   display=display, path=path)
        h = Renderer(display, self.get_request())
        d.addCallbacks (h.success, h.failure)
        return twisted.web.server.NOT_DONE_YET
    pass

class Renderer:
    def __init__ (self, display, request):
        object.__init__(self)
        self.__display = display
        self.__request = request
        return

    def failure (self, result):
        # pylint: disable=bare-except
        self.__request.write (b'<h1>Dynamic Content Generation Failed</h1><p>' +
                              str (result).replace ('\n','<br/>').encode() +
                              b'</p>')
        try: self.__request.finish()
        except: log.exception ('Failed to complete an error page: %s',
                               str (result))
        return

    def success (self, result):
        # pylint: disable=bare-except
        self.__request.write (self.__display.render().encode())
        try: self.__request.finish()
        except: log.exception ('Failed to complete a successful page: %s',
                               str (result))
        return
    pass
