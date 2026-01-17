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

import datetime
import dawgie.security
import enum
import inspect
import json
import logging; log = logging.getLogger(__name__)  # fmt: skip # noqa: E702 # pylint: disable=multiple-statements
import os
import twisted.web.resource


class HttpMethod(enum.Enum):
    GET = 0
    POST = 1
    PUT = 2
    DEL = 3
    pass


class Defer:
    def __init__(self):
        self.identity = None
        self.request = None

    @property
    def identity(self):
        return self.__identity

    @identity.setter
    def identity(self, ident):
        self.__identity = ident

    @property
    def request(self):
        return self.__request

    @request.setter
    def request(self, req):
        self.__request = req

    pass


class DynamicContent(twisted.web.resource.Resource):
    # pylint: disable=dangerous-default-value
    isLeaf = True

    def __init__(self, fnc, uri: str, methods: [HttpMethod] = [HttpMethod.GET]):
        twisted.web.resource.Resource.__init__(self)
        self.__fnc = fnc
        self.__methods = methods
        self.__uri = uri
        while uri.startswith('/'):
            uri = uri[1:]
        point = _root
        for node in uri.split('/')[:-1]:
            if node.encode() not in point.children:
                point.putChild(node.encode(), RoutePoint(node))
                pass

            point = point.children[node.encode()]
            pass
        node = uri.split('/')[-1].encode()

        if node not in point.children:
            point.putChild(node, self)
        return

    def __err(self, method: HttpMethod):
        return build_return_object(
            None,
            Status.FAILURE,
            f'Dynamic Content Lookup Failed. The uri "{self.__uri}" is not mapped to HTTP method {method}.',
        )

    def __render(self, request, method: HttpMethod):
        sig = inspect.signature(self.__fnc)
        kwds = {}
        if 'getPeerCertificate' in dir(request.transport):
            cert = request.transport.getPeerCertificate()
        else:
            cert = None

        if not dawgie.security.sanctioned(self.__uri, cert):
            msg = f'The endpoint {self.__uri} requires a client certficate to be provided and that certificate be known to this service.'
            response = build_return_object(None, Status.FAILURE, msg, False)
            response.update(
                {
                    'alert_status': 'danger',
                    'alert_message': msg,
                }
            )
            return json.dumps(response).encode()

        for ak in request.args.keys():
            if ak.decode() in sig.parameters:
                kwds[ak.decode()] = [a.decode() for a in request.args[ak]]
                pass
            pass

        if isinstance(self.__fnc, Defer):
            self.__fnc.identity = dawgie.security.identity(cert)
            self.__fnc.request = request
        if 0 < self.__methods.count(method):
            try:
                resp = self.__fnc(**kwds)
            except Exception as e:  # pylint: disable=broad-exception-caught
                log.exception('Unhandled dynamic front end excpetion')
                resp = build_return_object(None, Status.ERROR, str(e))
        else:
            resp = self.__err(method)

        return resp

    def render_GET(self, req):  # pylint: disable=invalid-name
        return self.__render(req, HttpMethod.GET)

    def render_POST(self, req):  # pylint: disable=invalid-name
        return self.__render(req, HttpMethod.POST)

    def render_PUT(self, req):  # pylint: disable=invalid-name
        return self.__render(req, HttpMethod.PUT)

    def render_DELETE(self, req):  # pylint: disable=invalid-name
        return self.__render(req, HttpMethod.DEL)

    pass


class RoutePoint(twisted.web.resource.Resource):
    isLeaf = False

    def __init__(self, name):
        twisted.web.resource.Resource.__init__(self)
        self.__name = name
        return

    def getChild(self, path, request):
        msg = (
            request.uri.decode()
            if os.environ.get('DAWGIE_FE_DEBUG', '')
            else 'DAWGIE_FE_DEBUG'
        )
        try:
            dpath = path.decode()
        except UnicodeDecodeError:
            dpath = 'cannot decode "path"'
        return twisted.web.resource.ErrorPage(
            404,
            'Could not locate requested URI',
            '<p>%(my_name)s.getChild().name:         %(name)s<br>%(my_name)s.getChild().request.uri:  %(uri)s</p>'
            % {'my_name': self.__name, 'name': dpath, 'uri': msg},
        )

    pass


@enum.unique
class Status(enum.Enum):
    ERROR = enum.auto()
    FAILURE = enum.auto()
    SUCCESS = enum.auto()


_root = RoutePoint('root')


def build_return_object(
    obj, status: Status = Status.SUCCESS, msg: str = '', encode=True
):
    if status != Status.SUCCESS:
        obj = datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')
    if msg is None:
        msg = ''
    if not msg and status != Status.SUCCESS:
        msg = "was not successful, but no hints are being given to the reader"
    response = {'content': obj, 'message': msg, 'status': status.name.lower()}
    if encode:
        return json.dumps(response).encode()
    return response
