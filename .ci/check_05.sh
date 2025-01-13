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

state="pending" # "success" "pending" "failure" "error"
description="Verify Test AE content: check the test AEs that they meet expectations"
context="continuous-integration/05/compliant"

post_state "$context" "$description" "$state"

if current_state
then
    docker run --rm -e PYTHONPATH=${rootdir}/Python -e USERNAME="$(whoami)" -v ${rootdir}:${rootdir} -u $UID -w ${rootdir} -t niessner/cit:$(cit_version) python3 -m dawgie.tools.compliant --ae-dir=${rootdir}/Test/ae --ae-pkg=ae --verbose | tee compliant.rpt.txt
    [[ $? -eq 0 ]] && ret_ae=passed || ret_ae=failed
    docker run --rm -e PYTHONPATH=${rootdir}/Python -e USERNAME="$(whoami)" -v ${rootdir}:${rootdir} -u $UID -w ${rootdir} -t niessner/cit:$(cit_version) python3 -m dawgie.tools.compliant --ae-dir=${rootdir}/Test/bae --ae-pkg=bae --verbose | tee -a compliant.rpt.txt
    [[ $? -ne 0 ]] && ret_bae=passed || ret_bae=failed
    docker run --rm -e PYTHONPATH=${rootdir}/Python -e USERNAME="$(whoami)" -v ${rootdir}:${rootdir} -u $UID -w ${rootdir} -t niessner/cit:$(cit_version) python3 -m dawgie.tools.compliant --ae-dir=${rootdir}/Test/Integration/ae --ae-pkg=ae --verbose | tee -a compliant.rpt.txt
    [[ $? -eq 0 ]] && ret_iae=passed || ret_iae=failed

    if [[ $ret_ae == "passed" ]] && [[ $ret_bae == "passed" ]] && [[ $ret_iae == "passed" ]]
    then
        echo "all passed"
    fi

    state=`get_state`
fi

post_state "$context" "$description" "$state"
current_state
