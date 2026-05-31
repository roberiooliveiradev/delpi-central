#!/usr/bin/env bash
# Validação — placeholder «DELPI Conexões Elétricas» (MFE + conteúdo + bundle opcional)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="${PYTHONPATH:-$ROOT}"

PY="${PYTHON:-python3}"
if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
fi

echo "== Placeholder pesquisa web — smoke (JSON + follow-up) =="
"$PY" scripts/smoke_shortcut_placeholders.py

echo ""
echo "== Placeholder pesquisa web — testes unitários web search =="
"$PY" -m pytest \
  tests/unit/application/services/test_chat_web_search_follow_up_service.py \
  tests/unit/application/services/test_chat_web_search_research_activity_service.py \
  -q

CHAT_PLUGIN="${REPO_ROOT}/plugins/minha-delpi-chat"
if [[ -f "$CHAT_PLUGIN/package.json" ]]; then
  echo ""
  echo "== Placeholder pesquisa web — Vitest MFE =="
  (cd "$CHAT_PLUGIN" && npm test -- --run src/ui/chatShortcutPrompt.test.ts)
fi

CONTAINER="${MFE_CONTAINER_NAME:-delpi-minha-delpi-chat}"
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then
  echo ""
  echo "== Placeholder pesquisa web — bundle no container $CONTAINER =="
  if docker exec "$CONTAINER" sh -c \
    'grep -rl "DELPI Conexões Elétricas" /usr/share/nginx/html/assets/*.js 2>/dev/null | head -1'; then
    if docker exec "$CONTAINER" sh -c \
      'grep -r "manual WEG CFW500" /usr/share/nginx/html 2>/dev/null'; then
      echo "FAIL bundle ainda contém manual WEG CFW500" >&2
      exit 1
    fi
    echo "OK bundle MFE sem exemplo legado WEG/CFW500"
  else
    echo "WARN bundle sem string DELPI — rebuild: docker compose -f infra/docker-compose.dev.yml build minha-delpi-chat" >&2
  fi
fi

echo ""
echo "Validação placeholder pesquisa web: concluída."
