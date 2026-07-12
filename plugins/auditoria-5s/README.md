# Auditoria 5S — plugin Minha DELPI

MFE federado para auditoria operacional 5S por filial (01/02).

## Dev local (WSL)

```bash
cd plugins/auditoria-5s
npm ci
npm run dev
```

## Build / CI

```bash
./scripts/ci/build-auditoria-5s.sh
```

## Docker (compose)

Serviço `auditoria-5s` → container `delpi-auditoria-5s`.

**Chat/Ollama:** no dev, `ollama`, `minha-delpi-ai-api` e `minha-delpi-chat` usam profile `chat` — não sobem junto com o gateway. Para o chat: `--profile chat`.

```bash
cd infra

# Stack mínima Auditoria 5S (sem Ollama, sem rebuild de todos os dashboards)
docker compose -f docker-compose.dev.yml --env-file .env up -d --build \
  postgres-plugins postgres-core keycloak core-api strategic-indicators-api \
  api-delpi auditoria-5s portal

docker compose -f docker-compose.dev.yml --env-file .env up -d --no-deps gateway

# Só se precisar do chat depois:
docker compose -f docker-compose.dev.yml --env-file .env --profile chat up -d ollama minha-delpi-ai-api minha-delpi-chat
```

Parar Ollama se subiu por engano: `docker stop delpi-ollama`

## Registro no Portal

```bash
export TOKEN="<jwt superadmin>"
./plugins/auditoria-5s/scripts/register-manifest.sh
```

## API (gateway)

Base: `/apps/api-delpi/quality/audit-5s`

Documentação: [docs/12-roadmap-e-evolucao/auditoria-5s/ROADMAP.md](../../docs/12-roadmap-e-evolucao/auditoria-5s/ROADMAP.md)

### Foto por critério (avaliação)

Em qualquer critério com nota **1, 3 ou 5**, a UI permite anexar foto opcional:

| Método | Path | Uso |
|--------|------|-----|
| `POST` | `/audits/{id}/responses/{criterionId}/attachments` | Upload da foto |
| `GET` | `.../attachments/{attachmentId}/file` | Preview/download |
| `DELETE` | `.../attachments/{attachmentId}` | Remover |

Ao criar a NC, a foto da avaliação é copiada automaticamente para a evidência **antes** (`before`), se o slot estiver vazio.

Storage: `AUDIT_5S_RESPONSE_UPLOAD_DIR` → volume `${DELPI_DATA_HOST_DIR}/audit-5s-responses`.

### Exclusão de auditorias

| Método | Path | Uso |
|--------|------|-----|
| `POST` | `/audits/{id}/delete` | Exclui auditoria em **avaliação** (`draft`) |
| `POST` | `/audits/{id}/force-delete` | Exclui auditoria em **qualquer status** (irreversível; remove respostas, fotos e NCs) |
| `POST` | `/audits/{id}/reopen-evaluation` | Volta para fase **Em avaliação** (`draft`); bloqueado se já houver NC registrada |

Permissão: `auditoria-5s.audit.filial-XX` da filial da auditoria.

### Exportação de resultados

Na lista de auditorias, menu **Mais ações** (⋯) por linha:

| Formato | Conteúdo |
|---------|----------|
| Excel (`.xlsx`) | Cabeçalho, notas por senso, critérios e NCs (quando existirem) |
| PDF | Mesmo conteúdo formatado para impressão/arquivo |

### Tratamento de NC — foto do antes

Na tela de tratamento, a **foto tirada na avaliação** aparece imediatamente no card «Foto do antes» (badge «Da avaliação»), sem precisar preencher o plano de ação. Ao salvar o plano, a API copia a foto para a evidência oficial da NC (`seed_nc_before_from_response_attachment`).

### Notificação ao designar responsável

Ao criar ou atualizar o plano de NC com um responsável selecionado no directory (`responsible_user_id` + `responsible_name`), a api-delpi emite notificação no sino do portal (`POST /integrations/notifications`) para esse usuário — categoria `auditoria_5s` / `sourceApp: auditoria-5s`.

- Dispara só quando o UUID do responsável **muda** (e não quando o responsável atribui a si mesmo).
- Destinatário precisa ter acesso ao app `auditoria-5s` no portal (filtro RBAC do catálogo).
- Flag: `AUDIT_5S_NOTIFICATIONS_ENABLED` (default `true`); requer `CORE_API_BASE_URL` + `CORE_API_INTEGRATIONS_SERVICE_TOKEN`.
- CTA: `/apps/auditoria-5s/filial-01/nc-board` ou `filial-02` (abre a Gestão de não conformidades).

Migration: `V040__audit_5s_nc_responsible_user_id.sql`.

## Homologação

```bash
# Fase 1 — remoteEntry + critérios
bash ../../scripts/homologacao/check-auditoria-5s.sh

export TOKEN="<jwt>"
bash ../../scripts/homologacao/check-auditoria-5s.sh

# Fase 2 — fluxo API completo
bash ../../scripts/homologacao/check-audit-5s-api.sh
```

## Migrations

As migrations do 5S ficam em `api-delpi/migrations/plugins/quality/` (plugin slug **`quality`**).

Inclui `V037__audit_5s_response_attachment_unique.sql` (índice único: 1 foto por resposta/critério) e `V040__audit_5s_nc_responsible_user_id.sql` (UUID do responsável no plano de NC).

**Pré-requisito:** `delpi-postgres-plugins` em execução (`Up`, não `Restarting`). Se o log mostrar `exec format error`, repuxar a imagem AMD64:

```bash
cd infra
docker compose -f docker-compose.dev.yml --env-file .env stop postgres-plugins
docker rm -f delpi-postgres-plugins
docker pull --platform linux/amd64 pgvector/pgvector:pg15
docker compose -f docker-compose.dev.yml --env-file .env up -d postgres-plugins
```

```bash
# Ver pendências (V022, V023 do audit_5s)
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin quality

# Aplicar só as do schema quality (recomendado)
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin quality
```
