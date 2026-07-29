# Atas Transforma+ — API e configuração Kimi

Atualizado: **jul/2026**

Backend do módulo de atas no `transformometro-api`: CRUD, assinaturas, PDF e **geração assistida** via gateway OpenAI-compatible (padrão: **OpenRouter + modelo Kimi**).

Visão de produto: [ATAS-TRANSFORMA-MAIS.md](../../docs/12-roadmap-e-evolucao/transformometro-app/ATAS-TRANSFORMA-MAIS.md).  
MFE: [plugins/transformometro/docs/atas.md](../../plugins/transformometro/docs/atas.md).

---

## Base HTTP

| Item | Valor |
|------|-------|
| Prefixo público | `/apps/transformometro-api/transformometro/atas` |
| Prefixo interno (container) | `/transformometro/atas` |
| Envelope | `{ "success", "message", "data" }` (`tm_app.core.responses`) |
| Auth | JWT Bearer (mesmo padrão do restante da API) |

Router: `tm_app/interface/http/routes/minutes_routes.py`  
Serviço: `tm_app/application/services/meeting_minutes_service.py`  
LLM: `tm_app/infrastructure/llm/kimi_llm_gateway.py`

Perfil de assinatura do usuário: `/transformometro/signatures/*` (router separado).

---

## Endpoints (atas)

| Método | Path | Permissão | Notas |
|--------|------|-----------|-------|
| `GET` | `/atas` | `view` | Filtros: `unit_code`, `status`, `q`, `pending_for_me`, datas, paginação |
| `GET` | `/atas/pending-signatures` | autenticado | Pendências do usuário |
| `POST` | `/atas/generate-from-transcript` | `manage` + filial | **Só IA** — não grava no banco |
| `POST` | `/atas` | `manage` | Cria ata + versão inicial |
| `GET` | `/atas/{id}` | `view` | Detalhe (minute, version, participants, signers, signatures, viewer) |
| `PATCH` | `/atas/{id}` | `manage` | Atualiza metadados / HTML / participantes |
| `POST` | `/atas/{id}/versions` | `manage` | Nova versão com motivo |
| `PUT` | `/atas/{id}/participants` | `manage` | |
| `PUT` | `/atas/{id}/signers` | `manage` | |
| `POST` | `/atas/{id}/send-for-signature` | `manage` | |
| `GET` | `/atas/{id}/sign-context` | signatário | |
| `POST` | `/atas/{id}/signatures` | signatário | `multipart` PNG + termos |
| `GET` | `/atas/{id}/signatures/{sid}/image` | `view` | PNG |
| `POST` | `/atas/{id}/signatures/refuse` | signatário | |
| `POST` | `/atas/{id}/finalize` | `manage` | Gera/persiste PDF |
| `POST` | `/atas/{id}/cancel` | `manage` | |
| `GET` | `/atas/{id}/export.pdf` | `view` | Download |
| `GET` | `/atas/{id}/audit` | `manage` | |
| `DELETE` | `/atas/{id}` | `manage` | Soft delete |

Códigos RBAC: `transformometro.atas.view` / `.manage` / `.sign`.

Erros de domínio comuns: `400` (validação / transição de status), `403` (RBAC/filial), `404`, `502` (`AtaGenerationError` do Kimi).

---

## Geração com Kimi

### Contrato

`POST /transformometro/atas/generate-from-transcript`

Body (aliases camelCase aceitos):

```json
{
  "unitCode": "01",
  "meetingDate": "2026-07-28",
  "title": "Reunião Transforma+",
  "transcriptHtml": "<p>…</p>",
  "source": "docx"
}
```

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `unitCode` | sim | Filial; usado só para RBAC `manage` |
| `meetingDate` | sim | Ecoado na resposta |
| `transcriptHtml` | sim | HTML da transcrição (DOCX convertido no MFE ou texto colado) |
| `source` | sim | Ex.: `docx`, `manual` |
| `title` | não | Ecoado se enviado |

Resposta `data` (snake_case nas seções):

```json
{
  "unitCode": "01",
  "meetingDate": "2026-07-28",
  "title": "…",
  "source": "docx",
  "agenda_html": "<p>…</p>",
  "body_html": "<p>…</p>",
  "decisions_html": "<ul>…</ul>",
  "pending_html": "<p>…</p>",
  "observations_html": "<p>…</p>"
}
```

**Não há INSERT/UPDATE.** O editor aplica o HTML no estado local; o usuário precisa **salvar** a ata.

### Pipeline no gateway

1. HTML → texto puro (`_html_to_plain_text`)
2. Truncamento em `KIMI_MAX_TRANSCRIPT_CHARS` (default **20 000**)
3. `POST {KIMI_BASE_URL}/chat/completions` com system prompt fixo (JSON com as 5 chaves)
4. Parse do conteúdo do modelo (remove fences markdown se vierem)
5. Validação: todas as chaves `agenda_html` … `observations_html` presentes e string

