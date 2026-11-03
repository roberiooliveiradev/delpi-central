# Carga Máquina — horizonte temporário por centro de trabalho

## Objetivo

Permitir que o PCP amplie **temporariamente** a programação de um CT com pouca fila, sem alterar o horizonte global da filial nem trazer operações futuras para as demais máquinas.

Decisão de produto: **OPÇÃO A** — exceção por atualização (geração WORKING), sem configuração permanente por máquina.

## Fluxo

1. `POST /machine-load/refresh` — janela-base (padrão `defaultDeliveryWindowDays`, tipicamente 14).
2. No CT selecionado, **Ampliar horizonte** (21 / 28 / 42 dias ou data final).
3. `POST /machine-load/horizon/preview` — consulta TOTVS só do CT no intervalo adicional (`base_end+1` … `end_date`).
4. `POST /machine-load/horizon/apply` — mescla no WORKING, preserva ordem/proteções/transferências/retiradas.
5. Cockpit permanece na PUBLISHED até `POST /machine-load/publish`.
6. Próximo refresh descarta `horizon_exceptions` e reconstrói a janela-base.

## Segurança de publicação

- Ampliação **bloqueada** quando `publication.state === live` (409): orientar «Atualizar».
- Apply grava via `_persist_queue_change` somente em draft/unpublished (WORKING-only).
- Prévia não altera WORKING nem PUBLISHED.
- Concorrência: `expectedGenerationId` (+ opcional `expectedNewOperationCount`).

## Contrato

| Método | Path | `operation_id` |
|---|---|---|
| POST | `/machine-load/horizon/preview` | `preview_machine_load_horizon_expansion` |
| POST | `/machine-load/horizon/apply` | `apply_machine_load_horizon_expansion` |

Body (camelCase): `workCenter`, `endDate`, `expectedGenerationId`, `expectedNewOperationCount?`.

Metadados no payload JSON WORKING: `horizon_exceptions[ct] = { end_date, base_end_date, added_count, … }`. Sem migration.

Permissão: mesma de visualização/mutação da carga máquina (`production-control.machine-load.view` + escopo de filial).

## Limites

- Data final deve ultrapassar o fim da janela-base.
- Teto: hoje + 90 dias (`MAX_HORIZON_DAYS_FROM_TODAY`).
- Sem escape HZA legado; runs MES abertos continuam protegidos pelas regras atuais de slots.
