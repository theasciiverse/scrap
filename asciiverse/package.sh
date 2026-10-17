#!/bin/sh
# Packs the game into its archive for av (the script is NetBSD games',
# theasciiverse/netbsd-games): dist/<id>-<target>.tar.gz
# (.zip for Windows), from the list in asciiverse/archive/<id>.txt: one
# file per line, relative to the repo root, all placed side by side at the
# top of the archive; "src -> name" renames. Binaries listed as out/<name>
# get .exe on Windows.
#
#   asciiverse/package.sh x86_64-unknown-linux-musl
set -eu
cd "$(dirname "$0")/.."
target="$1"
case "$target" in *windows*) exe=.exe ;; *) exe= ;; esac
mkdir -p dist
for list in asciiverse/archive/*.txt; do
  id=$(basename "$list" .txt)
  stage="stage/$id"
  rm -rf "$stage" && mkdir -p "$stage"
  grep -v '^#' "$list" | while read -r src arrow name; do
    [ -n "$src" ] || continue
    case "$src" in out/*) [ -f "$src$exe" ] && src="$src$exe" ;; esac
    if [ "$arrow" = "->" ]; then cp "$src" "$stage/$name"; else cp "$src" "$stage/"; fi
  done
  if [ -n "$exe" ]; then
    (cd "$stage" && zip -qr "../../dist/$id-$target.zip" .)
  else
    tar -czf "dist/$id-$target.tar.gz" -C "$stage" .
  fi
done
ls dist
