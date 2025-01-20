#! /usr/bin/env bash
#
# Script runs the work flow locally. This is not a general script that runs any
# workflow like act. It is clearning and build to process these workflows since
# they are all all Ubuntu based and require a virtual Python 3.12 environment.

do_job()
{
    python -m venv $3/venv
    . $3/venv/bin/activate
    python -m pip install pyyaml
    python $this/steps.py $1 $2 > $3/do.sh
    chmod 755 $3/do.sh
    $3/do.sh
}

if [ -z "$(which python)" ]
then
    echo "'python' is not defined in your path. It should execute Python 3.12 or later."
    exit -1
fi
python <<EOF
import sys
if sys.version_info.major >= 3 and sys.version_info.minor >= 12:
    sys.exit(0)
else: sys.exit(-2)
EOF
if [ $? -ne 0 ]
then
    echo "'python' is an older version. Need to use python 3.12 or later"
    python --version
    exit -2
fi
root=$(realpath $(dirname $0)/../..)
this=$(realpath $(dirname $0))
wdir=$this/local
cd $root
trap "rm -rf $wdir" EXIT
for yaml in $(ls $this/s*.yaml)
do
    echo "yaml: $yaml"
    for job in $(python $this/jobs.py $yaml)
    do
        echo "   queuing job: $job"
        mkdir -p $wdir/$job
        do_job $yaml $job $wdir/$job > $root/$job.rpt.txt 2>&1 &
    done
done
echo "waiting for jobs to end"
wait
rm -rf $wdir
trap - EXIT
