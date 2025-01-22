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

within()
{
    [[ $# -eq 1 ]] && return 0
    base=$1
    shift
    while [[ $# -gt 0 ]]
    do
        [[ "$base" = "$1" ]] && return 0
        shift
    done
    return 1
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
expected_jobs=""
root=$(realpath $(dirname $0)/../..)
this=$(realpath $(dirname $0))
wdir=$this/local
cd $root
rm -f $root/*.rpt.txt
trap "rm -rf $wdir $root/Python/build $root/Python/dawgie.egg-info $root/Python/dawgie/fe/requirements.txt" EXIT
for yaml in $(ls $this/*.yaml)
do
    echo "yaml: $yaml"
    for job in $(python $this/jobs.py $yaml)
    do
        if $(within $job $*)
        then
            echo "   queuing job: $job"
            expected_jobs="${expected_jobs} $job"
            mkdir -p $wdir/$job
            do_job $yaml $job $wdir/$job > $root/$job.rpt.txt 2>&1 &
        else
            echo "   skipping $job"
        fi
    done
done
echo "waiting for jobs to complete"
wait
rm -rf $wdir $root/Python/build $root/Python/dawgie.egg-info $root/Python/dawgie/fe/requirements.txt
declare -i summary=0
for job in $expected_jobs
do
    if [ -f $root/$job.rpt.txt ]
    then
        python <<EOF
import os,sys
def extract (frm:str, stmnt:str)->[str]:
    result = []
    idx = frm.find(stmnt)
    while idx >= 0:
       result.append (frm[idx+len(stmnt):frm.find('\n',idx)].strip())
       idx = frm.find(stmnt, idx+len(stmnt))
    return result
with open ("$root/$job.rpt.txt", 'rt') as file: content = file.read()
count = int(extract (frm=content,
                     stmnt='github actions expected steps: ')[0])
results = extract (frm=content,
                   stmnt='result of github action step: ')
summary = False
if len(results) != count:
    print ('Failure: $job did not produce all of the exptected messages. See $root/$job.rpt.txt for details.')
else:
    summary = all(r.startswith('success') for r in results) 
    if summary: print ('Success: $job')
    else: print ('Failure: $job - see $root/$job.rpt.txt for details')
for result in results:
    state,cmd = result.split(',')
    print (' ', state+':', cmd)
if summary:
    if 'KEEP_REPORTS' not in os.environ: os.unlink("$root/$job.rpt.txt")
    sys.exit(0)
else: sys.exit(1)
EOF
        summary=$summary+$?
    else
        echo "Failure: $job did not create expected report."
        summary=1
    fi
done
[[ $summary -eq 0 ]] && echo "Summary: All test verifications were successful" || echo "Summary: Some or all test verifications failed." 
trap - EXIT
