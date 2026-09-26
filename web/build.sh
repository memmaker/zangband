#!/bin/sh
# Build Zangband for the browser (Emscripten + Asyncify).
# Output goes to web/dist; deploy with web/deploy.sh.
set -e
cd "$(dirname "$0")/.."
OUT=web/dist
rm -rf "$OUT" web/stage && mkdir -p "$OUT" web/stage/lib

# Lua bindings: tolua is a host tool (it loads its .lua parts from next to
# the binary, so it lives in src/lua/); l-*.c are generated, not committed
LUA="lapi ldebug lmem lstrlib lvm tolua_lb lauxlib ldo lobject ltable lzio tolua_rg
	lbaselib lfunc lparser ltests tolua_bd tolua_tm lcode lgc lstate ltm tolua_eh
	tolua_tt ldblib llex lstring lundump tolua_gp"
[ -x src/lua/tolua ] || cc -w -O1 -o src/lua/tolua \
	$(for f in $LUA tolua tolualua liolib; do echo src/lua/$f.c; done)
for p in monst object player random ui misc spell field; do
	[ src/l-$p.c -nt src/l-$p.pkg ] || (cd src && lua/tolua -n $p -o l-$p.c l-$p.pkg)
done

# Game files (no X11 fonts, BMP tiles or Tk scripts)
for d in edit file help pref; do cp -R lib/$d web/stage/lib/; done
mkdir -p web/stage/lib/script && cp lib/script/*.lua web/stage/lib/script/
mkdir -p web/stage/lib/data web/stage/lib/info web/stage/lib/save web/stage/lib/user web/stage/lib/apex web/stage/lib/bone
mkdir -p web/stage/lib/xtra/sound && cp lib/xtra/sound/sound.cfg web/stage/lib/xtra/sound/
find web/stage -name 'makefile*' -delete

# Sources: LUAWOBJS/ANGOBJS/ZUTILOBJS/BORGOBJS/LUAOBJS of makefile.std, no main-*/maid-x11
SRCS=$(sed -n '/^LUAWOBJS/,/^$/p;/^ANGOBJS/,/^$/p;/^ZUTILOBJS/p;/^BORGOBJS/,/^$/p' src/makefile.std \
	| grep -o '[a-z0-9_-]*\.o' | grep -v '^main\|^maid-x11' | sed 's/\.o$/.c/;s|^|src/|' | sort -u)
SRCS="$SRCS $(for f in $LUA; do echo src/lua/$f.c; done)"

emcc -O2 -fcommon -std=gnu99 -DUSE_WEB -Isrc -w \
	$SRCS src/main.c src/main-web.c \
	-o "$OUT/zangband-core.js" \
	-sASYNCIFY -sASYNCIFY_STACK_SIZE=65536 -sSTACK_SIZE=1048576 \
	-sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=64MB \
	-sEXPORTED_FUNCTIONS=_main,_web_request_save \
	-sEXPORTED_RUNTIME_METHODS=FS,IDBFS,HEAPU8,addRunDependency,removeRunDependency \
	-sFORCE_FILESYSTEM -lidbfs.js -sENVIRONMENT=web \
	--preload-file web/stage/lib@/zangband/lib

cp web/index.html "$HOME/Games/rvip-tools/web/rvip-wm.js" web/zangband.js "$OUT/"
# Shockbolt tiles (Angband 4.2 lib/tiles/shockbolt/64x64.png), lossless WebP, as in
# ~/Games/tactical-angband; drawn nearest-neighbour; mapping: lib/pref/graf-shb.prf
cp web/tiles.webp "$OUT/"
# Help: stub until stage 6 (web/make-help.py from ~/Games/tinyangband)
echo '<h2>Zangband</h2><p>The full guide comes with the docs. In the game: <kbd>?</kbd> help, <kbd>Enter</kbd> all commands, <kbd>H</kbd> explore, <kbd>&lt;</kbd>/<kbd>&gt;</kbd> walk to stairs, <kbd>Ctrl</kbd>+<kbd>X</kbd> save and quit.</p>' > "$OUT/help.html"
# Sound effects and town music are stage 6; sound.cfg is in the preload
mkdir -p "$OUT/music" && cp ../quickband/web/music/new_town.ogg "$OUT/music/"
rm -rf web/stage
ls -la "$OUT"
