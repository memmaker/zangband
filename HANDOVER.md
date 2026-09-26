# Zangband 2.7.6: handover

## Source and changes

- Base: **Zangband 2.7.6**, upstream jjnoo/Zangband branch `dev` @ `e177ff5`
  (= tag-less "276" release `d09b2b8` + 3 fixes: colour table undo, 64-bit
  RNG, unbound-key message). `master` @ `d09b2b8` does not compile
  (`TERM_YELLOW` gone from `defines.h`), so the base is `dev`.
- Original source: https://github.com/jjnoo/Zangband/tree/e177ff5
- Upstream history kept; our commits on top (local branch `master`, no remote yet).

## RVIP progress

### Stage 1 (get + build): done 2026-09-26
- Folder `~/Games/zangband`, **case A** (z-term, `lib/edit`, `lib/pref`).
- Web frontend: `src/main-web.c` (copied from TinyAngband, a Zangband
  derivative; W3 pattern), registered as `"x11"` in `modules[]` of
  `src/main.c` under `USE_WEB` (with the real 3-argument
  `init_web(argc, argv, new_game)`: `INIT_MODULE()` casts init functions,
  which would trap in wasm). Page: `web/index.html`, `web/zangband.js`
  (`Module.qb`, IDBFS on `lib/save|user|apex|bone`, save = `0.PLAYER`),
  shared `rvip-wm.js` copied by the build. Text only for now (no tile sheet
  requested until stage 4).
- Build: `sh web/build.sh` → `web/dist`. Builds the host tool
  `src/lua/tolua` with `cc` first (it loads its `.lua` parts from its own
  folder, so it must live in `src/lua/`), generates `src/l-*.c` from
  `src/l-*.pkg` (both gitignored), then `emcc -O2 -fcommon -std=gnu99
  -DUSE_WEB -w` over `LUAWOBJS ANGOBJS ZUTILOBJS BORGOBJS` of
  `src/makefile.std` (minus `main-*`, `maid-x11`) + Lua 4 core + `main.c
  main-web.c`, `-sASYNCIFY -sASYNCIFY_STACK_SIZE=65536 -sSTACK_SIZE=1048576
  -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=64MB -sFORCE_FILESYSTEM -lidbfs.js
  -sENVIRONMENT=web`, preload `lib/{edit,file,help,pref,script/*.lua}` as
  `/zangband/lib`. Zero wasm-ld warnings; the only function-pointer casts
  (`-Wcast-function-type-strict`) are borg callback round-trips in
  `maid-grf.c` (cast back before the call; borg is off).
- Port edits (`USE_WEB`): `h-config.h` no `PRIVATE_USER_PATH`; `z-config.h`
  no `SAFE_SETUID`; `save.c` `web_sync_files()` after `save_player()`;
  `h-system.h` prototypes. No fork/signal/locking changes were needed.
- Quirks: no `TERM_XTRA_CLEAR` in this z-term (clears go through
  `wipe_hook`); no `bigcurs_hook`; prompt flag is `p_ptr->cmd.inkey_flag`,
  death `p_ptr->state.is_dead`, depth `p_ptr->depth`. Lua scripts
  (`lib/script/*.lua`) run fine in wasm (field/store triggers used in town).
- ASan: native curses build (`-DUSE_GCU -fsanitize=address`, isolated
  `HOME`, pty driver with random keys): 4 seeds × (2500–3000 keys from a
  new character, Ctrl-X save, 1500–3000 keys after restore). Three upstream
  bugs fixed in `port:` commit `1fa2be6`: `init2.c` window-flag loop read
  `window_flag_desc[32]` (has 15), `files.c` `show_file()` menu keys `u`–`z`
  overflowed `hook[62]`, `flavor.c` figurine name buffer out of scope. Then
  clean. Objects deleted.
- Browser test (own tab, 127.0.0.1): birth (Amberite Warrior, Beastman
  Rogue/Sorcery) → town (Satval/Ancacul Dun) → 400–500 random keys, no
  console errors (only favicon 404), Ctrl-X → reload → restored.
- **Tiles decision (stage 4): Shockbolt** (case A fallback). Own 16x16 set
  (`graf-new.prf` + `lib/xtra/graf/16x16.bmp`) covers **1528/1671 = 91.4%**
  of r/k/f/t_info entries (`python3 web/tile-coverage.py`; monsters
  773/892, objects 536/553, features 79/79, fields 140/147): below 95%.
