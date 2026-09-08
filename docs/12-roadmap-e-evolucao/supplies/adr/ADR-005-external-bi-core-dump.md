# ADR-005 — BIs / apps externos evidentes só na RBAC do Product Owner

| Campo | Valor |
|-------|--------|
| Status | Aceito como procedimento · destino de cada BI após dump |
| Data | 2026-09-08 |

---

## Contexto

O Product Owner evidenciou apps/capabilities usados por Analista SC/ES e Comprador SC:

| Nome UI (PO) | Permission observada |
|---|---|
| Análise - Importações | `importados.access` |
| Onde o item é usado - BI | `onde-e-usado.access` |
| Atraso de Fornecedores - SC - BI | `matriz_atraso-fornecedores.access` |
| Alçada de Compras - BI | `alcada-compras.access` |
| Controle de Estoques - SC - BI | `controle-estoque-sc.access` |
| Indicadores de Suprimentos - Sheets | `idd-suprimentos.access` |

Esses codes não foram localizados no monorepo; a existência operacional é **CONFIRMADO_POR_EVIDENCIA_DO_PRODUCT_OWNER** e o contrato técnico permanece desconhecido até dump do Core de produção.

## Decisão

1. Classificar os seis como `LEGADO_A_VALIDAR` durante E1.
2. E1.S1 consulta Core/admin/SQL autorizado e registra id, type, URL/basePath, routes, permissions e owner.
3. Não inventar redirect, paridade ou depreciação antes dessa evidência.
4. Não copiar permission PT/legada para o catálogo novo por conveniência.
5. Aliases só são definidos após confirmação do code real e análise de risco pelo ADR-007.

## Gate de cutover

`LEGADO_A_VALIDAR` é estado de descoberta, **não estado permitido no GO**.

Antes do `GATE-CUTOVER`, cada um deve estar em exatamente um destes estados:

```text
PARIDADE_HOMOLOGADA
MANTER_EXTERNO
DEEP_LINK
FORA_DO_ESCOPO_COM_ACEITE
```

Se o dump não encontrar o app, registrar `LEGADO_OU_POSSIVELMENTE_OBSOLETO`, investigar uso/owner e obter aceite antes de convertê-lo em `FORA_DO_ESCOPO_COM_ACEITE`.

## Casos especiais

### Indicadores / Sheets

A leitura de savings já existe via api-delpi. Isso não prova que o app Sheets possa ser removido; pode existir processo de edição. O destino só fecha após confirmar quem edita e qual é a fonte canônica de meta/realizado.

### Onde o item é usado

`GET /products/{code}/parents` é capability nativa existente, mas não prova paridade do BI externo. Comparar regra/filtros/apresentação antes da decisão final.

### Alçadas

Consultar `C7_APROV` não equivale automaticamente a workflow de aprovação. Se houver aprovação/rejeição real, avaliar segregação de função e possível permission específica conforme ADR-007.

## Não fazer

- tratar ausência no git como ausência operacional;
- tratar screenshot como contrato canônico completo;
- registrar redirect para path desconhecido;
- chegar ao cutover com qualquer BI ainda `LEGADO_A_VALIDAR`.
