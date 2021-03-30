'''

COPYRIGHT:
Copyright (c) 2015-2021, California Institute of Technology ("Caltech").
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

import base64
import boto3
import datetime
import dawgie.context
import dawgie.security
import json
import logging; log = logging.getLogger ('lambda function')
import os
import pickle

dawgie.context.cloud_data = 'api-key@https_url@excalibur-job.fifo@excalibur-scale@excalibur-cluster@excalibur-task'

aws_bot_public_key = '''-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

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
tMS6ZLFHNuP6zkdd/+IHIhTtgXHWR6k=
=M8NV
-----END PGP PUBLIC KEY BLOCK-----'''

dawgie_bot_public_key = '''-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1

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
j9MXah81BJp4ULWWWoyZCCxElweP8ovAv+mwO98=
=MKRM
-----END PGP PUBLIC KEY BLOCK-----'''

def lambda_handler(event, context):
    aws_bot_private_key = os.environ['AWSBOTPRIVATEKEY'].replace (';:;', '\n')

    if event['httpMethod'] == 'POST':
        dawgie.security.initialize()
        dawgie.security.extend ([aws_bot_public_key, aws_bot_private_key,
                                 dawgie_bot_public_key])
        data = event['body'] if isinstance (event['body'], dict) else json.loads (event['body'])
        sc,body = 200,exchange (data['request'])
    else: sc,body = 400,'invalid request'
    return {'statusCode':sc, 'body':body,
            'headers':{'Content-Type':'application/json'}}
