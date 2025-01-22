import os
import sys
import yaml

with open (sys.argv[1], 'rt') as file: y = yaml.safe_load(file)
lc = 0
steps = []
if sys.argv[2] == 'PyTesting':
    print ('docker pull postgres:latest')
    print ('docker run --detach --env POSTGRES_PASSWORD=password '
           '--env POSTGRES_USER=tester --name ga_postgres --network host '
           '--rm  postgres:latest')
    print ('sleep 3')
    print ('docker exec -i ga_postgres createdb -U tester testspace')
for step in y['jobs'][sys.argv[2]]['steps']:
    if 'run' in step:
        for line in filter (len, step['run'].split('\n')):
            if line.startswith ('sudo'): continue
            if line.startswith ('createdb'): continue
            if '&&' in line: line = line[:line.find('&&')]
            if '||' in line: line = line[:line.find('||')]
            cmd = line.split()[0]
            lc += 1
            if cmd == 'black' and 'KEEP_STYLE' in os.environ:
                line = line.replace ('--check ','')
            print (line,f'&& echo "result of github action step: success,{cmd}" '
                   f'|| echo "result of github action step: failure,{cmd}"')
if lc: print (f'echo "github actions expected steps: {lc}"')
if sys.argv[2] == 'PyTesting':
    print ('docker stop ga_postgres')