- Open problems: sub-window routing (inventory shows in the Messages window,
  Inventory shows a rule): Zangband's window flags differ from TinyAngband's
  (15 flags incl. overhead/dungeon view), stage 5 sets them (`user-x11.prf`
  / `window_flag`). No option defaults (auto_more etc.) yet. The help menu
  once said "Cannot open 'birth.txt'" during random keys (not reproduced).

### Next: stage 2 (explore + stairs)
- Copy the explore/stairs code from TinyAngband (`~/Games/tinyangband/src/cmd2.c`
  `do_cmd_explore()` ~l.4709, hooked in `dungeon.c` ~l.3414); Quickband's
  `src/pathfind.c` / `cmd0.c` for the stair walk.
- Main loop: `process_player()` (`src/dungeon.c` ~l.2588) →
  `process_command()`; keys go through term 0's queue (`Term_keypress`,
  as `web_pump()` does); commands table in `dungeon.c`/`cmd*.c`.
- Map access: no `cave[][]`; grids via `area(x, y)` → `cave_type`
  (`feat`, `info`, `o_idx`, `m_idx`, `fld_idx`) and player memory via
  `parea(x, y)` → `pcave_type` (`feat` = memorised feature, `player` flags);
  bounds `in_bounds2()` / `in_boundsp()` (function pointers: dungeon vs
  wilderness). Note the argument order is (x, y).
- Wilderness: the town is part of the wilderness (`wild1-3.c`, `place[]`);
  `p_ptr->depth == 0` there; dungeon entrances are places, not plain stairs.
  Stairs: `FEAT_LESS 0x06`, `FEAT_MORE 0x07` (`defines.h` ~l.1145); traps
  and glyphs are *fields* (`fld_idx`, `t_info`), not features.

