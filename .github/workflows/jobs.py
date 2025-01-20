import sys
import yaml

with open (sys.argv[1], 'rt') as file: y = yaml.safe_load(file)
print(' '.join(y['jobs'].keys()))
