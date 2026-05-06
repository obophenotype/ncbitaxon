#!/usr/bin/env bash
# Run the full NCBITaxon release as documented in README.md.
#
# Build steps run inside the ODK container via ./odk.sh.
# `gh` steps run on the host because they need your GitHub credentials
# (~/.config/gh), which aren't mounted into the container.
#
# Usage:
#   ./release.sh                 # tag = v<today>
#   ./release.sh v2026-05-05     # explicit tag
#
# ODK_DEBUG=yes is set so /usr/bin/time prints elapsed/peak-mem per phase.
set -euo pipefail

if [ ! -f ./odk.sh ] || [ ! -f ./Makefile ]; then
  echo "release.sh must be run from the repo root (where odk.sh and Makefile live)." >&2
  exit 1
fi

TAG="${1:-v$(date +%Y-%m-%d)}"

export ODK_DEBUG=yes

# Reset the consolidated per-target debug log once at the start.
# odk.sh appends to it across both make invocations below.
rm -f debug.log

echo ">>> [1/4] Building ontology: make clean all -B"
./odk.sh make clean all -B

echo ">>> [2/4] Building subsets: cd subsets && make all -B"
./odk.sh bash -c "cd subsets && make all -B"

ARTIFACTS=(
  ncbitaxon.json.gz
  ncbitaxon.obo
  ncbitaxon.obo.gz
  ncbitaxon.owl
  ncbitaxon.owl.gz
  subsets/taxslim-disjoint-over-in-taxon.owl
  subsets/taxslim.obo
  subsets/taxslim.owl
  subsets/taxslim.json
)

echo ">>> [3/4] Creating draft release $TAG"
gh release create "$TAG" --draft --title "$TAG" --notes ""

echo ">>> [4/4] Uploading artifacts to $TAG"
gh release upload "$TAG" "${ARTIFACTS[@]}"

echo ">>> Done. Review the draft on GitHub, then publish."
