#!/bin/zsh
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
ROOT="${0:A:h}"
LOGS="$ROOT/logs"
mkdir -p "$LOGS"

listening() { lsof -nP -iTCP:$1 -sTCP:LISTEN >/dev/null 2>&1 }

wait_for() {
  local port=$1 label=$2 tries=0
  until listening $port; do
    tries=$((tries + 1))
    if [ $tries -gt 120 ]; then
      echo "$label did not start. See $LOGS."
      return 1
    fi
    sleep 1
  done
  echo "$label is up on port $port."
}

cleanup() {
  echo
  echo "Stopping Valence..."
  trap - INT TERM HUP
  if [ -n "$FRONT_PID" ]; then
    pkill -P $FRONT_PID 2>/dev/null
    kill $FRONT_PID 2>/dev/null
    pkill -f "$ROOT/frontend/node_modules/.bin/vite" 2>/dev/null
  fi
  [ -n "$BACK_PID" ] && kill $BACK_PID 2>/dev/null
  sleep 2
  [ -n "$BACK_PID" ] && pkill -f "llama-server.*MentaLLaMA" 2>/dev/null
  exit 0
}
trap cleanup INT TERM HUP

echo "Valence"
echo "-------"

if listening 8000; then
  echo "Backend already running."
else
  cd "$ROOT/backend"
  .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 > "$LOGS/backend.log" 2>&1 &
  BACK_PID=$!
fi

if listening 5173; then
  echo "Frontend already running."
else
  cd "$ROOT/frontend"
  [ -d node_modules ] || npm install
  npm run dev > "$LOGS/frontend.log" 2>&1 &
  FRONT_PID=$!
fi

wait_for 8000 "Backend" || cleanup
wait_for 5173 "Frontend" || cleanup
wait_for 8081 "MentaLLaMA model server"

[ -z "$VALENCE_NO_OPEN" ] && open "http://localhost:5173/"
echo
echo "Valence is running at http://localhost:5173"
echo "Keep this window open. Press Ctrl+C or close it to stop everything."

while true; do
  sleep 3600 &
  wait $!
done
