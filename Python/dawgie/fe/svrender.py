'''Define a deferred rendering of a state vector

COPYRIGHT:
Copyright (c) 2015-2026, California Institute of Technology ("Caltech").
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

from dawgie.fe.basis import DeferContainer, Status, build_return_object

import dawgie

import logging
import twisted.internet.threads

LOG = logging.getLogger(__name__)


class Defer(DeferContainer):
    @staticmethod
    def _db_item(display: dawgie.Visitor, identity, fullname: str) -> None:
        LOG.info('Translating state vector %s to view', fullname)
        runid, tn, task, alg, sv = fullname.split('.')
        dawgie.db.view(display, identity, int(runid), tn, task, alg, sv)
        LOG.info('Translated state vector %s to view', fullname)
        return

    def __call__(
        self, path: [str] = None, form: [str] = None, fullname: [str] = None
    ):
        form = form[0].lower() if form and form[0] else 'html'
        fullname = fullname[0] if fullname and fullname[0] else None
        path = path[0] if path and path[0] else None
        if path == fullname:
            path = None
        if path and fullname:
            return build_return_object(
                None,
                Status.FAILURE,
                f'both path={path} and fullname={fullname} were given but '
                'not the same. Use fullname because psth is deprecated.',
            )
        if not path and not fullname:
            return build_return_object(
                None,
                Status.FAILURE,
                'Neither path nor fullname were given. Use fullname because '
                'psth is deprecated.',
            )
        fullname = path if path else fullname
        known = ['html']
        if form.lower() not in known:
            return build_return_object(
                None,
                Status.FAILURE,
                f'form={form} is not one of the known display types: {known}',
            )
        LOG.info('Request to dispaly %s in %s', fullname, form)
        display = dawgie.de.factory(form)
        d = twisted.internet.threads.deferToThread(
            self._db_item,
            display=display,
            identity=self.identity,
            fullname=fullname,
        )
        h = Renderer(display, fullname, self.request)
        d.addCallbacks(h.success, h.failure)
        return twisted.web.server.NOT_DONE_YET


class Renderer:
    def __init__(self, display, fullname, request):
        object.__init__(self)
        self.__display = display
        self.__fullname = fullname
        self.__request = request
        return

    def failure(self, result):
        self.__request.write(
            b'<h1>Dynamic Content Generation Failed</h1><p>'
            + str(result).replace('\n', '<br/>').encode()
            + b'</p>'
        )
        try:
            LOG.info('try to call finish with error: %s', str(self.__request))
            self.__request.finish()
            LOG.info(
                'completed view for state vector %s with error', self.__fullname
            )
        except:  # noqa: E722 # pylint: disable=bare-except
            LOG.exception('Failed to complete an error page: %s', str(result))
        return

    def success(self, result):
        self.__request.write(self.__display.render().encode())
        try:
            LOG.info('try to call finish: %s', str(self.__request))
            self.__request.finish()
            LOG.info('completed view for state vector %s', self.__fullname)
        except:  # noqa: E722 # pylint: disable=bare-except
            LOG.exception(
                'Failed to complete a successful page: %s', str(result)
            )
        return
