#!/bin/sh
# Builds Scrap into out/scrap. The compiler, flags and curses library come
# from the environment, so one script serves every target (see
# .github/workflows/release.yml):
#
#   asciiverse/build.sh                                       # Debian, Ubuntu
#   LIBS=-lncursesw LDFLAGS="-static -s" asciiverse/build.sh  # Alpine, static
#   LIBS=-lncurses asciiverse/build.sh                        # macOS
#   CXX=x86_64-w64-mingw32-g++ PDCURSES=/path/to/PDCurses-3.9 \
#     EXE=.exe asciiverse/build.sh                            # Windows
#
# Upstream's makefile.linux and makefile.mingw are kept as they were.
# The game has no data files: everything is compiled in.
set -eu
cd "$(dirname "$0")/.."
CXX="${CXX:-c++}"
CXXFLAGS="${CXXFLAGS:--O2}"
LDFLAGS="${LDFLAGS:-}"
LIBS="${LIBS:--lncursesw}"
EXE="${EXE:-}"
if [ -n "${PDCURSES:-}" ]; then
  CXXFLAGS="$CXXFLAGS -I$PDCURSES"
  LIBS="$PDCURSES/wincon/pdcurses.a"
  LDFLAGS="$LDFLAGS -static -s"
fi
mkdir -p out
# the 2005 sources pass string literals as char *; that is all the
# warnings say
$CXX $CXXFLAGS -Wno-write-strings *.cpp $LDFLAGS $LIBS -o "out/scrap$EXE"
echo "built scrap$EXE"