### Stage 2 (explore + stairs): done 2026-09-26
- **Explore key `H`** (Quickband's key; free in the original keyset: `X` is
  a `w0` keymap in `pref-key.prf`, `` ` `` becomes Escape in `util.c`).
  Roguelike keyset: `H` stays "run west", so no explore key there.
- Code: end of `src/cmd2.c` (port of Quickband `pathfind.c`
  `explore_step()`): `auto_explore` flag, `explore_step()`,
  `do_cmd_explore()`, `explore_to_stairs()`, `explore_reset()`,
  `explore_new_level()`; prototypes in `externs.h`.
- Hooks: `process_command()` `case 'H'` (`dungeon.c`); `process_player()`
  treats `auto_explore` like running (key abort check + `else if
  (auto_explore) explore_step();` before running); `dungeon()` calls
  `explore_new_level()` where `leaving = FALSE`; `disturb()` (`effects.c`)
  calls `explore_reset()`. `do_cmd_go_up/down()` (`cmd2.c`) call
  `explore_to_stairs()` instead of "I see no ... staircase here".
- **Known grid**: `parea(x, y)->feat != FEAT_NONE`, plus (dungeon only) the
  explorer's own `explore_seen[MAX_HGT][MAX_WID]`, because Zangband forgets
  torch-lit floors (`view_torch_grids` off) and the explorer would walk
  back and forth. BFS array is indexed from `p_ptr->min_wid/min_hgt`
  (wilderness window is 144x144, dungeon up to 66x198).
- Targets: known grid next to an unknown one, or a grid with a seen object
  (`OB_SEEN`) not yet stood on (marked with the free bit `OB_DUMMY4` as
  `OB_EXPLORED`). Avoids known traps (`field_first_known(FTYPE_TRAP)`), shop
  entrances (`FTYPE_BUILD`), known `FIELD_INFO_NO_ENTER` fields, lava/acid/
  deep water; opens closed doors with `do_cmd_open_aux()`; locked doors
  (`FEAT_CLOSED` + `FTYPE_DOOR` field) are never targets or walked through.
  Stops: `disturb()`, a new message (`message_num()` changed), a visible
  non-pet hostile monster in LOS (explore only; stair walks may flee), a
  step that did not move (unseen monster), no light in the dungeon.
- Wilderness: explore only inside the current town (`place[p_ptr->place_num]`
  block rectangle); in daytime the town is fully known, so it says "Nothing
  left to explore." `>` in town walks to the dungeon entrance (`FEAT_MORE`)
  and descends (tested).
- Option defaults: `init_web()` sets `auto_more` and `center_player` in
  `option_info[]` (new characters; saves keep their own). Birth had no
  `-more-`.
- Help: `lib/help/command.txt` (H), `commdesc.txt` (Auto-explore, `<`/`>`).
- Tested in the browser (own tab, 127.0.0.1): town `H` ("Nothing left"),
  `>` walk + descend, dungeon level 1 explored over many presses (rooms,
  corridors, doors, gold/items walked to, stops on monsters/messages), `<`
  walk + up to town, `>` walk to a seen down staircase on level 1 →
  level 2, explore there. Test IDBFS databases (`/zangband/lib/*`) deleted.
- ASan (native `-DUSE_GCU`, pty, random keys weighted to `H`/`<`/`>`,
  4 seeds x (2500 new + 2000 restored)): two upstream bugs fixed, then
  clean: `do_cmd_macro_aux()` (`cmd4.c`) key burst overflowed `tmp` via
  `ascii_to_text()` (now caps the trigger at 255 keys);
  `get_player_sort_choice()` (`ui.c`) indexed `strings[INVALID_CHOICE]` on
  Escape during birth.
- Open problems: a visible monster blocking the only path makes `>`/`<`
  say "You know of no way down/up"; explore knows a closed door is locked
  before trying it (door field); no explore key in the roguelike keyset;
  the move onto an object asks "Pick up ...? [y/n/k]" (game's own walk).

### Next: stage 3 (Enter menu + inventory)
- Keys: `request_command()` (`util.c`, keymaps via `keymap_act[mode][cmd]`,
  `pref-key.prf` has a `C:0:^J` keymap) → `process_command()` switch in
  `dungeon.c` (`case '\r'` exists there). Add the menu entry for `H`.
- Template code (RVIP A3b/A3c): Zangband-style → TinyAngband's
  `inkey_from_menu()` (`~/Games/tinyangband/src/util.c` / `autopick.c`,
  `command_menu` option); item menus from Quickband `cmd-obj.c`
  (`textui_inven_screen()`, `do_item_on()`), `get_item()` cursor keys,
  `show_obj_list()` (`obj-ui.c`), reopen hook in `cmd0.c`. Zangband has its
  own `menu_type` / `display_menu()` in `ui.c` (used by `do_cmd_options`,
  macro menus) — check it before porting.

### Stage 3 (Enter menu + inventory): done 2026-09-26
- **Enter menu**: `cmd_menu()` in `src/util.c` (TinyAngband's
  `inkey_from_menu()` idea, groups and commands in `cmd_menu_list[]` as
  `lib/help/commdesc.txt` groups them, incl. `H` explore and `<`/`>`).
  Opened in `request_command()` right after `inkey()` when the key is
  `'\r'`/`'\n'` and `!keymap_act[mode][key]` (so `C:0:^J` → `\r` also
  opens it; roguelike `^J` stays tunnel south). Two boxes: groups (a–p),
  then the group's commands with the key of the current keyset
  (`command_key()` reverse-looks-up `keymap_act`, e.g. roguelike `T`, `Z`,
  `^D`; explore has none in roguelike). 2/8/arrows move, Enter/Space/5/6
  choose, the letter/key chooses, Esc/0/4 back. The chosen *underlying*
  command skips the keymaps (`raw` flag in `request_command()`), so it runs
  through `process_command()` in both keysets.
- Boxes: `box_draw()` / `box_menu()` in `util.c`, sized to content (moved
  to fit the screen, no scrolling). Zangband's own `display_menu()` (`ui.c`)
  was not used: full-screen, no box, cursor only in scroll mode.
- **Item menus**: `inven_screen()` at the end of `src/cmd3.c` (Quickband's
  `textui_inven_screen()` ported); `do_cmd_inven()`/`do_cmd_equip()` call
  it. Cursor `>` left of the list (`show_list_col`, set by `show_list()` /
  `show_equip()` in `object1.c`). Letter = main action, Shift = drop,
  Ctrl = examine, Enter/Space/5 = `inv_action_menu()` (box over the item
  line), `+ - *` = main/drop/examine, 4/6 or `/` = other list, Esc/0/. close,
  any other key = normal command (as before).
- **How item actions run (key queue + preselect)**: `inv_act[]` holds
  each action's underlying key, name and the same item test and places
  as that command's `get_item()` call (tval, hook, USE_INVEN/EQUIP).
  Running one sets `get_item_preselect = o_ptr` and
  `queue_raw_command(key)` (`p_ptr->cmd.new`, no keymap); the command runs
  through `process_command()` and its `get_item()` (`object1.c`) returns the
  preselected item if the mode and tester accept it (else prompts as usual;
  `save_object_choice()` keeps `n` repeat working). `dungeon.c`: clears
  the preselect after a command unless a queued one is pending; `inven_reopen`
  queues `i`/`e` again before the next command unless a non-pet monster is
  in view (`inven_may_reopen()`). `item_tester_hook_activate` in `cmd6.c`
  is no longer static.
- No mouse: the page queues clicks but `web_pump()` drops them ("No mouse
  support in this variant"), so no click selection.
- Web: `sound.cfg` is now in the preload (`/zangband/lib/xtra/sound/`),
  read lazily by `loadSoundCfg()` in `zangband.js` (a fetched `.cfg` was a
  download prompt in the pane).
- Tested in the browser (own tab): Enter menu lists all 16 groups, pick by
  cursor (Game status → time) and by key (`H`), Esc closes, `^J` opens it;
  item menus on real items: read (Rumour), quaff (CLW, letter), eat (ale,
  menu and letter), wield (dagger, letter), wear (gloves, menu key `w`),
  take off (menu Enter; roguelike `T`), drop (Shift), examine (menu `I`),
  Fire shown only with a bow wielded; list reopens after each action.
  Roguelike keyset (`"Y:rogue_like_commands`): menu shows roguelike keys,
  explore runs from the menu.
- ASan (native `-DUSE_GCU`, pty, random keys weighted to Enter, `i`/`e`,
  letters, Shift/Ctrl letters, 2/4/6/8, `H`, `<`/`>`; 4 seeds x (3000 new +
  2000–2500 restored/new after death)): menus and item actions exercised
  (menus drawn 14–28 times per run), no reports. Driver lesson: ^Y is
  DSUSP on macOS (game stopped); SIGTERM at the end deadlocks in `quit()`
  → `endwin()` from the signal handler (upstream), use SIGKILL.
- Open problems: the reopened list hides the action's message line (it is
  in the message window and `^P`); Tab/^H act as Ctrl+letter examine in
  the list; the item menu box can cover the right part of the list.

### Next: stage 4 (tiles)
- Decision from stage 1: **Shockbolt** (own `graf-new.prf` + 16x16 set
  covers only 91.4% of r/k/f/t_info, `python3 web/tile-coverage.py`).
- Template tile loading (RVIP A4): TinyAngband `src/main-web.c`
  `init_web()` sets `use_graphics`, `arg_graphics`, `use_transparency`,
  bigtile and `ANGBAND_GRAF = "new"` (→ `graf-new.prf`); its
  `web/bmp2png.py` turns `16x16.bmp` into the page's PNG and
  `tinyangband.js` draws `js_pict` cells from it (no `web/tiles` folder).
  Shockbolt worked example on the web: `~/Games/tactical-angband`
  (HANDOVER "Tiles": 64x64 Shockbolt Dark drawn at 32 px); FrogComposband
  took the same decision.

### Stage 4 (tiles): done 2026-09-26
- **Tile set: Shockbolt** 64x64 (Raymond Gaustadnes; Angband 4.2
  `lib/tiles/shockbolt/64x64.png`, copied as `web/tiles.webp` from
  `~/Games/tactical-angband/web/tiles.webp`, lossless, 13 MB, committed),
  the one set: own 16x16 set covers 91.4%. Drawn nearest-neighbour
  (`imageSmoothingEnabled = false`) at the map cell size, square tiles in
  Zangband's **bigtile** mode (one grid = two half-width cells; tile size =
  `L.tile`, Zoom -/+ 16..64 px).
- **Pref**: `lib/pref/graf-shb.prf`, generated by `python3 web/mkgraf-shb.py`
  from tactical-angband's `graf-shb-dark.prf`, `flvr-shb.prf`, `xtra-shb.prf`
  and its 4.2 `gamedata` (monster/monster_base/flavor). Monsters/objects by
  name (accents stripped, a few aliases), the rest family stand-ins (monster:
  same symbol + colour; object: same tval); features, fields (traps, runes,
  locked doors, corpses, 113 shops by keyword → 4.2 shop tiles), S: slots
  (bolts by colour → GF tiles; flavours 0x80..0xFF by colour → 4.2 flavour
  tiles) by hand; player `R:0` per class/race from `xtra-shb.prf` (no
  `$GENDER` in Zangband). Loaded via `graf-x11.prf` `?:[EQU $GRAF shb]`.
- **Coverage** (`python3 web/tile-coverage.py`; `... new` for the old set):
  1668/1671 = **99.8%** (r_info 892/892, k_info 552/553, f_info 78/79,
  t_info 146/147; the 3 misses are the index-0 "nothing" entries).
  614 by name, 528 by hand, **527 family stand-ins** (445 monsters, 82
  objects).
- **C (decides the tile per cell)**: `GRAPHICS_SHOCKBOLT 6` (`defines.h`),
  `$GRAF` = "shb" (`files.c`); `maid-grf.c` `shb_triplet()`: Shockbolt terrain
  is torch/lit/dark side by side, the pref maps the lit one, dark = c+1,
  torch = c-1 (only for the 11 listed floor/stairs/rubble/vein/wall/lava
  tiles; AB-only hacks for spells/corpses are not triggered). Loader:
  `src/main-web.c` `web_graphics()` (use_graphics, transparency, bigtile)
  from `js_tiles_wanted()` at start; `web_col()`/`web_run()` map term
  columns to page cells (x' = 2x - big_x1 in the big region, passed as
  `big` to `js_text`/`js_pict`/`js_wipe`/`js_curs`); `web_switch_graphics()`
  (toggle_bigtile + reset_visuals + do_cmd_redraw) at the command prompt.
- **JS only blits**: `web/zangband.js` `pict(..., big)` (tile over terrain
  tile), `text(..., big)`; **Tiles: on/off** button (`btn-tiles`, kept in the
  layout file as `L.text`), applied at the next command prompt.
  `glyph()` now draws font-x11.prf's DEC chars (1 ◆, 2 ▒ walls): text mode
  showed no walls before.
- Tested in the browser (own tab, 127.0.0.1): town (shop entrance tiles,
  brick buildings, grass, tree, floors), dungeon 1 via `>` (walls, doors,
  stairs, ant, skeleton), debug jumps to 5/8 (water, magma/quartz,
  treasure veins, eye, molds, ring on floor, 8 traps from a Trap Creation
  scroll), dwarf warrior player tile. Canvas check (`2x1` cells of the map):
  tiles 734 tile cells / 7 other, text 1511 text / 0 tile; toggle
  tiles→text→tiles twice, map intact. IDBFS test dbs `/zangband/lib/*`
  deleted.
- Native ASan with graphics: skipped (native build is curses `USE_GCU`, no
  graphics; `shb_triplet()` is inert there).
- Open problems: 527 stand-ins (Zangband-only monsters: many share a
  family tile, e.g. all unknown `p` → first same-colour `p`); trees/bushes
  are Shockbolt monster tiles (huorn, willow, mold patches), sand/snow use a
  sandstone tile; lighting shades only with `view_yellow_lite` /
  `view_special_lite` on (off by default); the reduced map (`M`) draws
  tiles squashed into half cells (as X11); the Messages window still shows
  the inventory; the row-0 prompt box can leave the end of a long message
  line visible beside it (stage 5, RvipWM.prompt). Credit Shockbolt in the
  Help page/README (stage 6/7).

### Next: stage 5 (web page)
- Window flags: Stage 1 found the inventory in the Messages window;
  Zangband has 15 window flags (incl. overhead/dungeon view), not
  TinyAngband's: set them for terms 1-5 (`window_flag[]`, a web
  `user-x11.prf`/`init_web()` default) to match `TERMS` in `web/zangband.js`
  (main, Inventory, Messages, Visible, Recall, Equipment) and the window
  list in `web/index.html`.
- Layout file: `LAYOUT_FILE` = `/zangband/lib/user/web-layout.json` in
  `zangband.js` (now also holds `text` for the Tiles button).
- `web/deploy.sh`: copy from `~/Games/tinyangband/web/deploy.sh` (or
  tactical-angband), target `ruzzoli.de/roguelikes/zangband/`, with the
  guard line (deploy only pushed commits). No repo yet: no deploy before
  stage 7. `tiles.webp` is 13 MB: fine for rsync, mention in the page's
  loading status if slow.

### Stage 5 (web page): done 2026-09-26
- **Windows** (`rvip-wm.js`, shared copy; `web/index.html` `#t-<id>`,
  `TERMS` in `web/zangband.js`, 7 terms = `WEB_TERMS` in `src/main-web.c`):
  0 Map, 1 Inventory `PW_INVEN`, 2 Messages `PW_MESSAGE`, 3 Visible
  `PW_VISIBLE`, 4 Recall `PW_MONSTER|PW_OBJECT`, 5 Equipment `PW_EQUIP`,
  6 Character `PW_PLAYER` (new). Flags from `web_window_flags[]`, set in
  `init_web()` (runs before birth/load: birth.c only fills windows 1/2 when
  empty; a savefile brings its own flags, so pre-stage-5 test saves keep the
  old routing). Default on: Map, Inventory, Visible, Messages; Recall,
  Equipment, Character via Windows ▾. Fixes the inventory-in-Messages bug
  (birth.c's defaults were 1 = messages, 2 = inventory).
- **Layout file** `/zangband/lib/user/web-layout.json` (IDBFS; splits, wm
  tree incl. which windows are on, zoom, fonts, titles, Tiles, audio).
- **Game end**: one path, `close_game()` → `quit(NULL)` (`dungeon.c` end of
  `play_game()`) → `quit_aux` = `hook_quit` (set in `init_web()`, after
  main.c's own) → `js_quit(msg, p_ptr->state.is_dead)`. Death: tombstone
  menu (D/C/T/Esc) + "Do you really want to exit?" + scores wait for keys in
  C, then the page syncs and reloads; the dead save starts a new birth.
  Ctrl-X: "Press Return", Hall of Fame, then the "Play again" overlay
  (reload restores). Only other `exit()`: Lua panic (`lua/ldo.c`).
- **Help**: `build.sh` writes a stub `help.html` (stage 6 replaces it).
- **`web/deploy.sh`**: guard line from `roguelikes-index/deploy.sh`, target
  `ruzzoli.de/roguelikes/zangband/`. Dry run: "commit + push first", exit 1.
  **Not deployed, no repo.**
- Tested (own tab, 127.0.0.1): new character → inventory in Inventory,
  messages in Messages, soldier ant/newt/hell wyrm in Visible, equipment and
  character sheet in theirs; gutter drag + Equipment/Character on → reload →
  same layout; Ctrl-X → overlay → reload → character restored at DL1;
  debug `0756 ^A n` (Great hell wyrm) → death → tombstone → Esc, y → page
  reloaded → birth → new town character, windows right; Help opens/Esc
  closes; no console errors. IDBFS `/zangband/lib/*` deleted afterwards.
  Native ASan (1 seed, 2500 new + 1500 restored keys): clean.
- Open problems: Character window cuts `display_player()` (needs 80 cols,
  overlaps at narrow width); the Visible list's second symbol slot is the
  graphics char (upstream format `Name ('a')/(tile)`); message history of a
  dead character carries into the new one (upstream); spell list
  (`PW_SPELL`) has no window; 13 MB `tiles.webp` loads slowly.

### Next: stage 6 (docs + sound)
- Sound: `lib/xtra/sound/sound.cfg` is already in the preload and
  `loadSoundCfg()` in `web/zangband.js` reads it; add the wavs (Dubtrain,
  a `web/sounds.py` like the template's), the event hook is z-term's
  `Term_xtra(TERM_XTRA_SOUND)` → `js_sound()`; Sound/Music buttons exist,
  off by default.
- Help: `web/make-help.py` from `~/Games/tinyangband/web/` with
  `PAGE='zangband.html'`; replace the stub line in `web/build.sh`.
- Docs entry under `~/Desktop/Games/Roguelikes/Docs/` (`build-docs.py`,
  `guides.py`, with a Tips section); credit Shockbolt tiles.

### Stage 6 (docs + sound): done 2026-09-26
- **Docs** (`~/Desktop/Games/Roguelikes/Docs`, not git): `GAMES` entry
  `zangband.html` in `build-docs.py` (before Sil-Q; essentials, complete
  list = original + roguelike keyset parsed from `lib/help/command.txt`,
  sections About / Tips / In the browser / Credits), `GUIDES['zangband.html']`
  (first section "What makes Zangband special") and `SAVING['zangband.html']`
  in `guides.py`. `python3 build-docs.py` → `zangband.html` (140 keys).
  Credits as the splash screen and help say: Topi Ylinen, Robert Rühlmann,
  Steven Fuerst, DevTeam (2.3.0–2.7.5), JJ Mifsud (2.7.6); Angband (Ben
  Harrison), Moria/Umoria; licence = the Angband/Moria notice in the sources
  (no GPL file in this tree); Shockbolt © Raymond Gaustadnes 2012 (licence as
  tactical-angband `docs/copying.rst`); Dubtrain sounds.
- **Help**: `web/make-help.py` (TinyAngband's, `PAGE='zangband.html'`, key box
  with `H`, adds a Credits section, "About this version" jjnoo/Zangband @
  `e177ff5` + memmaker compare link) → `$OUT/help.html` in `build.sh` (stub
  gone). After a Docs edit: rebuild or `python3 web/make-help.py >
  web/dist/help.html`.
- **Sound**: `web/sounds.py <cfg> <wavdir>` writes the web `sound.cfg` (all
  65 `angband_sound_name[]` events, read from `src/variable.c`) into the
  preload stage and copies 103 Dubtrain wavs (10 MB) to `dist/sound`.
  Zangband names map to Dubtrain names in `MAP` (e.g. bite → mon_bite,
  breath → breathe_*, fail → lockpick_fail); `walk` silent. Upstream
  `lib/xtra/sound/sound.cfg` untouched (names wavs Zangband never shipped).
  Some Dubtrain cfg entries name missing files; sounds.py skips them.
  JS/C unchanged (hook `TERM_XTRA_SOUND` → `js_sound` → `Module.qb.sound`).
- Tested (own tab, 127.0.0.1:8766): fresh load Sound off / Music off; Help
  shows the guide (About … Credits, About this version); new Amberite
  Warrior; Sound on (real click) → eat + drop fired `eat`/`drop`,
  `plm_eat_bite.wav`/`plm_drop_boot.wav` loaded; Music on (real click) in
  town → `music/new_town.ogg` 200; reload → both still on; no console
  errors. IDBFS `/zangband/lib/*` deleted from `help.html`. No C change, no
  ASan run.
- Open problems: no hit/kill tested in the browser (same code path as
  eat/drop); music plays on the whole surface (depth 0 = wilderness too);
  `new_town.ogg` is copied from `../quickband/web/music` (stage 7: keep
  or vendor into `web/music`).

### Next: stage 7 (publish)
- README first lines: upstream https://github.com/jjnoo/Zangband branch
  `dev` @ `e177ff5` (2.7.6), compare link `…/compare/e177ff5...master`
  (branch is `master`); lineage Angband → Zangband 1.0 (Topi Ylinen 1994)
  → 2.x (Rühlmann, Fuerst, DevTeam) → 2.7.6 (JJ Mifsud); the web port
  (`src/main-web.c`, `web/`), controls (`H` explore, `<`/`>` stair walk,
  Enter menu, item menus), credits incl. Shockbolt and Dubtrain.
- `~/Games/roguelikes-index` (`git pull` first): card like DynaHack's
  commit `17d4c04` "index: DynaHack card + tree"; tree: Zangband already a
  parent (`<span class="n">Zangband</span> 1994 · Topi Ylinen`, over
  XAngband/TinyAngband, Hengband, PernAngband/ToME 2): turn that span into
  the `zangband/` link, no new node.
- Step 5b og block by hand in `web/index.html`; `web/deploy.sh` only after
  the orchestrator created `memmaker/zangband` and the commits are pushed;
  W2 row in RVIP.md.
