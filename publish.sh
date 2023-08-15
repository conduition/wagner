#!/bin/bash

set -e

[ -f .env ] && source .env

tempdir="$(mktemp -d)"
trap "rm -r '$tempdir'" exit
python3 setup.py sdist --dist-dir "$tempdir"

filename="$(realpath $tempdir/*)"
version="$(basename "$filename" | sed 's/^wagner-//' | sed 's/\.tar\.gz//')"

read -p "Publish wagner v${version}? (type 'yes')> " answer
if [[ "$answer" != "yes" ]]; then
  exit
fi

curl -v -X POST https://upload.pypi.org/legacy/ \
  --user "__token__:$PYPI_TOKEN" \
  -F ":action=file_upload" \
  -F protocol_version=1 \
  -F content="@$filename" \
  -F filetype=sdist \
  -F pyversion=source \
  -F sha256_digest="$(sha256sum "$filename" | head -c 64)" \
  -F metadata_version="2.1" \
  -F name=wagner \
  -F version="$version" \
  -F summary="Python implementation of Wagner's Algorithm for the Generalized Birthday Problem." \
  -F description="$(cat README.md)" \
  -F description_content_type="text/markdown; charset=UTF-8; variant=GFM" \
  -F keywords="birthday,musig,attack,wagner,generalized birthday problem,k-sum,k sum" \
  -F author="conduition" \
  -F author_email="conduition@proton.me" \
  -F home_page="https://github.com/conduition/wagner"
