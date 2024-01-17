#!/bin/bash

# COPYRIGHT:
# Copyright (c) 2015-2024, California Institute of Technology ("Caltech").
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

if [ $# -lt 1 ]
then
  echo "Usage: $0 <start|stop|reset|restart>"
  exit 1
fi

masterdir="/proj/sdp/ops/test"
lockfile="$masterdir/.pre_ops.lock"
export PYTHONPATH="$masterdir/Python:$PYTHONPATH"

case "$1" in
  start)
    echo "start"
    if [ ! -f $lockfile ]
    then
      $masterdir/Python/dawgie/pl/start.py --port=9090 --context-db-path=/proj/sdp/data/sandboxdb --context-db-port=9999 --context-data-log=/proj/sdp/logs/ --log-file=pre_ops.log --context-log-port=9021 &
      pid=$!
      echo $pid > $lockfile
    else
      echo "sdp pre_ops process is already running."
    fi
    ;;
  stop)
    echo "stop"
    if [ -f $lockfile ]
    then
      pid=`head -n 1 $lockfile`
      kill -9 $pid
      ps -ef | grep $pid | grep -v grep
      if [ $? -eq 0 ]
      then
        kill -9 $pid
        sleep 3
      fi
      ps -ef | grep $pid | grep -v grep
      if [ $? -eq 0 ]
      then
        echo "Failed to kill sdp pre_ops process $pid"
        exit 1
      fi
      rm $lockfile
    fi
    ;;
  reset|restart)
    echo "reset"
    $0 stop
    sleep 3
    $0 start
    ;;
  *)
    echo "Unknown command"
    exit 1
    ;;
esac

exit 0
