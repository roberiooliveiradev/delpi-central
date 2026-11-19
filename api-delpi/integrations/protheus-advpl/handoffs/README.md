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

Os registros vivem aqui por entrega — **uma pasta estável por pacote**
(`DELPI-ADVPL-<TAG>-<AMBIENTE>/`), sempre com a versão mais recente.
Histórico de versões fica no **Git**, não em pastas datadas.

## Layout (desde 2026-11-19 — sem ZIP)

```text
DELPI-ADVPL-<TAG>-<AMBIENTE>/
  delivery-record.yaml
  <package_id>.manifest.json      (quando gerado por packaging/package.py)
  <module-id>/
    README.md
    contracts/*
    src/<FONTE>.PRW
```

O `.PRW` que a equipe ERP compila sai direto de `<module-id>/src/`. Não
trabalhamos com `.zip` (o gerador `packaging/package.py` continua existindo
e produz manifest+ZIP determinísticos se um dia for necessário provar
integridade por hash).

Versões anteriores de uma entrega: `git log -- <pasta>` / histórico do
`delivery-record.yaml` (campo `package_version`).
