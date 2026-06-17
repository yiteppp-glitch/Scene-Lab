#!/bin/zsh
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PORT=4177
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done
URL="http://127.0.0.1:$PORT/intro.html"
echo "Scene Lab 附件版启动中：$URL"
open "$URL"
python3 scene_lab_server.py --port "$PORT" --host 127.0.0.1 --directory "$DIR"
