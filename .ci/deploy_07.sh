#! /usr/bin/env bash

# COPYRIGHT:
# Copyright (c) 2015-2019, California Institute of Technology ("Caltech").
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

# https://developer.github.com/v3/repos/statuses/

state="pending" # "success" "pending" "failure" "error"
description="build and deploy dawgie-test image"
context="continuous-deploy/07/docker-build-test"

post_state "$context" "$description" "$state"

if current_state
then
    DOCKER_GIT_REVISION=`git rev-parse HEAD`
    python3 <<EOF
with open ('.ci/Dockerfile.test', 'rt') as f: txt = f.read()
with open ('.ci/Dockerfile.5', 'tw') as f: f.write (txt.replace ('FROM dawgie', 'FROM ap:${ghrVersion}').replace ('##DOCKER_GIT_REVISION##', '$DOCKER_GIT_REVISION'))
EOF
    .ci/dcp.py --server .ci/Dockerfile.5 &
    while [ ! -f .ci/Dockerfile.5.dcp ]
    do
        sleep 3
    done
    docker build --network=host -t test:${ghrVersion} - < .ci/Dockerfile.5.dcp
    state=`get_state`
fi

post_state "$context" "$description" "$state"
