# Changes from upstream

This is the Asciiverse packaging of Scrap, the roguelike Thijs van Ommen
wrote in ten days in 2005 and extended in 2006, GPL-2.0-or-later (`COPYING`
and every source file's header; `mt19937ar.h`, the Mersenne Twister by
Makoto Matsumoto and Takuji Nishimura, carries its own BSD licence).
Upstream is github.com/thijsvanommen/scrap, the `upstream` remote, last
changed 2017-10-29. The `asciiverse` branch starts from its `master` at
`dafa819`, the commit that put the game under the GPL.

## The releases

Upstream's history already holds the three releases from the original
home page, www.math.leidenuniv.nl/~mommen/scrap/ (gone; fetched from the
Wayback Machine's 2007-03-11 captures). Each source tarball was compared
file by file with its commit and is byte for byte identical, apart from
the two-line README.md upstream's first commit added. The commits are
tagged here:

| tag | commit | release | `scrap.tar.gz` sha256 |
|---|---|---|---|
| `10drl` | `b5b50aa` | Scrap, the Ten-Day Roguelike (2005-03-16) | `cc65aac6258e234d07135217089977ad9400ad191b3bd1de65044a7dc1134d95` |
| `x10drl` | `59d89e9` | Scrap, the Extended 10DRL (2006-10-26) | `abfb60340f9eb0489db94dd2d97d9b40109cf02aad62aa4d51e2cbba54321f6e` |
| `x10drl-1.1` | `7793cde` | Scrap, the Extended 10DRL 1.1 (2006-11-15) | `3d67915bcd0ee826ce1c29a96480ddfa1d7502c87fda10698cb2f83a9522e3fb` |

The tarballs came from `web.archive.org/web/20070311000000id_/http://www.math.leidenuniv.nl:80/~mommen/scrap/<10drl|x10drl|x10drl1_1>/scrap.tar.gz`.
The Windows zips beside them hold the same sources with a built
`scrap.exe` and PDCurses' `curses.dll`; they are not imported.

## Known patches

- `18c7284` (tag `aur/1.1-6`), by E5ten, from the Arch User Repository's
  `scrap` package: `#include <cstring>` in being.cpp, game.cpp, main.cpp
  and ui.cpp, without which current g++ does not build the game. The AUR
  ships it as a repacked tarball (`scrap.tar.xz`, sha256
  `0e8bc30cf201b8fcb490c599e2fdd4dcdf04ac2108e2e3f07102d5092bbce1f7`),
  which differs from the 1.1 release only by these four lines and a
  `Makefile` that is upstream's `makefile.linux`. No other distribution
  packages Scrap (Repology, 2026-10-17).

## Our changes

- Savefile in the player's data folder: `scrap.sav` was written to and
  read from the folder the game was started in, which for an installed
  game is its install folder. It is now in `$XDG_DATA_HOME/scrap` (else
  `~/.local/share/scrap`), made on first use, or `%APPDATA%\scrap` on
  Windows (`savefilename()` in game.cpp).
- Centred in the terminal: the game draws its 80x25 screen on a curses
  pad, and every key read shows it centred (`showfield()` in ui.cpp).
  A resize blanks the terminal and places the screen again; the game used
  to read KEY_RESIZE as an unknown key and stay in the top left corner.
  stdscr points at the pad while it exists, so the drawing code is as it
  was. The game's own check for a terminal of at least 80x25 at the start
  is unchanged; a terminal that shrinks later shows the top left part.
- Esc, which cancels, answers at once: ncurses' ESCDELAY is set to 25 ms
  instead of waiting a second for the rest of an escape sequence.
- A restored game keeps its own last target: `Game::operator=`, which puts
  the restored game in place of the running one, copied everything but
  `prevtarget`, so the running game's last target (an index into its own
  list of robots) carried over and could point past the end of the
  restored game's list. Found by reading the code.

## Packaging (new files)

- `asciiverse/build.sh` compiles the game into `out/scrap` with the
  compiler and curses from the environment; upstream's `makefile.linux`
  and `makefile.mingw` are left as they were. The only warnings are the
  2005 code passing string literals as `char *`, which the script mutes.
- `asciiverse/package.sh` (NetBSD games') packs the files listed in
  `asciiverse/archive/scrap.txt`: the binary, README.md, manual.txt and
  COPYING. Everything else is compiled in.
- `.github/workflows/release.yml`: static Linux in Alpine (x86_64,
  aarch64), macOS (x86_64, arm64) and Windows x86_64 (MinGW and PDCurses
  3.9), plus SHA256SUMS, on a tag.
- `asciiverse/record/`: `scrap.py` plays the game for the preview in
  `asciiverse/casts/scrap.cast` (fights, salvages, takes the exit),
  reading the screen through pyte (`rec.py`, from NetBSD games'); with
  `--soak` it plays any build for as long as asked, for test runs.

## Tested

Linux: glibc builds with g++ and clang++, and the static musl build from
Alpine 3.22, run in a pseudo-terminal at 80x25, 100x30 and 120x40 and
resized while playing (smaller than 80x25 shows the game's own request
for a bigger terminal, and the game starts once it is big enough). Save
and restore: the savefile lands in the data folder, is restored and then
deleted, and a second restore reports that there is none. An
AddressSanitizer and UBSan build was played for twenty minutes by the
recording driver in `--soak` mode (two runs of ten minutes: down to level
5, 36 wrecks salvaged, eight games lost and started again), and the
build before our changes took 132,000 random key presses, without a
report. Windows: cross-built with MinGW and PDCurses 3.9; not run (no
Wine here). macOS: not built here.

## Ours

- **How to play it, at the top of README.md.** A short note on installing and
  starting it with av, or from a release archive; the original text follows
  unchanged.
