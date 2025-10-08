#!/bin/zsh
# === ONLYMATT Gateway launcher (background version) ===
# Gère auto .venv, .env, kill ancien process, log et relance stable

cd ~/onlymatt-gateway || exit 1

LOG_FILE="gateway.log"
PORT=5059

# === Active environnement virtuel ===
if [ -d ".venv" ]; then
  source .venv/bin/activate
else
  echo "⚠️  Virtual env (.venv) not found. Run: python3 -m venv .venv && source .venv/bin/activate"
  exit 1
fi

# === Charge .env ===
export $(grep -v '^#' .env | xargs)

# === Kill ancienne instance ===
PID=$(lsof -ti:$PORT)
if [ -n "$PID" ]; then
  echo "🛑 Killing old process on port $PORT (PID: $PID)"
  kill -9 $PID
fi

# === Lancer en background avec log ===
echo "🚀 Launching ONLYMATT Gateway on port $PORT..."
nohup uvicorn gateway:app --host 0.0.0.0 --port $PORT --reload > "$LOG_FILE" 2>&1 &

sleep 2
NEW_PID=$(lsof -ti:$PORT)
if [ -n "$NEW_PID" ]; then
  echo "✅ Gateway is now running in background (PID: $NEW_PID)"
  echo "📝 Logs → tail -f $LOG_FILE"
else
  echo "❌ Failed to start Gateway. Check $LOG_FILE"
fi
