#!/usr/bin/env bash
# Re-sync the static research survey from Roman's repo into public/survey/.
#
# The survey (https://github.com/r0m4k/maritime-ai-survey) is a standalone
# static site (vanilla HTML/CSS/JS posting to a Google Apps Script). We serve a
# COPY of it at laytimely.com/survey so it lives under our domain without
# pulling a second toolchain into this app. That copy is the tradeoff: when
# Roman ships survey changes, run this to pull them in, then commit.
#
# Usage:  bash apps/web/scripts/sync-survey.sh
set -euo pipefail

RAW="https://raw.githubusercontent.com/r0m4k/maritime-ai-survey/main"
DEST="$(cd "$(dirname "$0")/../public/survey" && pwd)"

FILES=(
  index.html
  styles.css
  survey.js
  questions.js
  config.js
  assets/logo.png
  assets/laytimely-logo.jpg
  assets/photography/hero-landing.jpg
)

echo "Syncing survey into $DEST"
for f in "${FILES[@]}"; do
  mkdir -p "$DEST/$(dirname "$f")"
  curl -fsS "$RAW/$f" -o "$DEST/$f"
  echo "  ok  $f ($(wc -c < "$DEST/$f")B)"
done
echo "Done. Review with 'git diff', then commit."
