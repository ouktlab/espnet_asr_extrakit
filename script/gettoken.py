import sys

tokenlist = set()
for line in sys.stdin:
    key, text = line.strip().split(maxsplit=1)
    
    for c in list(text):
        tokenlist.add(c)

print('<blank>\n<unk>')
for x in sorted(tokenlist):
    print(x)
print('<sos/eos>')
