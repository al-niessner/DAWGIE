'''Define the bits of the front end that require some help from the server

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

from dawgie.fe.basis import DynamicContent, HttpMethod
from . import submit
from . import svrender

import dawgie
import dawgie.context
import enum

@enum.unique
class Status(enum):
    error = enum.auto()
    failure = enum.auto()
    success = enum.auto()

def _return_object(obj, status:Status=success, msg:str=''):
    return json.dumps({'content':obj, 'message':msg, 'status':status.name})

def ae_name():
    return _return_object(dawgie.context.ae_base_package)

DynamicContent(ae_name, '/api/ae/name')
DynamicContent(, )


'/api/ae/name'
'/api/cmd/run'
'/api/database/search'
'/api/database/search/runid'  --> no params returns max value
'/api/database/search/target' --> no params returns full list
'/api/database/search/task' --> no params returns full list
'/api/database/search/alg' --> no params returns full list
'/api/database/search/sv' --> no params returns full list
'/api/database/search/val' --> no params returns full list
'/api/df_model/statistics'
'/api/logs/recent?limit=3'
'/api/rev/current'
'/api/rev/submit'
'/api/schedule/doing'
'/api/schedule/failed'
'/api/schedule/in-progress'
'/api/schedule/stats'
'/api/schedule/succeeded'
'/api/schedule/to-do'
'/api/state/pipeline'
