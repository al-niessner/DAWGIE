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

srcdir=$(realpath $(dirname $0))
rootdir=$(realpath ${srcdir}/../..)
. ${rootdir}/.ci/util.sh

# while in development, this should be here
#${rootdir}/.ci/step_00.sh
#${rootdir}/.ci/check_01.sh
#${rootdir}/.ci/check_02.sh
#${rootdir}/.ci/check_03.sh
#${rootdir}/.ci/check_04.sh
#${rootdir}/.ci/check_05.sh
# then it can be removed when complete and stable as check_06.sh is moved to CI

state="pending" # "success" "pending" "failure" "error"
description="FSM Test: check the FSM transitions with a simple AE"
context="continuous-integration/06/fsm-transitions"

post_state "$context" "$description" "$state"

wait_for_running()
{
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
}

wait_for_idle()
{
    python3 <<EOF
import json
import time
import urllib.request

isIdle = False
while not isIdle:
    time.sleep (3)
    crew = json.loads (urllib.request.urlopen ('http://localhost:8080/app/schedule/crew').read())
    doing = json.loads (urllib.request.urlopen ('http://localhost:8080/app/schedule/doing').read())
    todo = json.loads (urllib.request.urlopen ('http://localhost:8080/app/schedule/todo').read())
    isIdle = all([len (crew['busy']) == 0, int(crew['idle']) == 0,
                  len (doing) == 0, len (todo) == 0])
    pass
EOF
    wait_for_running
}

if current_state
then
    echo "building the pipeline foreman and workers"
    lv="$(layer_versions)"
    pyVersion="${lv:17:16}"
    cd ${rootdir}
    python3 <<EOF
with open ('${rootdir}/.ci/Dockerfile.dit', 'rt') as f: text = f.read()
with open ('${rootdir}/.ci/Dockerfile.4', 'tw') as f: f.write (text.replace ("ghrVersion", "${pyVersion}"))
EOF
    docker build --network=host -f .ci/Dockerfile.4 -t dit:latest .
    rm -f ${rootdir}/.ci/Dockerfile.[1-4]

    command -v gpg2 && gpg_cmd="gpg2" || gpg_cmd="gpg"
    plname=$(mktemp -u dit_XXXXX)
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
    docker run --detach --rm \
           -e GNUPGHOME=/proj/data/gnupg \
           -e USER=$USER \
           --name ${plname} \
           -p 8080-8089:8080-8089 \
           -u $UID \
           -v ${rootdir}:/proj/src \
           -v ${tempdir}:/proj/data \
           dit dawgie.pl -L logging.INFO --context-fe-path=/proj/data/fe
    wait_for_running
    docker run --rm \
           -e GNUPGHOME=/proj/data/gnupg \
           -e USER=$USER \
           --name worker_0 \
           --network host \
           -u $UID \
           -v ${rootdir}:/proj/src \
           -v ${tempdir}:/proj/data \
           dit dawgie.pl.worker -a /proj/src/Test/Integration/ae \
                                -b ae -c cluster -g /proj/data/gnupg -i 0 \
                                -n localhost -p 8081
    wait_for_running
    for iter in 1 2 3
    do
        docker run --detach --rm \
               -e GNUPGHOME=/proj/data/gnupg \
               -e USER=$USER \
               --name worker_$iter \
               --network host \
               -u $UID \
               -v ${rootdir}:/proj/src \
               -v ${tempdir}:/proj/data \
               dit dawgie.pl.worker -a /proj/src/Test/Integration/ae -b ae \
                                    -c cluster -g /proj/data/gnupg -i $iter \
                                    -n localhost -p 8081
    done
    curl -X POST 'http://localhost:8080/app/run?targets=__all__&tasks=prime.engine&tasks=second.engine&tasks=third.engine'
    wait_for_idle
    wait_for_running
    ## check logs for archiving
    docker stop ${plname}
    rm -r ${tempdir}
    state=`get_state`
fi

post_state "$context" "$description" "$state"
