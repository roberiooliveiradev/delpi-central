# ADR-005 — BIs / apps externos evidentes só na RBAC do Product Owner

| Campo | Valor |
|-------|--------|
| Status | Aceito como **procedimento** · destino de cada BI = após dump |
| Data | 2026-09-08 |

---

## Contexto

O Product Owner evidenciou apps e capabilities usados por Analista SC/ES e Comprador SC:

| Nome UI (PO) | Permissão observada |
|--------------|---------------------|
| Análise - Importações | `importados.access` |
| Onde o item é usado - BI | `onde-e-usado.access` |
| Atraso de Fornecedores - SC - BI | `matriz_atraso-fornecedores.access` |
| Alçada de Compras - BI | `alcada-compras.access` |
| Controle de Estoques - SC - BI | `controle-estoque-sc.access` |
| Indicadores de Suprimentos - Sheets | `idd-suprimentos.access` |

Scan do monorepo (plugins, manifests, seeds Core, Compose, gateway, docs, scripts): **zero** ocorrências desses códigos. **CONFIRMADO_NO_CODIGO** (ausência). A existência operacional é **CONFIRMADO_POR_EVIDENCIA_DO_PRODUCT_OWNER**.

Equivalentes **parciais** nativos existem (OTD, estoque, parents de produto, Sheets IDD via dashboard). Isso **não** prova que os BIs foram desligados.

## Decisão

1. Classificar os seis como **LEGADO_A_VALIDAR** até dump do Core de **produção** (`apps`, `app_routes`, `permissions`, URLs iframe/Power BI/Sheets).
2. Subetapa obrigatória **E1.S1** do plano: consultar Core (admin API ou SQL) e preencher a tabela de [INVENTARIO-ATIVOS.md](../INVENTARIO-ATIVOS.md) seção E.
3. **Proibido** inventar redirect ou depreciação sem URL/id reais.
4. Enquanto isso, o Hub do Portal pode ter **placeholders capability-driven** só depois que o dump revelar o `app id` — não antes.
5. Sheets IDD já é consumida por `GET /supplies/negotiation-savings/summary`. A perm `idd-suprimentos.access` (se existir no Core) vira alias de `supplies.analytics.view` **após** confirmação, não agora.

## Se o dump não achar o app

Registrar `LEGADO_OU_POSSIVELMENTE_OBSOLETO` + data. A jornada correspondente no Portal (Importações, Alçadas, etc.) permanece **P1/P2** conforme [PLAYBOOK](../PLAYBOOK-MODULO-SUPRIMENTOS.md), sem fingir paridade.

## Não fazer

- Tratar evidência visual de permissão como contrato canônico.
- Copiar o código PT (`alcada-compras.access`) para permission **nova**.
- Assumir que «Onde o item é usado» do chat (`GET /products/{code}/parents`) **é** o BI do PO — são superfícies diferentes até prova.
