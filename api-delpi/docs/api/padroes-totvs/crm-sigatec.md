# CRM TOTVS (SIGATEC) — dicionário Delpi

Inventário do **CRM Protheus** usado na Delpi (oportunidade/OV, funil LMP, proposta, contato).

| | |
|---|---|
| Extração | `GET /system/tables/{t}/schema|relations|indexes` e `POST /data/sql` em `SX2010`, `SX3010`, `SIX010`, `SX9010`, `AC1010`, `AC2010` |
| Data | 19 ago 2026 |
| Playbook completo | [playbooks/playbook-crm-totvs-dicionario.md](./playbooks/playbook-crm-totvs-dicionario.md) |
| Produto CRM Delpi | estado novo em `commercial-api` — [ADR-001](../../../../docs/12-roadmap-e-evolucao/commercial/adr/ADR-001-commercial-api.md) |
| Cliente SA1 | [cadastro-cliente.md](./cadastro-cliente.md) |
| Funil / status 9 | [comercial-taxa-conversao-estagios.md](../comercial-taxa-conversao-estagios.md) |

## Entidade central

```text
AC1 processo ──► AC2 estágio
        │              │
        └──────────► AD1 oportunidade (OV) ◄── SA1 cliente / SUS prospect / SA3 vendedor
                         │
          ┌──────────────┼──────────────┬─────────────┐
          ▼              ▼              ▼             ▼
        ADJ itens      AIJ histórico   ADY proposta  AD8 tarefa
                         (LMP)            │
                                          ▼
                                        ADZ itens proposta
```

## O que fazer

- Tratar **AD1** como cabeçalho da OV; **AIJ** como trilha de estágio (LMP); **ADY** como documento de proposta.
- Conversão comercial = `AD1_STATUS = '9'` (Ganha), **não** estágio `000013`.
- Sempre `D_E_L_E_T_ = ''` e filial (`*_FILIAL`). OV = `AD1_NROPOR` (6) + `AD1_REVISA` (2).
- Campos custom Delpi: prefixo `AD1_Z*` / `ADJ_Z*` (embalagem, certificação, amostra, OV original).
- Leitura TOTVS na **api-delpi**; workflow Delpi (follow-up, reminder, anexo) na **commercial-api**.

## O que NÃO fazer

- Confundir `AD1_STATUS` com `AIJ_STATUS` (domínios diferentes; combo SX3 de AIJ ≠ rótulos do LMP).
- Usar `ADC010` no lugar de `AIJ010` para o histórico LMP.
- Tratar prefixos `SQ*` (RH), `ADE` (help desk) ou `AI*` (portal) como entidades do CRM Delpi.
- Confiar em `/system/tables/search?description=CRM` (fallback da SX2 inteira).
- Expandir `allowed_tables.json` sem rota que consulte a tabela.

## Funil cadastrado (AC1)

| Código | Nome | `AC1_MSBLQL` | Estágios |
|--------|------|--------------|----------|
| 000001 | COMPONENTES | 1 Inativo | 11 |
| 000002 | OPORTUNIDADE | 2 Ativo | 13 |
| 000003 | MODIFICACAO | 2 Ativo | 13 |

`000002` e `000003` compartilham a trilha LMP (análise crítica → cotação → engenharia → amostra → homologação → encerrado).

## Núcleo já na api-delpi

| Física | Lógica | Uso |
|--------|--------|-----|
| `AD1010` | `AD1` | LMP, `/commercial/proposals`, `/commercial/closing-rate` |
| `ADJ010` | `ADJ` | LMP detalhe / produtos da OV |
| `AIJ010` | `AIJ` | `/history/events`, `/history/flow` |
| `AC1010` | `AC1` | rótulo de processo |
| `AC2010` | `AC2` | rótulo de estágio |
| `ADY010` | `ADY` | módulo proposta-comercial |
| `ADZ010` | `ADZ` | módulo proposta-comercial |
| `SA1010` | `SA1` | join cliente |
| `SA3010` | `SA3` | join vendedor |
| `SU5010` | `SU5` | contatos (propostas) |
| `SQB010` | `SQB` | departamento contato |
| `SUM010` | `SUM` | cargo comercial |
| `SE4010` | `SE4` | condição de pagamento |

Detalhe de **todas** as tabelas, colunas SX3, índices SIX e relações SX9: o playbook.
