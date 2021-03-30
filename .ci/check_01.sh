#! /usr/bin/env bash

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

. .ci/util.sh

# https://developer.github.com/v3/repos/statuses/

state="pending" # "success" "pending" "failure" "error"
description="Check that the code follows PEP-8 standards [coding standard compliance]"
context="continuous-integration/01/pep8"

post_state "$context" "$description" "$state"

if current_state
then
    docker run --rm -v $PWD:$PWD -u $UID -w $PWD cit:$(cit_version) pycodestyle \
           --ignore=E24,E121,E123,E124,E126,E127,E211,E225,E226,E231,E252,E301,E302,E305,E402,E501,W504,E701,E702,E704,E722,E741 \
           --exclude=binding.py \
           --statistics Python Test | tee pep8.rpt.txt
    errs=`wc -l pep8.rpt.txt | awk '{print $1}'`
    [ $errs -ne 0 ] && echo -n "failure" > .ci/status.txt
    state=`get_state`
fi

post_state "$context" "$description" "$state"
