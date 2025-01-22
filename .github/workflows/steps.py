import sys
import yaml

with open (sys.argv[1], 'rt') as file: y = yaml.safe_load(file)
lc = 0
steps = []
for step in y['jobs'][sys.argv[2]]['steps']:
    if 'run' in step:
        for line in filter (len, step['run'].split('\n')):
            if line.startswith ('sudo'): continue
            if '&&' in line: line = line[:line.find('&&')]
            if '||' in line: line = line[:line.find('||')]
            cmd = line.split()[0]
            lc += 1
            print (line,f'&& echo "result of github action step: success,{cmd}" '
                   f'|| echo "result of github action step: failure,{cmd}"')
if lc: print (f'echo "github actions expected steps: {lc}"')
