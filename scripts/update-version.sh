#!/bin/bash

TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")

MANIFEST=custom_components/neviweb130/manifest.json
jq --arg v "${TAG#v}" ".version = \$v" $MANIFEST > $MANIFEST-tmp
mv $MANIFEST-tmp $MANIFEST

sed -i -E "s/^version\s*=.*/version = \"${TAG#v}\"/" pyproject.toml
