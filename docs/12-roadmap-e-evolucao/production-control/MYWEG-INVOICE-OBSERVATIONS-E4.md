# MyWEG → Production Control — NF Emitidas (Etapa 4)

> **TASK_ID:** `MYWEG-INVOICE-OBSERVATIONS-E4`  
> **Status:** automação Linux do publicador fiscal (timer **não** habilitado por padrão)  
> **Depende de:** Etapas 1–3  
> **Owner:** `production-control-api` (job) + `infra` (Compose/systemd)  
> **EXISTING_EQUIVALENT:** `PARTIAL` · **REUSE_DECISION:** `EXTEND`

## Objetivo

Descobrir, validar e publicar automaticamente observações fiscais MyWEG no Linux,
reutilizando o publicador E1, com estado/lock/timer **independentes** do publicador
de necessidades.

Não altera cálculos E2 nem UI E3. Não baixa necessidades.

## Comandos

```bash
# Dry-run pendências
python -m production_control_app.jobs.myweg_invoice_observations_publisher \
  --dry-run --publish-pending --json

# Publicar pendências
python -m production_control_app.jobs.myweg_invoice_observations_publisher \
  --publish --publish-pending --json

# Marco de ativação (fail-closed sem ele)
python -m ... --set-activation-document-date '2026-11-05' --json

# Semear observação manual já aceita (evita republish do histórico)
python -m ... --record-published-success \
  --collection-id '...' --document-date 'YYYY-MM-DD' \
  --payload-sha256 '...' --semantic-sha256 '...' \
  --observation-id '...' --json
```

Compose (profile `manual`):

```bash
cd infra
docker compose -f docker-compose.yml --env-file .env --profile manual \
  run --rm --no-deps myweg-invoice-observations-publisher \
  --dry-run --publish-pending --json
```

## Deduplicação e conflito

- Agrupa por `document_date`.
- Exportações com o mesmo `semantic_sha256` → publica **uma** representante.
- Hashes semânticos divergentes no mesmo dia → `conflict` (sem POST).
- `empty_signaled_by_sap` + `with_records` no mesmo dia → `conflict`.
- Sem supersedência implícita (alinhado ao motor E2).

## Timer

Arquivos: `infra/systemd/myweg-invoice-observations-publisher.{service,timer}`  
Instalador: `infra/scripts/install-myweg-invoice-observations-publisher-timer.sh`  
**Não habilita** o timer. Cadência: 08/10/12/14/16/18 America/Sao_Paulo.

Ativar só após watermark + dry-run + autorização explícita:

```bash
sudo systemctl enable --now myweg-invoice-observations-publisher.timer
sudo systemctl disable --now myweg-invoice-observations-publisher.timer
```

## Estado

`/var/lib/delpi/myweg-invoice-publisher-state` (host)  
Arquivo: `invoice_publisher_state.json` — evidência operacional local; PostgreSQL permanece autoridade de negócio.

## Fora de escopo

Windows coletor, E2/E3, migrations, Protheus, timer de necessidades, Etapa 5.
