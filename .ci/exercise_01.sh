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

. .ci/util.sh

state="pending" # "success" "pending" "failure" "error"
description="Run the pipeline to completion using the Test AE"
context="continuous-exercise/01/run-test-ae"

post_state "$context" "$description" "$state"

# assign gpg command to variable, default to gpg2
command -v gpg2 && gpg_cmd="gpg2" || gpg_cmd="gpg"
if current_state
then
    tempdir=$(mktemp -d /tmp/tmp.XXXXXX)
    mkdir -p ${tempdir}/{db,dbs,fe,gnupg,logs,stg}
    mkdir ${tempdir}/gnupg/private-keys-v1.d
    chmod 700 ${tempdir}/gnupg ${tempdir}/gnupg/private-keys-v1.d
    GNUPGHOME=${tempdir}/gnupg ${gpg_cmd} --batch --generate-key <<EOF
     %echo Generating a basic OpenPGP key
     %no-ask-passphrase
     %no-protection
     %transient-key
     Key-Type: DSA
     Key-Length: 1024
     Subkey-Type: ELG-E
     Subkey-Length: 1024
     Name-Real: Automated Testing
     Name-Email: no-reply@dawgie.jpl.nasa,gov
     Expire-Date: 0
     # Do a commit here, so that we can later print "done" :-)
     %commit
     %echo done
EOF
    GNUPGHOME=${tempdir}/gnupg ${gpg_cmd} -armor --export no-reply@dawgie.jpl.nasa,gov > ${tempdir}/gnupg/dawgie.test.pub
    GNUPGHOME=${tempdir}/gnupg ${gpg_cmd} -armor --export-secret-key no-reply@dawgie.jpl.nasa,gov > ${tempdir}/gnupg/dawgie.test.sec
    docker run --rm -e GNUPGHOME=/proj/data/gnupg -e USER=$USER -p 8080-8089:8080-8089 -u $UID -v ${PWD}/Test:/proj/src -v ${tempdir}:/proj/data ex:${ghrVersion} dawgie.pl --context-fe-path=/proj/data/fe &
    python3 <<EOF
import json
import time
import urllib.request

isRunning = False
while not isRunning:
    time.sleep (3)
    state = json.loads (urllib.request.urlopen ('http://localhost:8080/app/state/status').read())
    isRunning = state['name'] == 'running' and state['status'] == 'active'
    pass
EOF
    declare -i jobs=1
    declare -i inc=1
    while [[ 0 -lt $jobs ]]
    do
        docker run --rm -e GNUPGHOME=/proj/data/gnupg -e USER=$USER --network host -u $UID -v ${PWD}/Test:/proj/src -v ${tempdir}:/proj/data ex:${ghrVersion} dawgie.pl.worker -a /proj/src/ae -b ae -c cluster -g /proj/data/gnupg -i $inc -n localhost -p 8081

        if [[ 4 -eq $inc ]]
        then
            target=$(curl http://localhost:8080/app/db/targets)
            target=${target:13:${#target}-15}
            echo "target: $target"
            curl -X POST -F tasks=feedback.command -F tasks=feedback.sensor -F targets=${target} http://localhost:8080/app/run
            echo ""
        fi

        inc=inc+1
        jobs=$(python3 <<EOF
import json
import time
import urllib.request

doing = json.loads (urllib.request.urlopen ('http://localhost:8080/app/schedule/doing').read())
todo = json.loads (urllib.request.urlopen ('http://localhost:8080/app/schedule/todo').read())
jobs = 0 # len (doing) + len (todo)
jobs += sum ([len (v) for v in doing.values()])
jobs += sum ([max (len (d['targets']), 1) for d in todo])
print (jobs)
EOF
            )
    done
    
    docker stop $(docker ps | grep "ex:${ghrVersion}" | awk '{print $1}')
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
