import sys
import re

### remove special characters
rmpat = re.compile(r'[…、。？！\?!,\.;:]')

###
for line in sys.stdin:
    line = line.strip()
    key, text = line.split(maxsplit=1)
    text = rmpat.sub('', text)
    print(' '.join(list(text.strip())), '\t(', key, ')', sep='')
    
