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
. .ci/util.sh
$(dirname $0)/step_00.sh

state="pending" # "success" "pending" "failure" "error"
description="Build an environment for CI"
context="continuous-integration/00/environment"

post_state "$context" "$description" "$state"

if current_state
then
    cv="$(git rev-parse HEAD)"
    lv="$(layer_versions)"
    pyVersion="${lv:17:16}"
    tag=${1:-latest}
    filename=.ci/Dockerfile.ap
    python3 <<EOF
with open ("${filename}", 'rt') as f: text = f.read()
with open (".ci/Dockerfile.3", 'tw') as f: f.write (text.replace ("pyVersion", "${pyVersion}").replace ("cvVersion","${cv}"))
EOF
    filename=.ci/Dockerfile.ex
    python3 <<EOF
with open ("${filename}", 'rt') as f: text = f.read()
with open (".ci/Dockerfile.4", 'tw') as f: f.write (text.replace ("apVersion", "${tag}").replace ('##DAWGIE_DOCKERIZED_AE_GIT_REVISION##',"$cv}"))
EOF

    python3 <<EOF
with open ('Python/setup.py', 'rt') as f: text = f.read()
with open ('Python/setup.py', 'tw') as f:
    f.write (text.replace ("pyVersion", "${pyVersion}"))
EOF

    docker build --network=host -t ap:${tag} - < .ci/Dockerfile.3

    docker build --network=host -t ex:latest - < .ci/Dockerfile.4
    rm -rf .ci/Dockerfile.[1-4]
    state=`get_state`
fi

post_state "$context" "$description" "$state"
