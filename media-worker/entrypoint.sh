#!/bin/sh
set -e
echo "media-worker: ffmpeg $(ffmpeg -version | head -n1)"
echo "Replace this entrypoint with your media job consumer (Arq/Temporal worker)."
exec sleep infinity
