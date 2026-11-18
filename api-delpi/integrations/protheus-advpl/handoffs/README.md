# handoffs — entregas para a equipe TOTVS/ERP

Registro **documental** de entregas de pacotes de compilação. Sem banco, sem
workflow executável nesta etapa.

## Fluxo de acompanhamento

`PREPARED → SENT → RECEIVED → COMPILED → TESTED → APPROVED`

Estados de **acompanhamento de entrega** — distintos dos estados de ciclo de
vida do fonte (`SOURCE_CANDIDATE … PRD_PUBLISHED`, ver README do workspace).

- `templates/delivery-record.yaml` — registro por entrega (IDs, hashes, datas,
  responsáveis, resultado).
- `templates/compilation-checklist.md` — checklist que a equipe ERP preenche na
  compilação/homologação.

Preenchidos, os registros vivem aqui por entrega (`YYYY-MM-DD-<package_id>/`),
junto do SHA-256 do ZIP — **o ZIP em si não é commitado**.
