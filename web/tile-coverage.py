#!/usr/bin/env python3
"""Coverage of Zangband's own 16x16 set (graf-new.prf + 16x16.bmp) over every
monster (r_info), object (k_info), feature (f_info) and field (t_info) entry.
An entry counts when the pref maps it to a tile inside the bitmap (plain
one-colour tiles count: the floor is plain grey)."""
import re, sys
from PIL import Image
L = sys.argv[1] if len(sys.argv) > 1 else 'lib'
img = Image.open(f'{L}/xtra/graf/16x16.bmp').convert('RGB')
W, H = img.size
def tile_ok(a, c):
    x, y = (c & 0x7F) * 16, (a & 0x7F) * 16
    if not (a & 0x80 and c & 0x80) or x + 16 > W or y + 16 > H:
        return False
    return True
maps = {}
for line in open(f'{L}/pref/graf-new.prf', encoding='latin-1'):
    m = re.match(r'([RKFT]):(\d+):(0x[0-9A-Fa-f]+)/(0x[0-9A-Fa-f]+)', line)
    if m:
        maps[(m[1], int(m[2]))] = tile_ok(int(m[3], 16), int(m[4], 16))
tot = hit = 0
for kind, f in (('R', 'r_info'), ('K', 'k_info'), ('F', 'f_info'), ('T', 't_info')):
    ids = [int(x) for x in re.findall(r'^N:(\d+):', open(f'{L}/edit/{f}.txt', encoding='latin-1').read(), re.M)]
    ok = [i for i in ids if maps.get((kind, i))]
    miss = [i for i in ids if not maps.get((kind, i))]
    print(f'{f}: {len(ok)}/{len(ids)}  missing: {miss[:30]}{" ..." if len(miss) > 30 else ""}')
    tot += len(ids); hit += len(ok)
print(f'total: {hit}/{tot} = {100 * hit / tot:.1f}%')
