#! /usr/bin/env bash

# COPYRIGHT:
# Copyright (c) 2015-2026, California Institute of Technology ("Caltech").
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

make_ca() {
    openssl req -x509 -new -nodes -newkey rsa:4096 -keyout ${1}.key -out ${1}.crt -days 7 \
            -subj "/CN=Exercise User CA" \
            -addext "basicConstraints=critical,CA:TRUE,pathlen:0" \
            -addext "keyUsage=critical,keyCertSign,cRLSign" \
            -addext "extendedKeyUsage=clientAuth" \
            -addext "nameConstraints=critical,permitted;URI:exercise.local"
}

make_cert () {
    openssl req -new -nodes -newkey rsa:2048 \
            -keyout ${1}.key -out ${1}.csr \
            -subj "/CN=$(id -un)"
    sign ${1}.csr ${tempdir}/certs/signed.public.pem.$(basename $1)
    cat ${1}.key ${tempdir}/certs/signed.public.pem.$(basename $1) > ${1}.ca.signed.pem
    chmod 600 ${1}.ca.signed.pem
}

sign () {
    CALLER=$USER
    EXT=$(mktemp)
    trap 'rm -f "${EXT}"' EXIT

    cat > "${EXT}" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=clientAuth
subjectAltName=URI:https://exercise.local/user/${CALLER}
EOF

    CA_CRT=${tempdir}/certs/ex-ca.crt
    CA_KEY=${tempdir}/certs/ex-ca.key
    openssl x509 -req -in "${1}" \
            -CA "${CA_CRT}" -CAkey "${CA_KEY}" -CAcreateserial \
            -out "${2}" -sha256 -extfile "${EXT}" -days 7
}

selfsign() {
    EXT=$(mktemp)
    cat > "${EXT}" <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=clientAuth,serverAuth
EOF
    openssl x509 -req -in ${1}.csr -signkey ${1}.key -days 7 \
            -out ${1}.crt -extfile "${EXT}"
    rm -f "${EXT}"
    cat ${1}.key ${1}.crt > ${1}.self.signed.pem
    chmod 600 ${1}.self.signed.pem
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
        EXERCISE_HOST=dex_pipeline
        EXERCISE_PATH=/proj/data/db
        EXERCISE_PORT=8083
        export EXERCISE_DB EXERCISE_HOST EXERCISE_PATH EXERCISE_PORT
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
make_ca ${tempdir}/certs/ex-ca
make_cert ${tempdir}/certs/guest  # client should load this into browser
make_cert ${tempdir}/certs/myself # allows interconnection
selfsign ${tempdir}/certs/myself
# server needs to be a self signed cert
# normally, this would be a cert provided by the company that fully validates
openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
  -keyout ${tempdir}/certs/server.key -out ${tempdir}/certs/server.crt \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,DNS:*.local"
cat ${tempdir}/certs/server.key ${tempdir}/certs/server.crt > ${tempdir}/certs/server.pem

# make sure the user is well defined
if [ -z "${UID}" ]
then
    UID=$(id -u)
fi
export UID

if [ -z "${EXERCISE_MODE}" ]
then
    EXERCISE_MODE=stable
fi
export EXERCISE_MODE

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
echo
target="__all__"
while [[ "$target" != "/tmp/"* ]]
do
    sleep 1
    obj=$(curl --insecure -Ss 'https://localhost:8080/app/db/targets')
    target=$(echo $obj | jq -r .[0])
    if [[ "$target" == "__all__" ]]
    then
        target=$(echo $obj | jq -r .[1])
    fi
done
echo "Requesting feeback on ${target}"
curl -XPOST --cert ${tempdir}/certs/guest.pem --insecure "https://localhost:8085/app/run?tasks=feedback.command&targets=${target}"
echo

echo
echo "Visit the site 'https://localhost:8080 to interact with the pipieline"
echo "Press Enter to shut the pipeline down and clean up..."
read
cleanup 0
