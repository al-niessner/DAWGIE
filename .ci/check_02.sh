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
description="Use pylint to verify code quality [static analysis]"
context="continuous-integration/02/pylint"

post_state "$context" "$description" "$state"

if current_state
then
    docker run --rm -v ${rootdir}:${rootdir} -u $UID -w ${rootdir} niessner/cit:$(cit_version) pylint --rcfile=${rootdir}/.ci/pylint.rc Python/dawgie Test/ae | tee pylint.rpt.txt
    python3 <<EOF
mn = '<unknown>'
count = 0
rated = False
with open ('pylint.rpt.txt', 'rt') as f:
    for l in f.readlines():
        rated |= 0 < l.find ('code has been rated at')

        if l.startswith ('***'): mn = l.split()[2]
        if len (l) < 2: continue
        if 0 < l.find ('(missing-docstring)'): continue
        if 0 < l.find ('(missing-class-docstring)'): continue
        if 0 < l.find ('(missing-function-docstring)'): continue
        if 0 < l.find ('(locally-disabled)'): continue
        if 0 < l.find ('Similar lines in'): continue  # FIXME: remove when ready to fix duplicates
        if l.count(':') <  4: continue

        count += 1
        print (count, mn, l.strip())
        pass
    pass

if 0 < count or not rated:
    print ('pylint check failed', count)
    with open ('${rootdir}/.ci/status.txt', 'tw') as f: f.write ('failure')
EOF
    state=`get_state`
fi

post_state "$context" "$description" "$state"
