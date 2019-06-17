''' Front-End for SDP

COPYRIGHT:
Copyright (c) 2015-2019, California Institute of Technology ("Caltech").
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

import enum
import inspect
import logging; log = logging.getLogger(__name__)
import os
import twisted.web.resource
import twisted.web.util

class HttpMethod(enum.Enum):
    GET = 0
    POST = 1
    PUT = 2
    DEL = 3
    pass

class DynamicContent(twisted.web.resource.Resource):
    # pylint: disable=dangerous-default-value
    isLeaf = True
    def __init__ (self, fnc, uri: str, methods:[HttpMethod]=[HttpMethod.GET]):
        twisted.web.resource.Resource.__init__(self)
        self.__fnc = fnc
        self.__methods = methods
        self.__uri = uri
        while uri.startswith ('/'): uri = uri[1:]
        point = _root
        for node in uri.split ('/')[:-1]:
            if node.encode() not in point.children:
                point.putChild (node.encode(), RoutePoint(node))
                pass

            point = point.children[node.encode()]
            pass
        node = uri.split ('/')[-1].encode()

        if node not in point.children: point.putChild (node, self)
        return

    def __err (self, method:HttpMethod):
        return ('<h1>Dynamic Content Lookup Failed</h1><p>The uri "%(uri)s" is not mapped to HTTP method %(method)s</p>' %
                {'method':str(method), 'uri':self.__uri}).encode()

    def __render (self, request, method:HttpMethod):
        sig = inspect.signature (self.__fnc)
        display = 'display' in sig.parameters and \
                  sig.parameters['display'].annotation == dawgie.Visitor
        kwds = {} if not display else \
               {'display':dawgie.de.factory (dawgie.de.Type.html)}
        for ak in request.args.keys():
            if ak.decode() in sig.parameters:
                kwds[ak.decode()] = [a.decode() for a in request.args[ak]]
                pass
            pass

        if 0 < self.__methods.count (method):
            if 'display' in kwds:
                d = twisted.internet.threads.deferToThread(self.__fnc, **kwds)
                h = Renderer(kwds['display'], request)
                d.addCallbacks (h.success, h.failure)
                resp = twisted.web.server.NOT_DONE_YET
            else: resp = self.__fnc(**kwds)
        else: resp = self.__err (method)

        return resp

    def render_GET    (self, req): return self.__render (req, HttpMethod.GET)
    def render_POST   (self, req): return self.__render (req, HttpMethod.POST)
    def render_PUT    (self, req): return self.__render (req, HttpMethod.PUT)
    def render_DELETE (self, req): return self.__render (req, HttpMethod.DEL)
    pass

class RedirectContent(twisted.web.resource.Resource):

    isLeaf = True
    def __init__ (self, url):
        twisted.web.resource.Resource.__init__(self)
        self.__url = url
        pass

    def render_GET (self, request):
        return twisted.web.util.redirectTo (self.__url.encode(), request)
    pass

class Renderer(object):
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
        except: log.exception ('Failed to complete an error page: ' +
                               str (result))
        return

    def success (self, result):
        # pylint: disable=bare-except
        self.__request.write (self.__display.render().encode())
        try: self.__request.finish()
        except: log.exception ('Failed to complete a successful page: ' +
                               str (result))
        return
    pass

class RoutePoint(twisted.web.resource.Resource):
    isLeaf = False
    def __init__ (self, name):
        twisted.web.resource.Resource.__init__(self)
        self.__name = name
        return

    def getChild (self, path, request):
        return twisted.web.resource.ErrorPage(404,
                                              'Could not locate requested URI',
                                              '<p>%(my_name)s.getChild().name:         %(name)s<br>%(my_name)s.getChild().request.uri:  %(uri)s</p>' %
                                              {'my_name':self.__name,
                                               'name': path.decode(),
                                               'uri':request.uri.decode()})
    pass

class StaticContent(twisted.web.resource.Resource):
    isLeaf = True
    def __init__ (self, bdir=os.path.dirname (os.path.abspath (__file__))):
        twisted.web.resource.Resource.__init__(self)
        self.__bdir = bdir
        pass

    def render_GET (self, request):
        return _static (request.uri.decode(), self.__bdir, request)
    pass

def _is_active (fn):
    try:
        is_active = dawgie.pl.start.sdp.is_pipeline_active()
        is_active |= fn.endswith ('pages/pipelines/index.html')
    except NameError: is_active = True
    return is_active

def _static (fn:str,
             bdir:str=os.path.dirname(os.path.abspath (__file__)),
             request=None)->bytes:
    if -1 < fn.find ('..'):
        return ('Error: path must be absolute and not relative.').encode()

    while fn.startswith ('/'): fn = fn[1:]
    result = ('Error: could not find static files ').encode()
    for d in [dawgie.context.fe_path, bdir]:
        ffn = os.path.join (d, fn)

        if os.path.isdir (ffn): ffn = os.path.join (ffn, 'index.html')
        if os.path.isfile (ffn): break
        else: result += ffn.encode() + b'     '
        pass

    if os.path.isfile (ffn):
        if ffn.endswith ('.html'):
            with open (ffn, 'rt', encoding='utf-8') as f: html = f.read()
            idx = html.find ("<link href='/stylesheets")
            dynamic = any ([0 < html.find ('/app/'),
                            0 < html.find ('/javascripts/db.js'),
                            0 < html.find ('/javascripts/schedule.js'),
                            0 < html.find ('/javascripts/welcome.js')])
            is_ready = _is_active (ffn) if dynamic else not dynamic
            while 0 < idx:
                end = html.find ('>', idx)
                fn = html[idx+13:html.find ("'", idx+13)]
                ffn = os.path.join (bdir, fn)
                with open (ffn, 'rt', encoding='utf-8') as f: css = f.read()
                html = html[:idx] + '<style>' + css + '</style>' + html[end+1:]
                idx = html.find ("<link href='/stylesheets")
                pass
            result = twisted.web.util.redirectTo (b'/pages/pipelines', request)\
                     if not is_ready else html.encode()
        else:
            if request is not None and ffn.endswith ('.svg'):
                request.setHeader (b'Content-Type', b'image/svg+xml')
                pass
            with open (ffn, 'rb') as f: result = f.read()
    else: log.warning ('request for the non-existent file %s', ffn)

    return result

_root = RoutePoint('root')
def root() -> bytes:
    _root.putChild (b'', RedirectContent('/pages/index.html'))
    _root.putChild (b'fonts', StaticContent())
    _root.putChild (b'images', StaticContent())
    _root.putChild (b'javascripts', StaticContent())
    _root.putChild (b'markdown', StaticContent())
    _root.putChild (b'pages', StaticContent())
    _root.putChild (b'partials', StaticContent())
    _root.putChild (b'scripts', StaticContent())
    _root.putChild (b'stylesheets', StaticContent())
    return _root

if __name__ == '__main__':
    import sys
    sys.path.append (os.path.abspath (os.path.join (
        os.path.dirname (os.path.abspath (__file__)), '../../..')))
    import dawgie.context
    import dawgie.db
    import dawgie.de
    import dawgie.fe.app
    import dawgie.pl.start
    dawgie.context.db_path = '/home/niessner/Data/Exoplanet/db'
    dawgie.db.open()
    # pylint: disable=protected-access
    dawgie.pl.start._run (8181, root())
else:
    import dawgie.context
    import dawgie.de
    import dawgie.fe.app
    import dawgie.pl.start
    pass
