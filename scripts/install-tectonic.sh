#!/usr/bin/env bash
set -euo pipefail

if command -v tectonic >/dev/null 2>&1 && tectonic --version >/dev/null 2>&1; then
  exit 0
fi

version="0.16.9"
arch="$(uname -m)"
case "$arch" in
  x86_64|amd64)
    asset="tectonic-${version}-x86_64-unknown-linux-musl.tar.gz"
    ;;
  aarch64|arm64)
    asset="tectonic-${version}-aarch64-unknown-linux-musl.tar.gz"
    ;;
  *)
    echo "[tectonic] unsupported architecture: $arch" >&2
    exit 1
    ;;
esac

url="https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40${version}/${asset}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl -fsSL "$url" -o "$tmp_dir/$asset"
tar -xzf "$tmp_dir/$asset" -C "$tmp_dir"
sudo install -m 755 "$tmp_dir/tectonic" /usr/local/bin/tectonic
