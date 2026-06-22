# Ambiente Docker — desenvolvimento vs produção

Este diretório (`infra/`) concentra os compose e as variáveis compartilhadas pela plataforma.

## Arquivos principais

| Arquivo | Uso |
|---------|-----|
| `docker-compose.dev.yml` | Desenvolvimento local: hot-reload, Flask dev, profile `chat` / `vision` |
| `docker-compose.yml` | Produção: Gunicorn, imagens `*.prod`, logging limitado |
| `docker-compose.vision.yml` | **Override legado** — equivalente a `Dockerfile.dev` (desde jun/2026 visão já vem no dev) |
| `docker-compose.prod.vision.yml` | **Override legado** prod — redundante; compose base já inclui visão |
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
| **EasyOCR / Docling** | Build via `docker_install_vision_extras.sh` + modelos em `/opt/delpi-vision/easyocr` | Idem (default no `Dockerfile.prod`) |
| **PaddleOCR** | Opcional — descomente em `requirements-vision.txt` + rebuild | Idem |
| Compose injeta `CHAT_DOCUMENT_VISION_*` | Sim (default `ENABLED=true`) | Sim (via `.env`; ver `.env.prod.example`) |
| Ollama / SearXNG | Dev: profile `chat` | Prod: Ollama; SearXNG opcional por env |

### Outra máquina ou deploy

1. **Git** traz código + exemplos de env; **não** traz `.env` nem imagens Docker.
2. Em cada máquina: `cp .env.*.example .env`, ajustar secrets, `docker compose build`.
3. Dados (Postgres, anexos, `metadata.documentVision`) vivem nos **volumes/DB**, não na imagem.
4. **Anexos de chat** e **fontes de projeto** (upload) ficam em `${DELPI_DATA_HOST_DIR:-$HOME/.delpi}/chat-attachments` e `.../chat-sources` no host — montados em `/data/delpi/...` no container (`CHAT_ATTACHMENT_STORAGE_PATH` / `CHAT_SOURCE_STORAGE_PATH`). Recriar o container **não** apaga esses arquivos; anexos antigos gravados em `/tmp/minha-delpi-chat-attachments` precisam ser reenviados.
5. **EasyOCR/Docling** e **pesos EasyOCR** vêm no build (`Dockerfile.dev` / `Dockerfile.prod`); entrypoint não roda `pip install`. Rebuild: `./minha-delpi-ai-api/scripts/build_vision_profile.sh [dev|prod]`. Doc: `minha-delpi-ai-api/docs/operations/vision-container-setup.md`.

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
| `CHAT_RESPONSE_MODE_*` | modos composer — ver tabela abaixo | Prod CPU: alinhar ao preset `operational_cpu` se `.env` legado |

### LLM chat — defaults compose (jun/2026)

Injetados em `docker-compose.dev.yml` e `docker-compose.yml` quando ausentes no `.env`:

| Variável | Default compose | Papel |
|----------|-----------------|-------|
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | Modelo base (turnos fora dos modos) |
| `CHAT_LLM_LATENCY_PROFILE` | `operational_cpu` | Preset 320 tokens / ctx 1024 |
| `LLM_MAX_TOKENS` | `320` | Teto global (override do preset) |
| `OLLAMA_NUM_CTX` | `1024` | Contexto global |
| `CHAT_RESPONSE_MODES_ENABLED` | `true` | Seletor Rápida/Normal/Pensador |
| `CHAT_RESPONSE_MODE_FAST_*` | 96 tok / ctx 512 | Modo Rápida (fallback LLM; prosa usual via commentary direct — ver `chat-response-modes.md`) |
| `CHAT_RESPONSE_MODE_NORMAL_*` | 320 tok / ctx 1024 | Modo Normal |
| `CHAT_RESPONSE_MODE_THINKER_*` | 512 tok / ctx 1536 | Modo Pensador |

Documentação: [`chat-response-modes.md`](../minha-delpi-ai-api/docs/architecture/chat-response-modes.md), changelog [`2026-06-playbook-19-prosa-latencia-analyser.md`](../minha-delpi-ai-api/docs/changelog/2026-06-playbook-19-prosa-latencia-analyser.md).

