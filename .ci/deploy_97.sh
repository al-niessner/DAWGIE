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
description="if everything is good deliver the docker images to artifactory"
context="continuous-deploy/97/docker-send"

post_state "$context" "$description" "$state"

if current_state
then
    port=$(which_port)
    echo "docker port: $port"
    # login to artifactory
    docker login -p ${BOT_APIKEY} -u ${BOT_NAME} cae-artifactory.jpl.nasa.gov:${port}
    # tag all of the dawgie layers
    docker tag os:${ghrVersion} cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/os:${ghrVersion}
    docker tag py:${ghrVersion} cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/py:${ghrVersion}
    docker tag ap:${ghrVersion} cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/ap:${ghrVersion}
    docker tag test:${ghrVersion} cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/test:${ghrVersion}
    # push all of the layers to artifactory
    docker push cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/os:${ghrVersion}
    docker push cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/py:${ghrVersion}
    docker push cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/ap:${ghrVersion}
    docker push cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/test:${ghrVersion}
    # logout of artifactory
    docker logout cae-artifactory.jpl.nasa.gov:${port}
    # remove all of the tags pointing to artifactory
    docker rmi cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/os:${ghrVersion}
    docker rmi cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/py:${ghrVersion}
    docker rmi cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/ap:${ghrVersion}
    docker rmi cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/test:${ghrVersion}
    sendmail -f no-reply@dawgie.jpl.nasa.gov sdp@jpl.nasa.gov <<EOF
Subject: dawgie release

Deployed newest version of dawgie to cae-artifactory.jpl.nasa.gov:${port}/gov/nasa/jpl/dawgie/ap:${ghrVersion}
EOF
    state=`get_state`
else
    sendmail -f no-reply@dawgie.jpl.nasa.gov sdp@jpl.nasa.gov <<EOF
Subject: dawgie release

Did not deploy verion ${ghrVersion}. For details, see:
${BUILD_URL}
EOF
fi

post_state "$context" "$description" "$state"
