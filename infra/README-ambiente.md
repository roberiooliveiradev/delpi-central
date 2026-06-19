# Ambiente Docker — desenvolvimento vs produção

Este diretório (`infra/`) concentra os compose e as variáveis compartilhadas pela plataforma.

## Arquivos principais

| Arquivo | Uso |
|---------|-----|
| `docker-compose.dev.yml` | Desenvolvimento local: hot-reload, Flask dev, profile `chat` / `vision` |
| `docker-compose.yml` | Produção: Gunicorn, imagens `*.prod`, logging limitado |
| `docker-compose.vision.yml` | **Override legado** — equivalente a `Dockerfile.dev` (desde jun/2026 visão já vem no dev) |
| `docker-compose.prod.vision.yml` | **Override** prod: `INSTALL_VISION_EXTRAS=true` no `Dockerfile.prod` |
| `.env.dev.example` | Modelo para copiar → `.env` no dia a dia |
| `.env.prod.example` | Modelo para servidor / CI de deploy |

```bash
# Desenvolvimento (a partir da raiz do monorepo ou de infra/)
cp infra/.env.dev.example infra/.env
docker compose -f infra/docker-compose.dev.yml --profile chat up -d

# Chat + rebuild explícito com extras de visão (opcional — dev já inclui EasyOCR/Docling)
./minha-delpi-ai-api/scripts/build_vision_profile.sh dev
```

O Compose lê **`infra/.env`** por padrão quando o comando é executado com `-f infra/docker-compose.*.yml`.

---

## Diferenças Docker: dev × prod (`minha-delpi-ai-api`)

| Aspecto | Dev (`Dockerfile.dev`) | Prod (`Dockerfile.prod`) |
|---------|------------------------|---------------------------|
| Servidor | Flask `flask run` | Gunicorn (2 workers, timeout 300s) |
| Código | Volume montado (`../minha-delpi-ai-api:/app`) | Copiado na imagem (imutável) |
| **Tesseract (OCR)** | `apt` + `por`/`eng` | `apt` + `por`/`eng` (alinhado) |
| **Python deps** | `requirements.txt` | `requirements.txt` (mesmo arquivo) |
| **EasyOCR / Docling** | Build via `docker_install_vision_extras.sh` + modelos em `/opt/delpi-vision/easyocr` | Só se `INSTALL_VISION_EXTRAS=true` no build (`Dockerfile.prod`) |
| **PaddleOCR** | Opcional — descomente em `requirements-vision.txt` + rebuild | Idem |
| Compose injeta `CHAT_DOCUMENT_VISION_*` | Sim (default `ENABLED=true`) | Sim (via `.env`; ver `.env.prod.example`) |
| Ollama / SearXNG | Dev: profile `chat` | Prod: Ollama; SearXNG opcional por env |

### Outra máquina ou deploy

1. **Git** traz código + exemplos de env; **não** traz `.env` nem imagens Docker.
2. Em cada máquina: `cp .env.*.example .env`, ajustar secrets, `docker compose build`.
3. Dados (Postgres, anexos, `metadata.documentVision`) vivem nos **volumes/DB**, não na imagem.
4. **EasyOCR/Docling** e **pesos EasyOCR** vêm no build (`Dockerfile.dev`); entrypoint não roda `pip install`. Rebuild: `./minha-delpi-ai-api/scripts/build_vision_profile.sh dev`. Doc: `minha-delpi-ai-api/docs/operations/vision-container-setup.md`.

---

## Variáveis por camada (organização)

| Seção no `.env.*.example` | Quem consome |
|---------------------------|--------------|
| Geral | Todos (timezone, URL pública) |
| Keycloak + DB | `keycloak`, `keycloak-db` |
| Postgres Core + Core API | `postgres-core`, `core-api` |
| Postgres Plugins | `postgres-plugins`, APIs de plugins |
| Portal (Vite) | Build do `portal` |
| **Minha DELPI AI API** | `minha-delpi-ai-api` — LLM, RAG, chat, **visão/OCR** |
| Ollama | `ollama`, embeddings e chat |
| Pesquisa web | Tavily/Serper/Bing/SearXNG |
| APIs legadas | `api-delpi`, planilhas Google, etc. |

