#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TOKEN="${TOKEN:-}"

API_BASE_URL="${BASE_URL}/apps/minha-delpi-ai/api"
REMOTE_ENTRY_URL="${BASE_URL}/apps/minha-delpi-chat/assets/remoteEntry.js"

fail() {
  echo "[ERRO] $*" >&2
  exit 1
}

ok() {
  echo "[OK] $*"
}

warn() {
  echo "[WARN] $*" >&2
}

require_token() {
  if [ -z "$TOKEN" ]; then
    fail "TOKEN não definido. Exporte TOKEN antes de rodar o script."
  fi
}

echo "== Minha DELPI Chat — Homologação Prod =="
echo "BASE_URL=${BASE_URL}"
echo

echo "1) Healthcheck backend"
HEALTH_FILE="/tmp/minha-delpi-chat-health.json"

curl -fsS "${API_BASE_URL}/health" > "$HEALTH_FILE"
python3 -m json.tool "$HEALTH_FILE" >/dev/null

HEALTH_STATUS="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status"))' "$HEALTH_FILE")"

if [ "$HEALTH_STATUS" != "ok" ]; then
  fail "Healthcheck não retornou status=ok"
fi

ok "Backend saudável"

echo
echo "2) remoteEntry.js"
REMOTE_HEADERS_FILE="/tmp/minha-delpi-chat-remote-entry.headers"

curl -fsSI "$REMOTE_ENTRY_URL" > "$REMOTE_HEADERS_FILE"

CONTENT_TYPE="$(grep -i '^content-type:' "$REMOTE_HEADERS_FILE" || true)"

if ! echo "$CONTENT_TYPE" | grep -qi 'javascript'; then
  warn "Content-Type não parece JavaScript: ${CONTENT_TYPE}"
fi

ok "remoteEntry.js acessível"

echo
echo "3) Rotas autenticadas"
require_token
ok "TOKEN definido"

echo
echo "4) Status LLM"
LLM_FILE="/tmp/minha-delpi-chat-llm-status.json"

curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  "${API_BASE_URL}/admin/llm/status" \
  > "$LLM_FILE"

python3 -m json.tool "$LLM_FILE"

PROVIDER="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("provider"))' "$LLM_FILE")"

if [ "$PROVIDER" != "ollama" ] && [ "$PROVIDER" != "vllm" ]; then
  fail "Provider inválido: $PROVIDER"
fi

ok "Provider LLM: $PROVIDER"

echo
echo "5) System check"
SYSTEM_FILE="/tmp/minha-delpi-chat-system-check.json"

curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  "${API_BASE_URL}/admin/system-check" \
  > "$SYSTEM_FILE"

python3 -m json.tool "$SYSTEM_FILE"

SYSTEM_STATUS="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status"))' "$SYSTEM_FILE")"

if [ "$SYSTEM_STATUS" != "ok" ]; then
  fail "System check não está OK: $SYSTEM_STATUS"
fi

ok "System check OK"

echo
echo "6) Métricas administrativas"
METRICS_FILE="/tmp/minha-delpi-chat-metrics.json"

curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  "${API_BASE_URL}/admin/metrics/summary" \
  > "$METRICS_FILE"

python3 -m json.tool "$METRICS_FILE" >/dev/null

python3 -c '
import json
import sys

data = json.load(open(sys.argv[1]))

required = [
    "sessions",
    "messages",
    "knowledgeDocuments",
    "activeKnowledgeDocuments",
    "knowledgeChunks",
    "auditLogs",
    "recentToolCalls24h",
    "recentErrors24h",
]

missing = [key for key in required if key not in data]

if missing:
    raise SystemExit("Campos ausentes em metrics/summary: " + ", ".join(missing))
' "$METRICS_FILE"

ok "Métricas admin OK"

echo
echo "7) Criar sessão"
SESSION_FILE="/tmp/minha-delpi-chat-session.json"

curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Homologação automática","context":"geral"}' \
  "${API_BASE_URL}/chat/sessions" \
  > "$SESSION_FILE"

python3 -m json.tool "$SESSION_FILE"

SESSION_ID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("id"))' "$SESSION_FILE")"

if [ -z "$SESSION_ID" ] || [ "$SESSION_ID" = "None" ]; then
  fail "Sessão não retornou id"
fi

ok "Sessão criada: $SESSION_ID"

echo
echo "8) Streaming"
STREAM_FILE="/tmp/minha-delpi-chat-stream.out"

curl -fsS -N \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Responda em uma frase: o que é a Minha DELPI?","context":"geral"}' \
  "${API_BASE_URL}/chat/sessions/${SESSION_ID}/messages/stream" \
  > "$STREAM_FILE"

cat "$STREAM_FILE"

if ! grep -q '^event: sources' "$STREAM_FILE"; then
  warn "Streaming não retornou event: sources"
fi

grep -q '^event: token' "$STREAM_FILE" || fail "Streaming não retornou event: token"
grep -q '^event: done' "$STREAM_FILE" || fail "Streaming não retornou event: done"

ok "Streaming OK"

echo
echo "9) Histórico da sessão"
MESSAGES_FILE="/tmp/minha-delpi-chat-messages.json"

curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  "${API_BASE_URL}/chat/sessions/${SESSION_ID}/messages" \
  > "$MESSAGES_FILE"

python3 -m json.tool "$MESSAGES_FILE" >/dev/null
ok "Histórico acessível"

echo
echo "10) Tool inexistente deve retornar erro padronizado"
TOOL_FILE="/tmp/minha-delpi-chat-tool-error.json"

TOOL_HTTP_CODE="$(curl -sS -o "$TOOL_FILE" -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tool":"drop_database","arguments":{}}' \
  "${API_BASE_URL}/tools/execute")"

python3 -m json.tool "$TOOL_FILE"

if [ "$TOOL_HTTP_CODE" != "404" ]; then
  fail "Tool inexistente deveria retornar 404, retornou ${TOOL_HTTP_CODE}"
fi

TOOL_ERROR_CODE="$(python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); print(data["errors"][0]["code"])' "$TOOL_FILE")"

if [ "$TOOL_ERROR_CODE" != "tool.not_found" ]; then
  fail "Código esperado tool.not_found, recebido ${TOOL_ERROR_CODE}"
fi

ok "Erro padronizado de tool inexistente OK"

echo
echo "== Resultado =="
ok "Homologação automática concluída com sucesso"
