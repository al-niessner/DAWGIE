'''Built-in Front-End for DAWGIE

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

import dawgie.context
import dawgie.de
import dawgie.fe.api  # loads the api endpoints into the twisted server
import dawgie.fe.app  # loads the app endpoints into the twisted server
import dawgie.fe.basis
import dawgie.security

import logging
import os
import twisted.web.resource
import twisted.web.util

from dawgie.util import resolve_site
from pathlib import Path

LOG = logging.getLogger(__name__)


class RedirectContent(twisted.web.resource.Resource):

    isLeaf = True

    def __init__(self, url):
        twisted.web.resource.Resource.__init__(self)
        self.__url = url

    def render_GET(self, request):  # pylint: disable=invalid-name
        return twisted.web.util.redirectTo(self.__url.encode(), request)


class StaticContent(twisted.web.resource.Resource):
    isLeaf = True

    def __init__(self):
        twisted.web.resource.Resource.__init__(self)
        self.__bdir, self.__isdep = resolve_site()

    def render_GET(self, request):  # pylint: disable=invalid-name
        return _static(request.uri.decode(), self.__bdir, self.__isdep, request)


def _is_active(fn):
    try:
        is_active = dawgie.context.fsm.is_pipeline_active()
        is_active |= fn.endswith('pages/pipelines/index.html')
    except NameError:
        is_active = True
    return is_active


def _static(
    fn: str,
    bdir: str,
    isdep: bool,  # 3.0.0 remove - and anything that uses this
    request=None,
) -> bytes:
    result = ('Error: could not find static files ').encode()
    fn = fn.lstrip('/')  # since a URL, remove all leading /
    for d in [Path(dawgie.context.fe_path).resolve(), Path(bdir).resolve()]:
        ffn = (d / fn).resolve()

        if not ffn.is_relative_to(d):
            result += b'attempted jail break'
            LOG.error('tried a jailbreak with %s from %s', ffn, d)
            continue
        if ffn.is_dir():
            ffn = ffn / 'index.html'
        if ffn.is_file():
            break
        result += bytes(ffn) + b'     '

    if ffn.is_file():
        if isdep and ffn.suffix.lower() == '.html':
            with open(ffn, 'rt', encoding='utf-8') as f:
                html = f.read()
            idx = html.find("<link href='/stylesheets")
            dynamic = any(
                [
                    0 < html.find('/app/'),
                    0 < html.find('/javascripts/db.js'),
                    0 < html.find('/javascripts/schedule.js'),
                    0 < html.find('/javascripts/welcome.js'),
                ]
            )
            is_ready = _is_active(ffn) if dynamic else not dynamic
            while 0 < idx:
                end = html.find('>', idx)
                fn = html[idx + 13 : html.find("'", idx + 13)]
                ffn = os.path.join(bdir, fn)
                with open(ffn, 'rt', encoding='utf-8') as f:
                    css = f.read()
                html = (
                    html[:idx] + '<style>' + css + '</style>' + html[end + 1 :]
                )
                idx = html.find("<link href='/stylesheets")
            result = (
                twisted.web.util.redirectTo(b'/pages/pipelines', request)
                if not is_ready
                else html.encode()
            )
        else:
            if request is not None and ffn.suffix.lower() == '.svg':
                request.setHeader(b'Content-Type', b'image/svg+xml')
            if request is not None and ffn.suffix.lower() == '.css':
                request.setHeader(b'Content-Type', b'text/css')
            if request is not None and ffn.suffix.lower() == '.js':
                request.setHeader(b'Content-Type', b'application/javascript')
            with open(ffn, 'rb') as f:
                result = f.read()
    else:
        LOG.warning('request for the non-existent file %s', ffn)

    return result


def root() -> 'dawgie.fe.basis.RoutePoint':
    # shared private variable
    # pylint: disable=protected-access
    dawgie.fe.basis._root.static_pages = StaticContent()
    return dawgie.fe.basis._root
