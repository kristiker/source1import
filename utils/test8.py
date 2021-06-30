from pathlib import Path

collected = {}
def collect_dev(k, v):
    
    v_evauluated = eval(repr(v))
    v_type = type(v_evauluated)

    c = collected.setdefault(k, ([], []))
    if v_type not in c[0]:
        c[0].append(v_type)
        c[1].append(v_evauluated)

e_types = []
for file in Path(r'D:\Games\steamapps\common\Half-Life Alyx\game\csgo\soundevents').glob("*.vsndevts"):
    with open(file) as fp:
        for line in fp.read().splitlines():
            if len(line) < 3:
                continue
            if line[:2] == '\t'*2 and line[2].isalpha():
                try:
                    k, v = tuple(line.strip().split('='))
                except ValueError:
                    print(line)
                if k.strip() == 'event_type':
                    e_types.append(v.strip())
                continue
                collect_dev(k.strip(), v.strip())

from collections import Counter
c = Counter(e_types)
print(c.most_common())
for k, v in collected.items():
    print(k, v[1])