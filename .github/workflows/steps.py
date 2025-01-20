import sys
import yaml

with open (sys.argv[1], 'rt') as file: y = yaml.safe_load(file)
steps = []
for step in y['jobs'][sys.argv[2]]['steps']:
    if 'run' in step: print (step['run'])
