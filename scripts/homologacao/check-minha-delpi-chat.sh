#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "[ERRO] Defina TOKEN antes de rodar."
  echo "Exemplo: TOKEN=... ./scripts/homologacao/check-minha-delpi-chat.sh"
  exit 1
fi

echo "[1/10] Healthcheck público"
curl -fsS "$BASE_URL/apps/minha-delpi-ai/api/health" | python3 -m json.tool

echo "[2/10] Status LLM admin"
curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/apps/minha-delpi-ai/api/admin/llm/status" | python3 -m json.tool

echo "[3/10] Listar sessões"
curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/apps/minha-delpi-ai/api/chat/sessions" | python3 -m json.tool >/tmp/minha-delpi-chat-sessions.json

echo "[4/10] Criar sessão"
SESSION_ID="$(
  curl -fsS \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"Homologação MVP","context":"geral"}' \
    "$BASE_URL/apps/minha-delpi-ai/api/chat/sessions" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'
)"
echo "SESSION_ID=$SESSION_ID"

echo "[5/10] Busca knowledge"
curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"O que é a Minha DELPI?","limit":3}' \
  "$BASE_URL/apps/minha-delpi-ai/api/knowledge/search" | python3 -m json.tool

echo "[6/10] Tool autorizada"
curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tool":"get_current_user","arguments":{}}' \
  "$BASE_URL/apps/minha-delpi-ai/api/tools/execute" | python3 -m json.tool

echo "[7/10] Tool bloqueada/inexistente deve retornar 404"
HTTP_CODE="$(
  curl -s -o /tmp/minha-delpi-chat-tool-error.json -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"tool":"drop_database","arguments":{}}' \
    "$BASE_URL/apps/minha-delpi-ai/api/tools/execute"
)"
cat /tmp/minha-delpi-chat-tool-error.json | python3 -m json.tool
test "$HTTP_CODE" = "404"

echo "[8/10] Streaming chat"
curl -fsS -N \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Quem sou eu? Responda de forma objetiva.","context":"geral"}' \
  "$BASE_URL/apps/minha-delpi-ai/api/chat/sessions/$SESSION_ID/messages/stream" \
  | tee /tmp/minha-delpi-chat-stream.txt

grep -q "event: tool_calls" /tmp/minha-delpi-chat-stream.txt
grep -q "event: done" /tmp/minha-delpi-chat-stream.txt

echo "[9/10] Histórico persistido"
curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/apps/minha-delpi-ai/api/chat/sessions/$SESSION_ID/messages" | python3 -m json.tool

echo "[10/10] remoteEntry"
curl -fsSI "$BASE_URL/apps/minha-delpi-chat/assets/remoteEntry.js" | grep -i "content-type"

echo "[OK] Homologação HTTP concluída."
