# Materiais de Terceiros — roadmap

## Escopo entregue

- View somente leitura `dbo.VW_PD3_BENEF_RETORNOS` (`SB6`) versionada na api-delpi
- Rotas EN `/supplies/third-party-materials/*` (lista por remessa, detalhe, KPIs, export)
- RBAC multi-filial `01`/`02`
- MFE federado `materiais-terceiros` (filtros, KPIs, grade, detalhe, URL, export)

## Regras imutáveis

- Chave remessa ↔ retorno: `B6_FILIAL + B6_PRODUTO + B6_IDENT`
- Não usar `B6_TPCF` / `B6_IDENTB6` como chave
- Remessa: `B6_PODER3 = R` e `B6_TIPO = D`; retorno: `B6_PODER3 = D` e `B6_TIPO = D`
- Saldo atual = `B6_SALDO` da remessa; não somar saldo repetido nas linhas de retorno
- Produto `99999999`: ocultar por config, nunca na view
- Somente leitura no Protheus

## Fora de escopo (follow-up)

- Chat Minha Delpi (`operational_route_registry` / perfil de apresentação)
- Índices novos no SQL Server sem plano medido
- Correção de saldo na `SB6`
- Histórico de saldo em data passada (limitação da view)

## Referências

- Plugin: [plugins/materiais-terceiros/README.md](../../../plugins/materiais-terceiros/README.md)
- API: [api-delpi/docs/api/materiais-terceiros.md](../../../api-delpi/docs/api/materiais-terceiros.md)
- Padrões SB6: [padroes-totvs/materiais-terceiros-sb6.md](../../../api-delpi/docs/api/padroes-totvs/materiais-terceiros-sb6.md)
