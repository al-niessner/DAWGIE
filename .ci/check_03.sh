#! /usr/bin/env bash

# COPYRIGHT:
# Copyright (c) 2015-2025, California Institute of Technology ("Caltech").
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

cidir=$(realpath $(dirname $0))
rootdir=$(realpath ${cidir}/..)
. ${rootdir}/.ci/util.sh

# https://developer.github.com/v3/repos/statuses/

state="pending" # "success" "pending" "failure" "error"
description="Use pytest to exercise code [unit testing]"
context="continuous-integration/03/pytest"

post_state "$context" "$description" "$state"

if current_state
then
    if [[ $# -gt 0 ]]
    then
        units="$@"
    else
        units=Test
    fi

    # set up postgres requirements for test 13 (at least)
    if [[ $(docker images postgres:latest | wc -l) -eq 1 ]]
    then
        echo "fetching the latest postgresql image for testing"
        docker pull postgres:latest
    fi

    if [[ $(docker network inspect ${CIT_NETWORK:-citnet} | wc -l) -eq 1 ]]
    then
        echo "create the docker network: ${CIT_NETWORK:-citnet}"
        docker network create ${CIT_NETWORK:-citnet}
    fi

    if [[ $(docker container inspect cit_postgres | wc -l) -eq 1 ]]
    then
        echo "starting a posgresql container (cit_postgres) then enabling it"
        docker run --detach --env POSTGRES_PASSWORD=password --env POSTGRES_USER=tester --name cit_postgres --network ${CIT_NETWORK:-citnet} --rm  postgres:latest
        sleep 3
        docker exec -i cit_postgres createdb -U tester testspace
    fi

    # run pytest
    docker run --rm -e PYTHONPATH=${rootdir}/Python -e USERNAME="$(whoami)" --network ${CIT_NETWORK:-citnet} -v ${rootdir}:${rootdir} -u $UID -w ${rootdir} niessner/cit:$(cit_version) python3 -m pytest --cov=dawgie --cov-branch --cov-report term-missing -v ${units} | tee unittest.rpt.txt
    [ 0 -lt `grep FAILED unittest.rpt.txt | wc -l` ]  && echo 'failure' > ${rootdir}/.ci/status.txt
    [ 0 -lt `grep "ERROR " unittest.rpt.txt | wc -l` ]  && echo 'failure' > ${rootdir}/.ci/status.txt

    # cleanup postgresql
    docker stop cit_postgres
    state=`get_state`
fi

post_state "$context" "$description" "$state"
current_state
