# Apontamento de Produção — especificação (Fase 0+)

> Plugin portal: **Apontamento de Produção**  
> Id técnico: `production-appointments`  
> Status: **Fase 1 API + Fase 2 MFE** (jul/2026) — chat/OpenAPI agent pendente

## Objetivo

Acompanhar **apontamentos de produção** (`SH6010`, tipo `P`) por **centro de trabalho (CT)**, com:

- catálogo de CTs;
- lista / summary / série temporal;
- drill-down por OP.

**Fora de escopo:** PPM, NC, eficiência %, MOD. CT de inspeção final entra nos totais como qualquer CT (metadado `is_final_inspection` opcional no catálogo).

## Modelo de dados (TOTVS)

```text
SH6010 (apontamento)
  └─ H6_RECURSO → SH1010.H1_CODIGO (recurso)
       └─ H1_CTRAB → SHB010.HB_COD (centro de trabalho)
```

| Tabela | Uso |
|--------|-----|
| `SH6010` | `H6_QTDPROD`, `H6_QTDPERD`, `H6_OP`, `H6_PRODUTO`, `H6_DTAPONT`, `H6_TIPO='P'` |
| `SH1010` | vínculo recurso → CT |
| `SHB010` | cadastro CT (`HB_COD`, `HB_NOME`) |
| `SB1010` | tipo/descrição do produto (opcional na listagem) |
| `SC2010` | enriquecer OP no drill-down (fase 1+, se útil) |

Filtros canônicos: `D_E_L_E_T_ = ' '`, período em `H6_DTAPONT` (`>= start` e `< end_exclusive`), filial `H6_FILIAL`.

Flag inspeção final (somente metadado): `UPPER(HB_NOME) LIKE '%INSPE%FINAL%'` — mesma convenção do domínio qualidade, **sem** acoplar rotas PPM.

## Rotas previstas (api-delpi)

Prefixo sugerido: `/production/appointments`

| Método | Path | operationId |
|--------|------|-------------|
| GET | `/production/appointments/work-centers` | `list_production_appointment_work_centers` |
| GET | `/production/appointments` | `list_production_appointments` |
| GET | `/production/appointments/summary` | `get_production_appointments_summary` |
| GET | `/production/appointments/series` | `get_production_appointments_series` |
| GET | `/production/appointments/by-op` | `list_production_appointments_by_op` |

Parâmetros comuns: `date_start`, `date_end`, `branch`, `work_center`, `op`, `product`, paginação.

Chat / OpenAPI agent: **somente após** validação API + plugin.

## Multi-filial

SC (`01`) / ES (`02`) — permissões `.view.filial-*` + `branch_access_error` no router.

## Validação Fase 0

Ver [FASE0-VALIDACAO.md](./FASE0-VALIDACAO.md).

Script: `api-delpi/scripts/sql/production_appointments_fase0_probe.py`.