**Prod srv-api:** `.env` com `OLLAMA_MODEL=3b` e ctx 2048 **não** herda estes defaults — atualizar explicitamente ou aceitar latência maior. Após mudança: `docker compose … up -d --force-recreate minha-delpi-ai-api`.

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

## Anexos e fontes persistentes (chat)

Uploads de conversa e arquivos de fonte de projeto **devem** sobreviver a rebuild do container.

| Variável | Default no container | Descrição |
|----------|----------------------|-----------|
| `DELPI_DATA_HOST_DIR` | `${HOME}/.delpi` no host | Pasta base **fora do repositório** |
| `CHAT_ATTACHMENT_STORAGE_PATH` | `/data/delpi/chat-attachments` | Anexos de sessão + cache `drawing-library-cache` |
| `CHAT_SOURCE_STORAGE_PATH` | `/data/delpi/chat-sources` | PDFs/docs enviados como fonte de projeto ou agente |

Volumes (prod e dev): `${DELPI_DATA_HOST_DIR}/chat-attachments` e `.../chat-sources` montados nos paths acima.

```bash
# Ajuste opcional em infra/.env
DELPI_DATA_HOST_DIR=/var/lib/delpi

docker compose -f infra/docker-compose.yml up -d --force-recreate minha-delpi-ai-api
ls -la ~/.delpi/chat-attachments   # ou o caminho configurado
```

Anexos gravados antes desta configuração (path `/tmp/minha-delpi-chat-attachments` no container) precisam ser **reenviados**.

Guia completo: [`minha-delpi-ai-api/docs/operations/chat-attachment-storage.md`](../minha-delpi-ai-api/docs/operations/chat-attachment-storage.md).

---

## Produção CPU (srv-api, 4 vCPU · ~15 GB)

Perfil enxuto: **`infra/.env.prod.cpu.example`** — só tuning do host e overrides `false` (router, agentic, semantic rank, colunas R16, LanguageTool). O restante vem do default do `docker-compose.yml` prod.

Catálogo completo (tudo ligado): **`infra/.env.prod.example`**.

---

## Ferramentas do chat (default ligadas)

Dev e produção injetam no `minha-delpi-ai-api` o **pacote padrão** de ferramentas do pipeline. Valores abaixo são os defaults do Compose quando a variável **não** está no `.env`:

| Variável | Dev | Prod | Função |
|----------|-----|------|--------|
| `CHAT_TOOL_ROUTER_ENABLED` | `true` | `true` | Router LLM para tools/actions |
| `CHAT_AGENTIC_LOOP_ENABLED` | `true` | `true` | Loop agentic (planner + catálogo) |
| `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` | `12` | `12` | Teto de actions no catálogo agentic |
| `CHAT_MULTI_ACTION_ENABLED` | `true` | `true` | Várias external actions por turno |
| `CHAT_PAGINATION_AUTO_FETCH_ENABLED` | `true` | `true` | Busca páginas extras quando pedido |
| `CHAT_RAG_HYBRID_ENABLED` | `true` | `true` | RAG vetor + keyword |
| `CHAT_RAG_RERANK_ENABLED` | `true` | `true` | Boost por overlap de keywords |
| `CHAT_WEB_SEARCH_ENABLED` | `true` | `true` | Pesquisa web (SearXNG/Tavily/…) |
| `CHAT_DEFAULT_SQL_AUTHORING_SKILL` | `true` | `true` | Skill `sql` no chat sem agente |
| `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL` | `true` | `true` | Skill `company-knowledge` (RAG global) |
| `CHAT_NATIVE_TOOL_CALLING_ENABLED` | `true` | `true` | Piloto tools nativas LLM |
| `CHAT_TYPING_CORRECTION_FUZZY_ENABLED` | `true` | `true` | Fuzzy no corretor do composer (P14) |
| `CHAT_TEXT_CORRECTION_SPELL_CHECK_ENABLED` | `true` | `true` | Preflight LanguageTool na correção textual |
| `CHAT_PRESENTATION_COLUMN_LABEL_DISCOVERY_ENABLED` | `true` | `true` | Descoberta LLM de rótulos de coluna |
| `CHAT_LEARNING_AUTO_APPROVE_ENABLED` | `true` | `true` | Auto-aprovar termos aprendidos |
| `CHAT_DOCUMENT_VISION_PADDLE_USE_GPU` | `false` | `false` | GPU no PaddleOCR (**única exceção**) |

