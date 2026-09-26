#!/usr/bin/env python3
"""Coverage of a tile set over every monster (r_info), object (k_info),
feature (f_info) and field (t_info) entry.  An entry counts when the pref
maps it to a non-empty tile inside the sheet.

  python3 web/tile-coverage.py            Shockbolt (graf-shb.prf, 64x64)
  python3 web/tile-coverage.py new        own 16x16 set (graf-new.prf)"""
import re, sys, os
from PIL import Image
L = 'lib'
if sys.argv[1:] == ['new']:
    pref, sheet, S = 'graf-new.prf', f'{L}/xtra/graf/16x16.bmp', 16
else:
    pref, sheet, S = 'graf-shb.prf', os.path.expanduser('~/Games/tactical-angband/lib/tiles/shockbolt/64x64.png'), 64
img = Image.open(sheet).convert('RGBA')
W, H = img.size
def tile_ok(a, c):
    x, y = (c & 0x7F) * S, (a & 0x7F) * S
    if not (a & 0x80 and c & 0x80) or x + S > W or y + S > H:
        return False
    # plain one-colour tiles count (16x16 floor is plain grey); empty = fully transparent
    return img.crop((x, y, x + S, y + S)).getbbox() is not None
maps, stand = {}, set()
prev = ''
for line in open(f'{L}/pref/{pref}', encoding='latin-1'):
    m = re.match(r'([RKFT]):(\d+):(0x[0-9A-Fa-f]+)/(0x[0-9A-Fa-f]+)', line)
    if m:
        maps[(m[1], int(m[2]))] = tile_ok(int(m[3], 16), int(m[4], 16))
        if prev.endswith('(stand-in)'): stand.add((m[1], int(m[2])))
    prev = line.rstrip()
tot = hit = 0
for kind, f in (('R', 'r_info'), ('K', 'k_info'), ('F', 'f_info'), ('T', 't_info')):
    ids = [int(x) for x in re.findall(r'^N:(\d+):', open(f'{L}/edit/{f}.txt', encoding='latin-1').read(), re.M)]
    ok = [i for i in ids if maps.get((kind, i))]
    miss = [i for i in ids if not maps.get((kind, i))]
    si = sum((kind, i) in stand for i in ok)
    print(f'{f}: {len(ok)}/{len(ids)} ({si} family stand-ins)  missing: {miss[:30]}{" ..." if len(miss) > 30 else ""}')
    tot += len(ids); hit += len(ok)
print(f'total: {hit}/{tot} = {100 * hit / tot:.1f}%, family stand-ins: {len(stand)}')
