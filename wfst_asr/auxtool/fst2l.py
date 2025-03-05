import sys
import re
import argparse

# argument analysis
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('isym', type=str)
parser.add_argument('--use_pron', action='store_true')
parser.add_argument('--delimiter', type=str, default='+')
args = parser.parse_args()

#
use_pron = args.use_pron
delimiter = args.delimiter
isym = args.isym

# read input symbols
isymbols = set()
for line in sys.stdin:
    line = line.strip()
    tokens = line.split()
    
    if len(tokens) >= 3:
        isymbols.add(tokens[2])

# judge duplication
existence = set()
extra_id = 1

# gen lexicon fst
token_list = set()
n_node = 2
for x in isymbols:
    if x == '<s>' or x == '</s>' or x == '<sp>':
        token_list.add(x)
        print(f'0\t1\t{x}\t{x}')
        continue
    if re.match(r'\[.*\]', x):
        token_list.add(x)
        print(f'0\t1\t{x}\t{x}')
        continue
    if re.match(r'@.*', x):
        token_list.add(x)
        print(f'0\t1\t{x}\t{x}')
        continue
    if x == '<eps>':
        continue

    tokens = x.split(delimiter)
    if len(tokens) >= 2:
        if use_pron is True:
            tgt = tokens[1]
        else:
            tgt = tokens[0]
    else:
        tgt = x
        
    print(f'0\t{n_node}\t<eps>\t<eps>')
    for c in list(tgt):
        token_list.add(c)
        print(f'{n_node}\t{n_node+1}\t{c}\t<eps>')
        n_node += 1

    if tgt in existence:
        print(f'{n_node}\t{n_node+1}\t#{extra_id}\t<eps>')
        token_list.add(f'#{extra_id}')
        n_node += 1
        extra_id += 1
    else:
        existence.add(tgt)
        
    print(f'{n_node}\t1\t<eps>\t{x}')
    n_node += 1

    
print('1\t0\t<eps>\t<eps>')
print('1')

###
with open(isym, "w") as f:
    print('<eps> 0', file=f)
    n_sym = 1
    for x in sorted(token_list):
        print(f'{x} {n_sym}', file=f)
        n_sym += 1
