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

**Importante:** após deploy da api-delpi, reinicie o processo/container antes do sync — o OpenAPI (`x-delpi`, `presentation.strategy`) fica em cache no worker até o restart. Sem isso o chat pode persistir `delpiMetadata` desatualizado.

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
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | `qwen2.5:1.5b` (igual dev; override no `.env` se srv-api usar 3b) |
| `CHAT_LLM_LATENCY_PROFILE` | `operational_cpu` | Preset 320 tokens / ctx 1024 |
| `LLM_MAX_TOKENS` | `320` | Teto global (override do preset) |
| `LLM_TEMPERATURE` | `0.2` | Igual dev |
| `OLLAMA_NUM_CTX` | `1024` | Contexto global |
| `MAX_CONTEXT_CHUNKS` / `MAX_CONTEXT_CHARS` | `6` / `9000` | Igual dev (menos RAG = menos latência) |
| `CHAT_FAST_PATH_MAX_CHARS` | `48` | Igual dev |
| `CHAT_DIRECT_RESPONSE_STREAM_*` | `4` chars / `0` ms | Sem delay artificial (prod antigo: 2/45) |
| `CHAT_RESPONSE_MODES_ENABLED` | `true` | Seletor Rápida/Normal/Pensador |
| `CHAT_RESPONSE_MODE_FAST_*` | 96 tok / ctx 512 | Modo Rápida |
| `CHAT_RESPONSE_MODE_NORMAL_*` | 1.5b, 256 tok, ctx 1536 | Modo Normal |
| `CHAT_RESPONSE_MODE_THINKER_*` | 3b, 512 tok, ctx 2048 | Modo Pensador |

Documentação: [`chat-response-modes.md`](../minha-delpi-ai-api/docs/architecture/chat-response-modes.md), changelog [`2026-06-playbook-19-prosa-latencia-analyser.md`](../minha-delpi-ai-api/docs/changelog/2026-06-playbook-19-prosa-latencia-analyser.md).

**Prod srv-api:** defaults de `docker-compose.yml` alinhados ao dev (jun/2026). `.env` de produção: só overrides (R16, paths, secrets) — **remover** bloco IA legado com `3b`/ctx alto se ainda existir. Após mudança: `docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --force-recreate minha-delpi-ai-api`.

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

## Evidências PAC e anexos Auditoria 5S (api-delpi)

Uploads de evidências do plugin **quality-action-plans** e anexos de NC da **auditoria-5s** ficam no filesystem do container `api-delpi`, path padrão `/app/data/pac-evidences` e `/app/data/audit-5s-nc`.

**Sem volume no host**, `docker compose up -d --force-recreate api-delpi` apaga os binários — o Postgres (`plugins_hub`) mantém o registro e o download retorna **«Arquivo não encontrado»**.

| Variável | Default no container | Host (volume) |
|----------|----------------------|---------------|
| `PAC_EVIDENCE_UPLOAD_DIR` | `/app/data/pac-evidences` | `${DELPI_DATA_HOST_DIR}/pac-evidences` |
| `KAIZEN_EVIDENCE_UPLOAD_DIR` | `/app/data/kaizen-evidences` | `${DELPI_DATA_HOST_DIR}/kaizen-evidences` |
| `AUDIT_5S_NC_UPLOAD_DIR` | `/app/data/audit-5s-nc` | `${DELPI_DATA_HOST_DIR}/audit-5s-nc` |
| `QUALITY_LABELS_QR_DIR` | `/app/data/quality-labels/qr` | `${DELPI_DATA_HOST_DIR}/quality-labels/qr` |

> As etiquetas da qualidade (**quality-labels**, CRUD dentro da `api-delpi`) guardam os PNGs de QR em `QUALITY_LABELS_QR_DIR`. Mesmo padrão: o Postgres mantém o registro da inspeção; sem volume, o QR some no recreate.

