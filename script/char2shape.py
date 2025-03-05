import sys

if len(sys.argv) < 4:
    print('usage: num-token textfile shapefile')
    quit()

ntoken = int(sys.argv[1])
textfile = sys.argv[2]
shapefile = sys.argv[3]

n_limit = 490

with open(textfile, 'w') as tf, open(shapefile, 'w') as sf:
    for line in sys.stdin:
        try:
            key, text = line.split()
        except:
            print(line, file=sys.stderr)
            quit()
        n_char = len(list(text))

        if n_char > n_limit:
            print(f'[CAUTION]: text length {n_char} is over {n_limit}. skip {key}', file=sys.stderr)
            continue

        print(key, text, file=tf)
        print(key, ' ', n_char, f',{ntoken}', sep='', file=sf)