Timeouts / HTTP do provedor → `AtaGenerationError` → HTTP **502** com mensagem amigável (sem traceback).

### Variáveis de ambiente

Definidas em `tm_app/config.py` e passadas pelo Compose (`infra/docker-compose*.yml` → serviço `transformometro-api`):

| Variável | Default | Descrição |
|----------|---------|-----------|
| `KIMI_API_KEY` | *(vazio)* | **Obrigatória** para gerar. Sem chave → 502 claro |
| `KIMI_BASE_URL` | `https://openrouter.ai/api/v1` | Base OpenAI-compatible |
| `KIMI_MODEL` | `moonshotai/kimi-k3` | Modelo no provedor |
| `KIMI_TIMEOUT_SECONDS` | `180` | Timeout HTTP da chamada |
| `KIMI_MAX_TRANSCRIPT_CHARS` | `20000` | Cap do texto enviado ao modelo |
| `KIMI_MAX_OUTPUT_TOKENS` | `4096` | `max_tokens` da completion |

Compose hoje injeta `KIMI_API_KEY`, `KIMI_BASE_URL` e `KIMI_MODEL` a partir de `infra/.env`. Os limites/timeout usam default da Settings dentro do container; para sobrescrever, adicione as variáveis no `.env` **e** no bloco `environment:` do serviço (ou `env_file` já carrega se a Settings ler o ambiente — `Settings` usa `os.environ` / `_get_env`, então bastam no `env_file` do compose se o container herdar `infra/.env`).

No monorepo:

```bash
# infra/.env (não commitado)
KIMI_API_KEY=sk-or-v1-...
KIMI_BASE_URL=https://openrouter.ai/api/v1
KIMI_MODEL=moonshotai/kimi-k3
# opcional:
# KIMI_TIMEOUT_SECONDS=180
# KIMI_MAX_TRANSCRIPT_CHARS=20000
# KIMI_MAX_OUTPUT_TOKENS=4096
```

Exemplos versionados: `transformometro-api/.env.example`, `infra/env.local.example`.

Após alterar:

```bash
./infra/scripts/up-dev-sequential.sh --fase api --build transformometro-api
# ou recreate sem rebuild se só mudou env:
# docker compose -f infra/docker-compose.dev.yml up -d --force-recreate transformometro-api
```

### Teste isolado (sem API)

```bash
cd transformometro-api
cp .env.example .env   # preencha KIMI_API_KEY
python scripts/test_kimi_ata.py
```

Testes unitários do gateway (mock HTTP): `tests/test_kimi_llm_gateway.py`.

### Smoke autenticado

```bash
TOKEN="…"   # JWT com transformometro.atas.manage + filial
curl -sS -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "unitCode":"01",
    "meetingDate":"2026-07-28",
    "transcriptHtml":"<p>Abertura. Decisão: aprovar plano. Pendência: João até sexta.</p>",
    "source":"manual"
  }' \
  "http://localhost/apps/transformometro-api/transformometro/atas/generate-from-transcript" \
  | jq '.success, .data | keys'
```

Esperado: `success: true` e chaves `agenda_html`, `body_html`, …

---

## Storage persistente

| Variável | Path container | Host |
|----------|----------------|------|
| `TM_ATA_SIGNATURE_UPLOAD_DIR` | `/app/data/transformometro/atas/signatures` | `${DELPI_DATA_HOST_DIR}/transformometro/atas/signatures` |
| `TM_ATA_PDF_UPLOAD_DIR` | `/app/data/transformometro/atas/pdfs` | `${DELPI_DATA_HOST_DIR}/transformometro/atas/pdfs` |

Metadado no Postgres; binário no volume. Ver regra `persistent-upload-storage` e [infra/README-ambiente.md](../../infra/README-ambiente.md).

Migration: `migrations/V042__meeting_minutes_transforma_mais.sql` (imutável após apply).

---

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| 502 «KIMI_API_KEY não configurada» | Env vazia no container | Definir em `infra/.env` e recreate da API |
| 502 timeout | Transcrição enorme / provedor lento | Subir `KIMI_TIMEOUT_SECONDS`; texto já é capped em 20k |
| 502 JSON inválido | Modelo fora do contrato | Ver logs `transformometro.llm.kimi`; repetir; conferir `KIMI_MODEL` |
| 403 na geração | Sem `atas.manage` ou filial | RBAC Core API |
| UI «Gerando…» e F5 perde resultado | Esperado — geração não persiste | Não navegar até o merge no editor + salvar |
| Logo/PDF ok, mas IA não | Só MFE rebuildado | Rebuild/recreate **API** com env Kimi |

Logs úteis no container: `kimi_ata_generate_start`, `kimi_ata_timeout`, `kimi_ata_http_error`, `kimi_ata_invalid_model_json`.