Variáveis só no **código** (sem entrada no compose) ainda podem ser definidas no `.env`; o container as recebe se você as adicionar ao bloco `environment:` ou usar `env_file:`.

Documentação detalhada da API de chat: `minha-delpi-ai-api/README.md`.

---

## Pós-deploy api-delpi → chat (OpenAPI sync)

Após deploy de nova versão da `api-delpi`, rode o job que reimporta o schema no provider do chat, reindexa embeddings e regenera o catálogo MD:

```bash
# Stack local (compose prod ou dev com containers padrão)
./scripts/homologacao/sync-api-delpi-openapi.sh

# Servidor com gateway HTTPS
BASE_URL=https://seu-dominio ./scripts/homologacao/sync-api-delpi-openapi.sh
```

| Variável | Default | Descrição |
|----------|---------|-----------|
| `BASE_URL` | `http://localhost` | Gateway (health em `/apps/api-delpi/health`) |
| `CHAT_API_CONTAINER` | `delpi-minha-delpi-ai-api` | Container onde roda o sync |
| `WAIT_SECONDS` | `180` | Timeout aguardando api-delpi |
| `PROVIDER_KEY` | `api-delpi` | Provider cadastrado no admin |

CI manual: `.github/workflows/sync-api-delpi-openapi.yml` (Environment `homolog` / `prod` com secrets SSH).

Procedimento completo: `api-delpi/docs/api/12-procedimento-reimport-openapi.md`.

---

## Visão de documentos (Onda 13)

| Variável | Dev (compose default) | Prod (recomendado no `.env`) |
|----------|----------------------|------------------------------|
| `CHAT_VISION_EXTRAS_WARN` | `true` | `true` — aviso se extras não estiverem na imagem |
| `CHAT_DOCUMENT_VISION_ENABLED` | `true` | `true` se usar OCR/anexos/desenhos |
| `CHAT_DOCUMENT_VISION_BACKEND` | `auto` | `auto` (ou `tesseract` / `docling` com extras na imagem) |
| `CHAT_DOCUMENT_VISION_OLLAMA_MODEL` | `qwen2.5vl:7b` | `qwen2.5vl:7b` com `ollama_vlm` ou fallback em `auto` (`CHAT_DOCUMENT_VISION_AUTO_VLM_FALLBACK=true`) |
| `CHAT_RESPONSE_MODE_*` | modos composer | `FAST_MODEL=1.5b`, `OLLAMA_MODEL=3b` para normal/pensador |

Backend `docling` e OCR regional `easyocr` exigem `requirements-vision.txt` na imagem (dev já inclui). Verificação: `python3 scripts/check_vision_profile_deps.py` dentro do container.

Guia completo: `minha-delpi-ai-api/docs/operations/vision-container-setup.md`.

---

## Biblioteca PDF de desenhos (FILESERVER dev)

O `api-delpi` em dev lê PDFs do **FILESERVER** (`X:\DESENHOS DELPI EM PDF`), não da pasta gitignored `minha-delpi-ai-api/desenhos/`.

| Variável | Onde | Default dev |
|----------|------|-------------|
| `DRAWING_PDF_FILESERVER_HOST_PATH` | `infra/.env` / `.env.local` | `/mnt/x/DESENHOS DELPI EM PDF` |
| `DRAWING_PDF_LIBRARY_DIR` | container api-delpi | `/drawing-pdfs` |

**Montar X: no WSL** (se `/mnt/x` estiver vazio):

```bash
sudo mkdir -p /mnt/x && sudo mount -t drvfs X: /mnt/x
ls "/mnt/x/DESENHOS DELPI EM PDF" | wc -l
```

**Aplicar no Docker:**

```bash
# infra/.env.local — ver env.local.example
DRAWING_PDF_FILESERVER_HOST_PATH=/mnt/x/DESENHOS DELPI EM PDF

docker compose -f infra/docker-compose.dev.yml up -d --force-recreate api-delpi
docker exec delpi-api-delpi ls /drawing-pdfs | wc -l
```

