import sys
import re
import argparse

# argument analysis
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--use_pron', action='store_true')
parser.add_argument('--use_char', action='store_true')
parser.add_argument('--delimiter', type=str, default='+')
args = parser.parse_args()

#
use_pron = args.use_pron
use_char = args.use_char
delimiter = args.delimiter

#
for line in sys.stdin:
    line = line.strip()

    line = line.replace('<s>', '<sos/eos>')
    line = line.replace('</s>', '<sos/eos>')
    tokens = line.split()    

    # 
    if len(tokens) >= 4:
        if re.match(r'\[.*any.*\]', tokens[2]):
            pass
        elif re.match(r'\[.*\]', tokens[2]):
            tokens[2] = '<eps>'
        if re.match(r'#[0-9]+', tokens[2]):
            tokens[2] = '<eps>'

        if re.match(r'(\[.*\]|<eps>|<sos/eos>)', tokens[3]) is None:
            if use_char is True:
                entries = tokens[3].split(delimiter)
                tokens[3] = entries[0]
            if use_pron is True:
                entries = tokens[3].split(delimiter)
                tokens[3] = entries[1]

        print('\t'.join(tokens))
    else:
        print(line)
