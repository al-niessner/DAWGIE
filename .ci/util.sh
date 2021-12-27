
# COPYRIGHT:
# Copyright (c) 2015-2021, California Institute of Technology ("Caltech").
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

GHE_API_URL=https://api.github.com
ghrVersion=${ghrVersion:-"`git describe --tags`"}
PYTHONPATH=${PWD}/Python:${PWD}/Test
REPO=al-niessner/DAWGIE

export GHE_API_URL PATH PYTHONPATH

cit_version ()
{
    lv="$(layer_versions)"
    rm .ci/Dockerfile.1 .ci/Dockerfile.2 .ci/Dockerfile.3
    echo "${lv:34:16}"
}

current_state ()
{
    test `cat .ci/status.txt` == "success" 
}

download ()
{
    curl -L \
         -H "Authorization: token ${GHE_TOKEN}" \
         ${ghrReleaseTarball} > $1
}

get_state ()
{
    cat .ci/status.txt
}

layer_versions ()
{
    python3 <<EOF
with open ('.ci/Dockerfile.os', 'rt') as f: text = f.read()
with open ('.ci/Dockerfile.1', 'tw') as f: f.write (text.replace ("ghrVersion", "${ghrVersion}"))
EOF
    osVersion=$(python3 <<EOF

try:
    import pyblake2 as hashlib
except:
    import hashlib

with open ('.ci/Dockerfile.1', 'br') as f: data = f.read()
k = hashlib.blake2b (data, digest_size=8)
print (k.hexdigest())
EOF
           )
    python3 <<EOF
with open ('.ci/Dockerfile.py', 'rt') as f: text = f.read()
with open ('.ci/Dockerfile.2', 'tw') as f: f.write (text.replace ("ghrVersion", "${osVersion}"))
EOF
    pyVersion=$(python3 <<EOF
try:
    import pyblake2 as hashlib
except:
    import hashlib

with open ('.ci/Dockerfile.2', 'br') as f: data = f.read()
k = hashlib.blake2b (data, digest_size=8)
print (k.hexdigest())
EOF
           )
    python3 <<EOF
with open ('.ci/Dockerfile.cit', 'rt') as f: text = f.read()
with open ('.ci/Dockerfile.3', 'tw') as f: f.write (text.replace ("ghrVersion", "${pyVersion}"))
EOF
    citVersion=$(python3 <<EOF
try:
    import pyblake2 as hashlib
except:
    import hashlib

with open ('.ci/Dockerfile.3', 'br') as f: data = f.read()
k = hashlib.blake2b (data, digest_size=8)
print (k.hexdigest())
EOF
           )
    echo $osVersion $pyVersion $citVersion
}

post_state ()
{
    if current_state && [ "$3" == "pending" ]
    then
        echo "$1 -- $2"
    else
        echo "$1 -- completion state: $3"
    fi

    curl -XPOST \
         -H "Authorization: token ${GHE_TOKEN}" \
         ${GHE_API_URL}/repos/${REPO}/statuses/${CIRCLE_SHA1} \
         -d "{\"state\": \"${3}\", \"target_url\": \"${CIRCLE_BUILD_URL}\", \"description\": \"${2}\", \"context\": \"${1}\"}"  > /dev/null 2>&1
    exit $(check_state)
}

which_port ()
{
    python3 <<EOF
v = "${ghrVersion}".split ('.')

if len (v) == 3:
    if v[0].isdigit() and v[1].isdigit() and v[2].isdigit(): port = 16003
    elif v[0].isdigit() and v[1].isdigit() and 0 < v[2].find ('-rc') and v[2].split('-')[0].isdigit(): port = 16002
    else: port = 16001
else: port = 16001

print (port)
EOF
}
