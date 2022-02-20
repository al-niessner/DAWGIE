#! /usr/bin/env bash

# COPYRIGHT:
# Copyright (c) 2015-2022, California Institute of Technology ("Caltech").
# U.S. Government sponsorship acknowledged.
#
# All rights reserved.
#
# LICENSE:
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
#   - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
#   - Neither the name of Caltech nor its operating division, the Jet
# Propulsion Laboratory, nor the names of its contributors may be used to
# endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# NTR:

[ -f aws_deployment.zip ] && rm aws_deployment.zip
mkdir -p Build/dawgie/de
cp ../dawgie/*.py Build/dawgie/
cp ../dawgie/de/__init__.py Build/dawgie/de/
pip3 install -t Build/ gnupg
python3 <<EOF
with open ('aws_lambda.py', 'rt') as f: ltext = f.readlines()
with open ('../dawgie/pl/aws.py', 'rt') as f: atext = f.readlines()
retain = False
for line in atext:
    start = line.startswith ('def exchange') or line.startswith ('def _sqs_push') or line.startswith ('def _advertise') or line.startswith ('def _interview') or line.startswith ('def _hire')
    retain = retain or start
    if retain:
        if start: ltext.append ('\n')
        ltext.append (line)
        retain = not line.startswith ('    return')
        pass
    pass
with open ('Build/lambda_function.py', 'tw') as f:
    for line in ltext: f.write (line)
    pass
with open ('Build/gnupg/_util.py', 'rt') as f: text = f.read()
with open ('Build/gnupg/_util.py', 'tw') as f: f.write (text.replace ('disallow_symlinks=True', 'disallow_symlinks=False'))
EOF
cd Build
zip -r ../aws_deployment.zip *
cd ..
rm -rf Build