**Desligar só o necessário:** defina `false` no `infra/.env` (ex.: `CHAT_AGENTIC_LOOP_ENABLED=false` em CPU apertada). Exceção intencional: `CHAT_DOCUMENT_VISION_PADDLE_USE_GPU` permanece `false` (CPU/WSL).

**Prioridade:** o pipeline do chat lê **sempre** as variáveis de ambiente (`CHAT_*`, `RAG_*`, `EXTERNAL_ACTION_*`). No boot do container, `docker-entrypoint.sh` executa `flask sync-chat-intelligence-env` para espelhar o `.env` no painel admin (Postgres). Toggles salvos só no painel **não** alteram o runtime até mudar o `.env` e recriar o serviço. Para pular o sync: `SKIP_CHAT_INTELLIGENCE_SYNC=true`.

Conferir no container:

```bash
docker exec delpi-minha-delpi-ai-api printenv | grep -E '^(CHAT_TOOL_ROUTER|CHAT_AGENTIC|CHAT_RAG_HYBRID|CHAT_DEFAULT_)'
```

Após alterar `.env`: `docker compose … up -d --force-recreate minha-delpi-ai-api`.

### LanguageTool (correção textual)

Serviço `languagetool` (`erikvl87/languagetool`) incluído em **dev** e **prod**. Usado apenas pela skill «corrija este texto» — **não** pelo corretor de typos operacionais do composer (Playbook 14).

| Variável | Default compose | Efeito |
|----------|-----------------|--------|
| `CHAT_TEXT_CORRECTION_SPELL_CHECK_ENABLED` | `true` | Liga preflight LanguageTool no turno de correção |
| `CHAT_LANGUAGETOOL_BASE_URL` | `http://languagetool:8010` | URL interna na rede Docker |
| `CHAT_LANGUAGETOOL_TIMEOUT_SECONDS` | `4` | Timeout HTTP por turno |
| `CHAT_LANGUAGETOOL_LANGUAGE` | `pt-BR` | Idioma enviado ao `/v2/check` |

**Prod:** o serviço **não** expõe porta pública — só `minha-delpi-ai-api` acessa na rede interna. Reservar ~2,5 GB RAM.

```bash
# Deploy / atualização
docker compose -f infra/docker-compose.yml pull languagetool
docker compose -f infra/docker-compose.yml up -d --force-recreate languagetool minha-delpi-ai-api

# Validar (na máquina de deploy, se 8010 não estiver exposto — use exec na API)
docker exec delpi-minha-delpi-ai-api printenv | grep CHAT_TEXT_CORRECTION_SPELL
curl -sf -X POST http://127.0.0.1:8010/v2/check -d 'language=pt-BR' -d 'text=teste'  # só se porta exposta para debug
```

Config declarativa (regras ignoradas, siglas ERP): `minha-delpi-ai-api/app/content/pt-BR/assistant/text_correction_spell_check.json`.

---

## Checklist deploy produção

- [ ] `cp infra/.env.prod.example infra/.env` e trocar todos os `CHANGE_ME`
- [ ] `KEYCLOAK_ISSUER` / `PUBLIC_BASE_URL` com URL HTTPS real (gateway)
- [ ] `docker compose -f infra/docker-compose.yml build` na máquina de deploy (EasyOCR/Docling já na imagem)
- [ ] `CHAT_DOCUMENT_VISION_ENABLED=true` (padrão no `.env.prod.example`)
- [ ] `CHAT_DOCUMENT_VISION_BACKEND=docling` ou `auto` conforme política do servidor
- [ ] `ollama pull` dos modelos de chat e embedding (`OLLAMA_MODEL`, `EMBEDDING_MODEL`)
- [ ] `CHAT_TEXT_CORRECTION_SPELL_CHECK_ENABLED=true` + serviço `languagetool` no ar (opcional; ~2,5 GB RAM)
- [ ] Não commitar `.env` (já no `.gitignore`)

### Rebuild prod com visão (já incluída no compose padrão)

```bash
./minha-delpi-ai-api/scripts/build_vision_profile.sh prod
```
