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
