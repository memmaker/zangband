**RVIP port** of Zangband 2.7.6, upstream
[jjnoo/Zangband branch `dev` @ `e177ff5`](https://github.com/jjnoo/Zangband/tree/e177ff5)
(JJ Mifsud). Play: https://ruzzoli.de/roguelikes/zangband/
Our changes: https://github.com/memmaker/zangband/compare/e177ff5...master

Lineage: Moria → Angband (1990) → Zangband 1.0 (Topi Ylinen, 1994) → 2.x
(Robert Rühlmann, Steven Fuerst, the Zangband DevTeam, 2.3.0–2.7.5) →
2.7.6 (JJ Mifsud). The upstream notes are in `readme`, `z_faq.txt`,
`z_update.txt` and `lib/help/`.

What this port adds (the game code in `src/` is nearly untouched):
- **Web frontend** `src/main-web.c` (z-term, from TinyAngband) and `web/`
  (`zangband.js`, shared `rvip-wm.js`): Emscripten + Asyncify, saves in the
  browser's IndexedDB.
- **Windows**: main map plus Inventory, Messages, Visible, Recall, Equipment
  and Character windows; drag bars to resize, titles to move, layout via
  Windows ▾ (kept across reloads).
- **Tiles**: Shockbolt mode (Angband 4.2's 64×64 Shockbolt set, mapping in
  `lib/pref/graf-shb.prf` from `web/mkgraf-shb.py`), drawn nearest-neighbour.
- **Explore** `H`: walks to the nearest unexplored spot, stops for monsters
  and messages. **`<` / `>`** take the stairs you stand on, or walk to the
  nearest known ones (end of `src/cmd2.c`).
- **Enter menu**: every command, grouped, with the key of the current keyset
  (`cmd_menu()` in `src/util.c`).
- **Item menus**: `i` / `e` show a cursor list; Enter opens the actions for
  the item, letter = main action, Shift = drop, Ctrl = examine
  (`inven_screen()` in `src/cmd3.c`).
- **Sound** (off by default): Dubtrain effects (`web/sounds.py`) and a town
  music loop (`web/music/new_town.ogg`, from Quickband).
- Fixes for upstream memory bugs found with ASan (commit `1fa2be6`).

Controls: the original keyset (or the roguelike one, `=` options); Enter for
the command menu, `H` explore, `<`/`>` stairs, `?` help. The Help button
opens the game guide.

Build: `sh web/build.sh` → `web/dist` (needs emcc, cc, python3).
Deploy: `sh web/deploy.sh`. Notes: `HANDOVER.md`.

Credits: Zangband by Topi Ylinen, Robert Rühlmann, Steven Fuerst, the
Zangband DevTeam and JJ Mifsud; Angband by Ben Harrison and others, from
Moria/Umoria (Robert Alan Koeneke, James E. Wilson); licence: the
Angband/Moria notice in the source headers. Shockbolt tiles © Raymond
Gaustadnes (Shockbolt) 2012. Sound effects: Dubtrain sound pack.
