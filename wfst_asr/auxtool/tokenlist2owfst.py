import sys

n_node = 2
for line in sys.stdin:
    line = line.strip()
    print(f'0\t{n_node}\t<eps>\t<eps>')    
    for c in list(line):
        print(f'{n_node}\t{n_node+1}\t{c}\t{c}')
        n_node += 1
    print(f'{n_node}\t1\t<eps>\t<eps>')
    n_node += 1
print('1')
