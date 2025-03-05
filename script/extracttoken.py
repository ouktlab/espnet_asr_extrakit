import sys
import yaml

if len(sys.argv) < 2:
    print('usage: conf')
    quti()


with open(sys.argv[1], 'r') as file:
    config = yaml.safe_load(file)

for x in config['token_list']:
    print(x)