```bash
# srv-api (produção)
sudo mkdir -p /var/lib/delpi/pac-evidences /var/lib/delpi/kaizen-evidences /var/lib/delpi/audit-5s-nc /var/lib/delpi/quality-labels/qr
# em infra/.env:
DELPI_DATA_HOST_DIR=/var/lib/delpi

cd ~/projetos/delpi-central/infra
docker compose -f docker-compose.yml up -d --force-recreate api-delpi
docker exec delpi-api-delpi ls -la /app/data/pac-evidences
```

Anexos enviados **antes** deste volume precisam ser **reenviados** (não há backup automático).

---

## Logs de aplicação persistentes (api-delpi)

A `api-delpi` grava logs diários em arquivo (`app/utils/logger.py` → `logs/api_YYYYMMDD.log`, relativo ao WORKDIR `/app` → `/app/logs`).

- **Dev** (`docker-compose.dev.yml`): já persistem porque o serviço monta o código-fonte (`../api-delpi:/app`), então `/app/logs` cai em `api-delpi/logs` no host.
- **Prod** (`docker-compose.yml`): **sem volume**, `docker compose up -d --force-recreate api-delpi` apaga o histórico. Volume adicionado:

| Path no container | Host (volume) |
|-------------------|---------------|
| `/app/logs` | `${DELPI_DATA_HOST_DIR:-/var/lib/delpi}/api-delpi-logs` |

```bash
# srv-api (produção)
sudo mkdir -p /var/lib/delpi/api-delpi-logs
# em infra/.env: DELPI_DATA_HOST_DIR=/var/lib/delpi

cd ~/projetos/delpi-central/infra
docker compose -f docker-compose.yml up -d --force-recreate api-delpi
docker exec delpi-api-delpi ls -la /app/logs
tail -f /var/lib/delpi/api-delpi-logs/api_$(date +%Y%m%d).log
```

A **`api-pac-context`** (stack standalone) segue o mesmo padrão: `app/utils/logger.py` → `logs/ctx_YYYYMMDD.log`, com volume `${PAC_CONTEXT_LOG_DIR:-./logs}:/app/logs` no `api-pac-context/docker-compose.yml` (default: `./logs` ao lado do compose).

---

## Foto do visitante e QR (customer-experience-api)

Fotos dos participantes e imagens de QR do plugin **customer-experience** ficam no filesystem do container `customer-experience-api`, paths padrão `/app/data/customer-experience/photos` e `/app/data/customer-experience/qr`.

**Sem volume no host**, `docker compose up -d --force-recreate customer-experience-api` apaga os binários — o Postgres (schema `customer_experience`) mantém o registro e a página pública de agradecimento não exibe a foto.

| Variável | Default no container | Host (volume) |
|----------|----------------------|---------------|
| `CUSTOMER_EXPERIENCE_PHOTO_UPLOAD_DIR` | `/app/data/customer-experience/photos` | `${DELPI_DATA_HOST_DIR}/customer-experience/photos` |
| `CUSTOMER_EXPERIENCE_QR_DIR` | `/app/data/customer-experience/qr` | `${DELPI_DATA_HOST_DIR}/customer-experience/qr` |

```bash
# srv-api (produção)
sudo mkdir -p /var/lib/delpi/customer-experience/photos /var/lib/delpi/customer-experience/qr
# em infra/.env: DELPI_DATA_HOST_DIR=/var/lib/delpi

cd ~/projetos/delpi-central/infra
docker compose -f docker-compose.yml up -d --force-recreate customer-experience-api
docker exec delpi-customer-experience-api ls -la /app/data/customer-experience/photos
```

A página pública de agradecimento é servida **fora do portal** (sem login) pelo **shell público genérico** `public-hub` (container `delpi-public-hub`), com dados vindos do endpoint público `GET /apps/customer-experience-api/public/participants/{token}`.

O `public-hub` é o **irmão público do portal**: um único SPA estático que roteia páginas públicas de vários apps por `/p/{app}/{page}/{token}` (canônico). O QR atual usa o alias legado `/welcome/{token}` → `customer-experience/thanks`, mantido no gateway e no nginx do container para não quebrar códigos já impressos. Novos apps públicos registram suas views em `plugins/public-hub/src/apps/<app>/` + `src/shell/registry.ts`, sem criar um novo container por app.

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
