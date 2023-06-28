#! /usr/bin/env bash

# COPYRIGHT:
# Copyright (c) 2015-2023, California Institute of Technology ("Caltech").
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

if [[ $# -ne 1 ]]
then
    echo "usage: $0 <version>"
    echo "   where <version> is the release number to get from github.com"
    exit
fi

# sudo pip3 install -U twine wheel setuptools
# . ${HOME}/.venv/dawgie/bin/activate
export DAWGIE_VERSION=$1
bdir=$(pwd)
wdir=$(mktemp -d)
echo "tempdir: ${wdir}"
cd $wdir
wget https://github.com/al-niessner/DAWGIE/archive/${1}.tar.gz
tar  --strip-components=1 -xzf ${1}.tar.gz
cd Python
cp ../README.md README.md
cat ../COPYRIGHT.txt > LICENSE
echo "" >> LICENSE
echo "" >> LICENSE
cat ../LICENSE.txt >> LICENSE
python3 setup.py sdist bdist_wheel
twine check dist/*
twine upload --verbose dist/*
cd ${bdir}
rm -rf ${wdir}
