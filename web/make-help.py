#!/usr/bin/env python3
"""Writes the in-page game guide (dist/help.html) for the web build.

The game content comes from the desktop key guides in
~/Desktop/Games/Roguelikes/Docs (build-docs.py + guides.py), so both guides
stay in sync; only the saving and "playing in the browser" parts are
written here, because they differ on the web."""
import html, importlib.util, os, sys

DOCS = os.path.expanduser('~/Desktop/Games/Roguelikes/Docs')
PAGE = 'zangband.html'

sys.path.insert(0, DOCS)
spec = importlib.util.spec_from_file_location('build_docs', os.path.join(DOCS, 'build-docs.py'))
docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)
from guides import GUIDES   # noqa: E402

game = next(g for g in docs.GAMES if g['file'] == PAGE)
guide = dict(GUIDES[PAGE])
info = dict(game['info'])
kbd = docs.kbd
esc = html.escape

SAVING = '''<ul>
<li><strong>Saving is automatic.</strong> Every save goes straight into this browser's storage (IndexedDB). The game saves every two minutes while it waits for your next command, and whenever you switch to another tab or window.</li>
<li><kbd>Ctrl+S</kbd> saves and keeps playing. <kbd>Ctrl+X</kbd> saves and quits; reload the page (or press <em>Play again</em>) to continue.</li>
<li>Reloading or closing the tab loses at most the last couple of minutes. The browser asks before you leave a running game.</li>
<li>Each browser keeps <strong>one character</strong>. <em>File ▾ → New game</em> deletes it and starts over.</li>
<li><em>Export save</em> downloads your savefile; <em>Import save</em> loads one. Use them to keep a backup or to move a character to another browser or computer.</li>
<li>Your window layout, zoom levels, window titles and the Tiles/Sound/Music buttons are stored in the same browser storage and survive a new character.</li>
<li>Private/incognito windows and "clear site data" delete the stored game. Export first if the character matters.</li>
</ul>'''

WEB = '''<ul>
<li><strong>Windows:</strong> the map fills the big window; Inventory and Visible (monsters and items in view) are on the right, Messages along the bottom. Recall, Equipment and Character can be turned on under <em>Windows</em>.</li>
<li><strong>Resize windows</strong> by dragging the gaps between them. The windows always fill the screen and never overlap; the game redraws them at their new size. <em>Reset windows</em> puts everything back.</li>
<li><strong>Zoom:</strong> <em>Zoom −</em> / <em>Zoom +</em> in the top bar change the size of the map tiles. Hover over a small window's title to show its <em>A−</em> / <em>A+</em> buttons, which change its text size.</li>
<li><strong>Rename a window</strong> by clicking its title, typing a new name and pressing <kbd>Enter</kbd> (<kbd>Esc</kbd> cancels, an empty name restores the default).</li>
<li><strong>Keys:</strong> arrow keys, the numeric keypad or <kbd>1</kbd>–<kbd>9</kbd> move you; <kbd>Shift</kbd> + direction runs. Zangband has no mouse support.</li>
<li><strong>Tiles</strong> switches between Shockbolt tiles and text. <strong>Sound</strong> and <strong>Music</strong> are off by default; Music plays a town tune while you are on the surface (towns and wilderness).</li>
<li>Browsers keep a few shortcuts for themselves (<kbd>Ctrl+W</kbd>, <kbd>Ctrl+T</kbd>, <kbd>Ctrl+N</kbd>, and <kbd>Cmd</kbd> shortcuts on a Mac), so those never reach the game.</li>
<li>If the game ever crashes, a message appears at the top; reload the page to continue from your last save.</li>
</ul>'''

KEY_HINTS = [
    ('?', 'In-game help: every command, with explanations'),
    ('H', 'Auto-explore: walk to the nearest unexplored spot (original keyset)'),
    ('Enter', 'Menu of all commands'),
    ('<', 'Go up (walks to the nearest known staircase)'),
    ('>', 'Go down (walks to the nearest known staircase)'),
    ('Ctrl+S', 'Save'),
]


def dl(items):
    return '<dl>' + ''.join(f'<dt>{kbd(k)}</dt><dd>{esc(d)}</dd>' for k, d in items) + '</dl>'


def section(anchor, title, body):
    return f'<h2 id="h-{anchor}">{esc(title)}</h2>{body}'


parts = []
toc = [('about', 'About the game'), ('keys', 'Keyboard controls'), ('saving', 'Saving your game'),
       ('tips', 'Tips'), ('guide', "New player's guide"), ('web', 'Playing in the browser'), ('credits', 'Credits')]
parts.append('<p>' + esc(game['tagline']) + '</p><ul class="toc">' +
             ''.join(f'<li><a href="#h-{a}">{esc(t)}</a></li>' for a, t in toc) + '</ul>')

parts.append(section('about', 'About the game',
                     guide.pop('What makes Zangband special')))

ess = ''.join(f'<div class="box"><h3>{esc(cat)}</h3>{dl(items)}</div>' for cat, items in game['essentials'])
all_keys = game['all']() if callable(game['all']) else game['all']
full = ''.join(f'<div>{kbd(k)}<span>{esc(d)}</span></div>' for k, d in all_keys)
parts.append(section('keys', 'Keyboard controls',
                     '<div class="box key"><h3>The keys to remember</h3>' + dl(KEY_HINTS) + '</div>'
                     '<h3>Essential keys</h3><div class="grid">' + ess + '</div>'
                     '<details><summary>Complete key list (' + str(len(all_keys)) + ' commands)</summary>'
                     '<div class="all">' + full + '</div></details>'))

parts.append(section('saving', 'Saving your game', SAVING))
parts.append(section('tips', 'Tips', info['Tips']))
parts.append(section('guide', "New player's guide",
                     ''.join(f'<h3>{esc(t)}</h3>{b}' for t, b in guide.items())))
parts.append(section('web', 'Playing in the browser', WEB))
parts.append(section('credits', 'Credits', info['Credits']))

# RVIP: About this version (rogue2wasm.md: Source and changes)
parts.append('<h2 id="h-version">About this version</h2><ul>'
             '<li>Based on <strong>Zangband 2.7.6</strong>.</li>'
             '<li>Original source: <a href="https://github.com/jjnoo/Zangband/tree/e177ff5" target="_blank" rel="noopener">jjnoo/Zangband (dev), commit e177ff5</a></li>'
             '<li>Our changes (port, auto-explore, command menu, web build): '
             '<a href="https://github.com/memmaker/zangband/compare/e177ff5...master" target="_blank" rel="noopener">memmaker/zangband</a></li></ul>')
print('\n'.join(parts))
