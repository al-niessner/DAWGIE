#! /usr/bin/env bash

# COPYRIGHT:
# Copyright (c) 2015-2024, California Institute of Technology ("Caltech").
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

make_cert () {
    # make CSR
    openssl req -days 36500 -newkey rsa:2048 -nodes -keyout device.key \
            -subj "/C=US/ST=CA/L=LA/O=None/CN=exercise.dawgie" -out device.csr
    # write the v3.ext file
    echo "authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = exercise.dawgie" > v3.ext
    # build the certificate
    openssl x509 -req -in device.csr -signkey device.key -out device.crt \
            -sha256 -extfile v3.ext -days 36500 
    # build the complete pem and just public bit for being a guest
    cat device.key device.crt > $1
    mv device.crt $1.public
    rm device.csr device.key v3.ext
}

cidir=$(realpath $(dirname $0))
rootdir=$(realpath ${cidir}/..)
. .ci/util.sh

state="pending" # "success" "pending" "failure" "error"
description="Run the pipeline to completion using the Test AE"
context="continuous-exercise/01/run-test-ae"

post_state "$context" "$description" "$state"

if current_state
then
    tempdir=$(mktemp -d /tmp/tmp.XXXXXX) # will be deleted when fininshed
    mkdir -p ${tempdir}/{certs,db,dbs,fe,logs,stg}
    make_cert ${tempdir}/certs/guest.pem  # client should load this into browser
    make_cert ${tempdir}/certs/myself.pem # allows interconnection
    make_cert ${tempdir}/certs/server.pem # for https
    # rename guest certificate to something dawgie will find
    cp ${tempdir}/certs/guest.pem.public ${tempdir}/certs/dawgie.public.pem.guest
    docker run --rm \
           -e DAWGIE_GUEST_PUBLIC_KEYS=/proj/data/certs \
           -e DAWGIE_SSL_PEM_FILE=/proj/data/certs/server.pem \
           -e DAWGIE_SSL_PEM_MYSELF=/proj/data/certs/myself.pem \
           -e USER=$USER -p 8080-8089:8080-8089 -u $UID \
           -v ${PWD}/Test:/proj/src -v ${tempdir}:/proj/data \
           ex dawgie.pl --context-fe-path=/proj/data/fe &
    python3 <<EOF
import json
import time
import urllib.request

isRunning = False
while not isRunning:
    time.sleep (3)
    state = json.loads (urllib.request.urlopen ('https://localhost:8080/app/state/status').read())
    isRunning = state['name'] == 'running' and state['status'] == 'active'
    pass
EOF
    declare -i jobs=1
    declare -i inc=1
    while [[ 0 -lt $jobs ]]
    do
        docker run --rm \
               -e DAWGIE_SSL_PEM_MYSELF=/proj/data/certs/myself.pem \
               -e USER=$USER --network host -u $UID \
               -v ${PWD}/Test:/proj/src -v ${tempdir}:/proj/data \
               ex dawgie.pl.worker \
                  -a /proj/src/ae -b ae -c cluster -i $inc -n localhost -p 8081

        if [[ 4 -eq $inc ]]
        then
            target=$(curl https://localhost:8080/app/db/targets)
            target=${target:13:${#target}-15}
            echo "target: $target"
            curl -X POST -F tasks=feedback.command -F tasks=feedback.sensor -F targets=${target} https://localhost:8080/app/run
            echo ""
        fi

        inc=inc+1
        jobs=$(python3 <<EOF
import json
import time
import urllib.request

doing = json.loads (urllib.request.urlopen ('https://localhost:8080/app/schedule/doing').read())
todo = json.loads (urllib.request.urlopen ('https://localhost:8080/app/schedule/todo').read())
jobs = 0 # len (doing) + len (todo)
jobs += sum ([len (v) for v in doing.values()])
jobs += sum ([max (len (d['targets']), 1) for d in todo])
print (jobs)
EOF
            )
    done
    
    docker stop $(docker ps | grep "ex" | awk '{print $1}')
    python3 <<EOF
import os

tempdir="${tempdir}"
v = []
with open (os.path.join (tempdir,'logs/dawgie.log'), 'rt') as f:
    for line in f.readlines():
        if 0 < line.find ('reaction'):
            v.append (float (line.split()[-1]))
            pass
        pass
    pass

if v and not all ([9.9 < x < 10.1 for x in v[-3:]]):
    print ('failed to converge correctly to 10', v)
    print ('   incarnations:',  $inc)
    with open ('.ci/status.txt', 'tw') as f: f.write ('failure')
    pass
EOF
    rm -r ${tempdir}
    state=`get_state`
fi

post_state "$context" "$description" "$state"
