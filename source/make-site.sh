#!/usr/bin/env bash
# Builds the publishable website in ~/TransportTycoon/site from the WebAssembly build + HD graphics.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/src/OpenTTD-15.3/build"
SITE="$ROOT/site"
HDTAR="$ROOT/assets/dl/OpenGFX2_HighDef-0.8.1.tar"
mkdir -p "$SITE"
cp "$BUILD/openttd.html" "$SITE/index.html"
cp "$BUILD/openttd.js" "$BUILD/openttd.wasm" "$BUILD/openttd.data" "$SITE/"
touch "$SITE/.nojekyll"

if [ ! -f "$SITE/hd/manifest.json" ]; then
  TMP="$(mktemp -d)"; mkdir -p "$SITE/hd"
  tar xf "$HDTAR" -C "$TMP"
  python3 - "$TMP"/OpenGFX2_HighDef-* "$SITE/hd" <<'PY'
import json, os, sys
src, dst = sys.argv[1], sys.argv[2]
PART = 45 * 1024 * 1024
files = []
for name in sorted(os.listdir(src)):
    if not (name.endswith(".grf") or name.endswith(".obg") or name == "license.txt"): continue
    data = open(os.path.join(src, name), "rb").read()
    parts = []
    for i in range(0, max(len(data), 1), PART):
        pn = "%s.%03d" % (name, i // PART)
        open(os.path.join(dst, pn), "wb").write(data[i:i + PART])
        parts.append(pn)
    files.append({"name": name, "size": len(data), "parts": parts})
json.dump({"set": "OpenGFX2 High Def 0.8.1", "files": files}, open(os.path.join(dst, "manifest.json"), "w"), indent=1)
print("HD parts:", sum(len(f["parts"]) for f in files))
PY
  rm -rf "$TMP"
fi
du -sh "$SITE"