Catálogo: `GET /apps/api-delpi/products/drawings?page_size=5` (via gateway).

Doc: `api-delpi/docs/api/14-desenhos-pdf.md`.

---

## Ferramentas do chat (default ligadas)

Dev e produção injetam no `minha-delpi-ai-api` o **pacote padrão** de ferramentas do pipeline. Valores abaixo são os defaults do Compose quando a variável **não** está no `.env`:

| Variável | Dev | Prod | Função |
|----------|-----|------|--------|
| `CHAT_TOOL_ROUTER_ENABLED` | `true` | `false` | Router LLM para tools/actions |
| `CHAT_AGENTIC_LOOP_ENABLED` | `true` | `false` | Loop agentic (planner + catálogo) |
| `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` | `12` | `12` | Teto de actions no catálogo agentic |
| `CHAT_MULTI_ACTION_ENABLED` | `true` | `true` | Várias external actions por turno |
| `CHAT_PAGINATION_AUTO_FETCH_ENABLED` | `true` | `true` | Busca páginas extras quando pedido |
| `CHAT_RAG_HYBRID_ENABLED` | `true` | `true` | RAG vetor + keyword |
| `CHAT_RAG_RERANK_ENABLED` | `true` | `true` | Boost por overlap de keywords |
| `CHAT_WEB_SEARCH_ENABLED` | `true` | `true` | Pesquisa web (SearXNG/Tavily/…) |
| `CHAT_DEFAULT_SQL_AUTHORING_SKILL` | `true` | `true` | Skill `sql` no chat sem agente |
| `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL` | `true` | `true` | Skill `company-knowledge` (RAG global) |
| `CHAT_NATIVE_TOOL_CALLING_ENABLED` | `false` | `false` | Piloto tools nativas LLM (opt-in) |

**Desligar só o necessário:** defina `false` no `infra/.env` (ex.: `CHAT_AGENTIC_LOOP_ENABLED=false` em CPU apertada). O código (`settings.py`) usa os mesmos defaults quando a API roda **fora** do Docker.

**Prioridade:** o pipeline do chat lê **sempre** as variáveis de ambiente (`CHAT_*`, `RAG_*`, `EXTERNAL_ACTION_*`). No boot do container, `docker-entrypoint.sh` executa `flask sync-chat-intelligence-env` para espelhar o `.env` no painel admin (Postgres). Toggles salvos só no painel **não** alteram o runtime até mudar o `.env` e recriar o serviço. Para pular o sync: `SKIP_CHAT_INTELLIGENCE_SYNC=true`.

Conferir no container:

```bash
docker exec delpi-minha-delpi-ai-api printenv | grep -E '^(CHAT_TOOL_ROUTER|CHAT_AGENTIC|CHAT_RAG_HYBRID|CHAT_DEFAULT_)'
```

Após alterar `.env`: `docker compose … up -d --force-recreate minha-delpi-ai-api`.

---

## Checklist deploy produção

- [ ] `cp infra/.env.prod.example infra/.env` e trocar todos os `CHANGE_ME`
- [ ] `KEYCLOAK_ISSUER` / `PUBLIC_BASE_URL` com URL HTTPS real (gateway)
- [ ] `docker compose -f infra/docker-compose.yml build` na máquina de deploy
- [ ] `CHAT_DOCUMENT_VISION_ENABLED=true` (padrão no `.env.prod.example`)
- [ ] Docling opcional: `INSTALL_VISION_EXTRAS=true` antes do `build` + `CHAT_DOCUMENT_VISION_BACKEND=docling`
- [ ] `ollama pull` dos modelos de chat e embedding (`OLLAMA_MODEL`, `EMBEDDING_MODEL`)
- [ ] Não commitar `.env` (já no `.gitignore`)

### Build prod com Docling (opcional)

```bash
INSTALL_VISION_EXTRAS=true docker compose -f infra/docker-compose.yml build minha-delpi-ai-api
```
