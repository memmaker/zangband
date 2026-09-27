#!/usr/bin/env python3
"""Write the web build's sound.cfg (Zangband event names) from the Dubtrain
pack and copy the used .wavs. Upstream's lib/xtra/sound/sound.cfg names
samples Zangband never shipped, so every event comes from Dubtrain.
Usage: sounds.py <sound.cfg to write> <wav dir>"""
import os, shutil, sys
PACK = os.path.expanduser('~/Downloads/Dubtrain Angband Sound Pack v3.1.0')
# Zangband event (angband_sound_name[] in src/variable.c) -> Dubtrain events;
# same name unless listed. 'walk' stays silent (every step).
MAP = {'zap': 'zap_rod', 'scroll': 'study', 'buy': 'money1', 'sell': 'money2',
       'warn': 'hitpoint_warn', 'rocket': 'breathe_fire', 'n_kill': 'kill',
       'u_kill': 'kill_unique', 'quest': 'level', 'heal': 'recover', 'x_heal': 'recover',
       'bite': 'mon_bite', 'claw': 'mon_claw', 'm_spell': 'mon_cast_fear',
       'summon': 'summon_monster', 'breath': 'breathe_fire breathe_frost breathe_acid',
       'ball': 'cast_spell', 'm_heal': 'recover', 'atkspell': 'cast_spell', 'evil': 'cursed',
       'touch': 'mon_touch', 'sting': 'mon_sting', 'crush': 'mon_crush', 'slime': 'mon_drool',
       'wail': 'mon_wail', 'winner': 'level', 'fire': 'destroy', 'acid': 'destroy',
       'elec': 'destroy', 'cold': 'destroy', 'illegal': 'nothing_to_open',
       'fail': 'lockpick_fail', 'wakeup': 'mon_shriek', 'fall': 'stairs_down',
       'pain': 'mon_hit', 'destitem': 'destroy', 'moan': 'mon_moan', 'show': 'mon_insult',
       'unused': 'mon_gaze', 'explode': 'breathe_force', 'walk': ''}
EVENTS = open(os.path.join(os.path.dirname(__file__), '../src/variable.c')).read()
EVENTS = EVENTS.split('angband_sound_name[SOUND_MAX][16] =')[1].split('};')[0]
EVENTS = [e for e in EVENTS.replace('"', ' ').replace(',', ' ').split() if e.isidentifier()]
pack = {}
for line in open(os.path.join(PACK, 'sound.cfg'), encoding='latin-1'):
    if '=' in line and not line.lstrip().startswith('#'):
        k, v = line.split('=', 1)
        pack[k.strip()] = [f for f in v.split() if os.path.exists(os.path.join(PACK, f))]
cfg_path, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
lines = ['# Zangband web build: Dubtrain Angband Sound Pack v3.1.0 (web/sounds.py)', '[Sound]']
for e in EVENTS:
    files = sorted({f for d in MAP.get(e, e).split() for f in pack.get(d, [])})
    # DASP names lie: its 'shoot' has the melee swish; firing gets the arrow
    # samples only, and a melee miss (SOUND_MISS, py_attack) the swish
    if e == 'shoot': files = [f for f in files if f != 'plc_miss_swish.wav']
    if e == 'miss': files = ['plc_miss_swish.wav']
    assert files or e == 'walk', 'no sample for ' + e
    for f in files:
        shutil.copy(os.path.join(PACK, f), out)
    lines.append(f'{e} = {" ".join(files)}')
open(cfg_path, 'w').write('\n'.join(lines) + '\n')
