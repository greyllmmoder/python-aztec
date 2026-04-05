#!/usr/bin/env bash
set -euo pipefail

repo="${1:-greyllmmoder/python-aztec}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2
  exit 1
fi

# create or update labels
upsert() {
  local name="$1" color="$2" desc="$3"
  gh label create "$name" --repo "$repo" --color "$color" --description "$desc" --force >/dev/null
}

upsert "bug" "d73a4a" "Something is broken"
upsert "enhancement" "a2eeef" "New feature or request"
upsert "good first issue" "7057ff" "Good for first-time contributors"
upsert "help wanted" "008672" "Maintainer help is welcome"
upsert "breaking" "b60205" "Breaking behavior/API change"
upsert "needs repro" "fbca04" "Needs a minimal reproducible case"

echo "Labels synced for $repo"
