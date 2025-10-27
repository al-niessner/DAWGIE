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

abort() {
    cleanup 1
}

cleanup () {
    # shut the system down and clean up
    docker compose \
           --env-file ${exdir}/.env \
           --file ${exdir}/compose.yaml \
           down
    docker image prune -f
    rm -rf ${tempdir}
    exit $1
}

make_cert () {
    # make CSR
    openssl req -newkey rsa:2048 -nodes -keyout device.key \
            -subj "/C=US/ST=CA/L=LA/O=None/CN=exercise.dawgie" -out device.csr
    # write the v3.ext file
    echo "authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = exercise.dawgie
DNS.2 = localhost
DNS.3 = server_ex" > v3.ext
    # build the certificate
    openssl x509 -req -in device.csr -signkey device.key -out device.crt \
            -sha256 -extfile v3.ext -days 36500 
    # build the complete pem and just public bit for being a guest
    cat device.key device.crt > $1
    mv device.crt $1.public
    rm device.csr device.key v3.ext
}

if [[ $# -gt 1 ]]
then
    echo "usage: $(basename $0) [post|shelve]"
    exit
fi

if [[ $# -eq 1 ]]
then
    if [[ "$1" == "shelve" ]]
    then
        EXERCISE_DB=$1
        EXERCISE_PATH=/proj/data/db
        export EXERCISE_DB EXERCISE_PATH
    else if [[ "$1" != "post" ]]
         then
             echo "usage: $(basename $0) [post|shelve]"
             exit
         fi
    fi
fi

trap abort SIGINT
exdir=$(realpath $(dirname $0))
export tempdir=$(mktemp -d /tmp/dex.XXXXXX) # will be deleted when fininshed
mkdir -p ${tempdir}/{certs,db,dbs,fe,logs,stg}
make_cert ${tempdir}/certs/guest.pem  # client should load this into browser
make_cert ${tempdir}/certs/myself.pem # allows interconnection
make_cert ${tempdir}/certs/server.pem # for https
# rename guest certificate to something dawgie will find
cp ${tempdir}/certs/guest.pem.public ${tempdir}/certs/dawgie.public.pem.guest

# make sure the user is well defined
if [ -n "${UID}" ]
then
    UID=$(id -u)
fi
export UID
   
# build and start a pipeline to exercise the code
docker compose \
       --env-file ${exdir}/.env \
       --file ${exdir}/compose.yaml \
       build
docker compose \
       --env-file ${exdir}/.env \
       --file ${exdir}/compose.yaml \
       up --detach

# While the network tree will run automatically, need to signal the feedback
# tree to run for a complete exercise routine.
#
# In a more real world situation, the user would have copied the cert used
# here into their browser and use the commanding page. However, using curl
# shows that it is possible to script it as well.
#
# Wait until there is a target other than __all__, the request feedback tree
# to begin its exercise.
target="__all__"
while [[ "$target" != "/tmp/"* ]]
do
    sleep 1
    target=$(curl --insecure -Ss 'https://localhost:8080/app/db/targets' | jq -r .[0])
done
curl -XPOST --cert ${tempdir}/certs/guest.pem --insecure "https://localhost:8085/app/run?tasks=feedback.command&targets=${target}"
echo

echo "Visit the site 'https://localhost:8080 to interact with the pipieline"
echo "Press Enter to shut the pipeline down and clean up..."
read
cleanup 0
