'''Built-in Front-End for DAWGIE

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

import dawgie.context
import dawgie.de
import dawgie.fe.app
import dawgie.fe.basis
import dawgie.security
import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import os
import twisted.web.resource
import twisted.web.util


class RedirectContent(twisted.web.resource.Resource):

    isLeaf = True

    def __init__(self, url):
        twisted.web.resource.Resource.__init__(self)
        self.__url = url
        pass

    def render_GET(self, request):  # pylint: disable=invalid-name
        return twisted.web.util.redirectTo(self.__url.encode(), request)

    pass


class StaticContent(twisted.web.resource.Resource):
    isLeaf = True

    def __init__(self, bdir=os.path.dirname(os.path.abspath(__file__))):
        twisted.web.resource.Resource.__init__(self)
        self.__bdir = bdir
        pass

    def render_GET(self, request):  # pylint: disable=invalid-name
        return _static(request.uri.decode(), self.__bdir, request)

    pass


def _is_active(fn):
    try:
        is_active = dawgie.context.fsm.is_pipeline_active()
        is_active |= fn.endswith('pages/pipelines/index.html')
    except NameError:
        is_active = True
    return is_active


def _static(
    fn: str,
    bdir: str = os.path.dirname(os.path.abspath(__file__)),
    request=None,
) -> bytes:
    if -1 < fn.find('..'):
        return ('Error: path must be absolute and not relative.').encode()

    while fn.startswith('/'):
        fn = fn[1:]
    result = ('Error: could not find static files ').encode()
    for d in [dawgie.context.fe_path, bdir]:
        ffn = os.path.join(d, fn)

        if os.path.isdir(ffn):
            ffn = os.path.join(ffn, 'index.html')
        if os.path.isfile(ffn):
            break
        result += ffn.encode() + b'     '
        pass

    if os.path.isfile(ffn):
        if ffn.endswith('.html'):
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
                pass
            result = (
                twisted.web.util.redirectTo(b'/pages/pipelines', request)
                if not is_ready
                else html.encode()
            )
        else:
            if request is not None and ffn.endswith('.svg'):
                request.setHeader(b'Content-Type', b'image/svg+xml')
                pass
            with open(ffn, 'rb') as f:
                result = f.read()
    else:
        log.warning('request for the non-existent file %s', ffn)

    return result


def root() -> "dawgie.fe.basis.RoutePoint":
    # shared private variable
    # pylint: disable=protected-access
    dawgie.fe.basis._root.putChild(b'', RedirectContent('/pages/index.html'))
    dawgie.fe.basis._root.putChild(b'fonts', StaticContent())
    dawgie.fe.basis._root.putChild(b'images', StaticContent())
    dawgie.fe.basis._root.putChild(b'javascripts', StaticContent())
    dawgie.fe.basis._root.putChild(b'markdown', StaticContent())
    dawgie.fe.basis._root.putChild(b'pages', StaticContent())
    dawgie.fe.basis._root.putChild(b'partials', StaticContent())
    dawgie.fe.basis._root.putChild(b'scripts', StaticContent())
    dawgie.fe.basis._root.putChild(b'stylesheets', StaticContent())
    return dawgie.fe.basis._root
