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

cidir=$(realpath $(dirname $0))
rootdir=$(realpath ${cidir}/..)
. ${rootdir}/.ci/util.sh

# https://developer.github.com/v3/repos/statuses/

state="pending" # "success" "pending" "failure" "error"
description="Build an environment for CI"
context="continuous-integration/00/environment"

post_state "$context" "$description" "$state"

if current_state
then
    lv="$(layer_versions)"
    osVersion="${lv:0:16}"
    pyVersion="${lv:17:16}"
    citVersion="${lv:34:16}"
    echo "OS Version: $osVersion"
    echo "PY Version: $pyVersion"
    echo "CIT Version: $citVersion"

    if [ -z "$(docker images | grep cit | grep ${citVersion})" ]
    then
       docker pull niessner/cit:${citVersion}

       if [ -z "$(docker images niessner/cit | grep ${citVersion})" ]
       then
           echo "building CIT because $(docker images niessner/cit | grep ${citVersion})"

           if [ -z "$(docker images | awk '{print $1":"$2}' | grep os:$osVersion)" ]
           then
               echo "   Building OS layer $osVersion"
               docker build --network=host -t os:${osVersion} - < ${rootdir}/.ci/Dockerfile.1
           fi

           if [ -z "$(docker images | awk '{print $1":"$2}' | grep py:$pyVersion)" ]
           then
               echo "   Building Python layer $pyVersion"
               docker build --network=host -t py:${pyVersion} - < ${rootdir}/.ci/Dockerfile.2
           fi

           if [ -z "$(docker images | awk '{print $1":"$2}' | grep cit:$citVersion)" ]
           then
               echo "   Building CI Tools layer $citVersion"
               docker build --network=host -t niessner/cit:${citVersion} - < ${rootdir}/.ci/Dockerfile.3
               docker login -p ${DOCKER_LOGIN_PASSWORD} -u ${DOCKER_LOGIN_ID}
               docker push niessner/cit:${citVersion}
               docker logout
           fi

           rm ${rootdir}/.ci/Dockerfile.1 ${rootdir}/.ci/Dockerfile.2 ${rootdir}/.ci/Dockerfile.3
       fi
    fi
    state=`get_state`
fi

post_state "$context" "$description" "$state"
