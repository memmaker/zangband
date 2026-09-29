# Zangband 2.7.6: handover

RVIP stages 1–9 done (2026-09-26). Live: https://ruzzoli.de/roguelikes/zangband/,
repo https://github.com/memmaker/zangband (`master`), shrine
https://ruzzoli.de/roguelikes/shrine/zangband.html. Procedure:
`~/Games/rvip-tools/RVIP.md`.

## Source
- **Case A** (z-term, `lib/edit`, `lib/pref`). Remote `upstream` =
  jjnoo/Zangband, base branch `dev` @ `e177ff5` (2.7.6 release `d09b2b8` + 3
  fixes). `master` @ `d09b2b8` does not compile (`TERM_YELLOW` gone), so `dev`.
- Lineage (tree text): 1994 · Topi Ylinen; 2.x from Angband 2.8.1, later
  Robert Rühlmann, Steven Fuerst, DevTeam 2.3.0–2.7.5, JJ Mifsud 2.7.6
  (2012–2013).

## Build, test, deploy
- `sh web/build.sh` → `web/dist`. Builds the host tool `src/lua/tolua` with
  `cc` first (must live in `src/lua/`), generates `src/l-*.c` from
  `src/l-*.pkg` (gitignored), then emcc over `LUAWOBJS ANGOBJS ZUTILOBJS
  BORGOBJS` of `src/makefile.std` (minus `main-*`, `maid-x11`) + Lua 4 +
  `main.c main-web.c`, Asyncify, IDBFS. Preload `lib/{edit,file,help,pref,
  script/*.lua}` + web `sound.cfg` as `/zangband/lib`. Pages load the shared
  `../rvip-wm.js` / `../rvip-app.js`.
- `web/deploy.sh` → `ruzzoli.de/roguelikes/zangband/` (needs commit + push).
- Native ASan test build (ad hoc): `-DUSE_GCU -fsanitize=address`, isolated
  `HOME`, pty random keys. Driver: ^Y is DSUSP on macOS; SIGTERM deadlocks in
  `quit()` → `endwin()`, use SIGKILL. `.github/workflows/release.yml` builds
  Linux/macOS/Windows releases.
- Cheats: `USE_DEBUG` → `^W` wizard, `^A` debug (e.g. `0756 ^A n` = Great
  hell wyrm). Borg (`^Z`) compiled in, untested in the browser.

## Port map (`USE_WEB`)
- `src/main-web.c` (from TinyAngband), registered as `"x11"` in `modules[]`
  of `main.c` with a real 3-argument `init_web()` (the `INIT_MODULE()` cast
  traps in wasm). No `TERM_XTRA_CLEAR` (clears via `wipe_hook`), no
  `bigcurs_hook`. `init_web()` sets `auto_more`, `center_player` for new
  characters, `hook_quit`, and window flags (`web_window_flags[]`, 7 terms:
  Map, Inventory, Messages, Visible, Recall, Equipment, Character `PW_PLAYER`
  new; a savefile brings its own flags).
- Text windows (RVIP part 2 "Presentation rules (W0)" rule 6): map canvas =
  term 0's map area only; sub-terms have fixed sizes (`web_cols[]` /
  `web_rows[]`) and go out as trimmed HTML rows (`web_sub_fresh()`); sidebar
  + status line = Status window (`web_status()`); pop-up (`#pop`) = term 0
  while `!character_generated || (character_icky && Term->scr->next)`, diffed
  against the oldest saved screen unless one was cleared
  (`term_win.cleared`). Fixes: `Term_bigtile_expand()` keeps the cursor;
  `do_cmd_view_map()` wrapped in `screen_save()/screen_load()`. Pop-up list
  icons are CSS sprites; sub-window lists draw no tiles. No mouse.
- Other edits: `h-config.h` no `PRIVATE_USER_PATH`; `z-config.h` no
  `SAFE_SETUID`; `save.c` `web_sync_files()` after `save_player()`.
- Explore (`H`, original keyset; roguelike `H` = run west): end of
  `src/cmd2.c` (Quickband port), hooks in `dungeon.c`, `disturb()`
  (`effects.c`). Known grid = `parea(x,y)->feat != FEAT_NONE` + own
  `explore_seen[][]` (Zangband forgets torch-lit floors). Grid access is
  `(x, y)` order; traps/doors/shops are *fields* (`fld_idx`). Moves visibly
  (40 ms per step). `<`/`>` off the stairs only walk to the nearest known
  staircase; in town `>` walks to the dungeon entrance.
- Enter menu: `cmd_menu()` in `util.c` (`cmd_menu_list[]`, `box_menu()`, keys
  of the current keyset via `command_key()`). Item menus: `inven_screen()` at
  the end of `cmd3.c`; actions via `get_item_preselect` +
  `queue_raw_command()`, list reopens (`inven_reopen`) unless a non-pet
  monster is in view.
- Tiles: **Shockbolt** 64x64 (`web/tiles.webp`, 13 MB, from tactical-angband;
  own 16x16 set covers 91.4%). `lib/pref/graf-shb.prf` from
  `python3 web/mkgraf-shb.py`; coverage `python3 web/tile-coverage.py`
  (99.8%, 527 family stand-ins). `GRAPHICS_SHOCKBOLT 6`, `$GRAF` "shb",
  bigtile; `maid-grf.c` `shb_triplet()` (torch/lit/dark = c-1/c/c+1 for 11
  terrain tiles). Switch at the command prompt (`web_switch_graphics()`).
- Game end: `close_game()` → `quit()` → `hook_quit` → `js_quit`; dead save
  starts a new birth. Run-end beacon: `scores.c` `close_game()` is_dead
  branch → `web_run_end(total_points())` (win = `total_winner`, checked
  first). Score is 0 until the character gains exp. Killer art:
  roguelikes-index `killers/make.py` `zangband()`.
- Sound: `web/sounds.py` writes the web `sound.cfg` (65 events from
  `src/variable.c`) + 103 Dubtrain wavs; music `web/music/new_town.ogg`.
  Help: `web/make-help.py` from the Docs entry
  `~/Desktop/Games/Roguelikes/Docs` (`zangband.html`).
- Layout file `/zangband/lib/user/web-layout.json`.

## Open problems
- Explore: a visible monster blocking the only path makes `>`/`<` say "You
  know of no way down/up"; explore knows a closed door is locked before
  trying it; no explore key in the roguelike keyset; stepping onto an object
  asks "Pick up ...? [y/n/k]".
- Item lists: the reopened list hides the action's message; Tab/^H act as
  Ctrl+letter examine; the item menu box can cover the list.
- Tiles: 527 stand-ins; trees/bushes are monster tiles, sand/snow sandstone;
  `M` squashes tiles; 13 MB `tiles.webp` loads slowly.
- A dead character's message history carries into the new one (upstream);
  the Visible list's second symbol is the graphics char; no spell window;
  music plays on the whole surface. Character window: was cut when narrow,
  now a fixed 80x24 HTML term (recheck).
- Beacon: real Serpent kill not tested (win tested via a temporary build).
