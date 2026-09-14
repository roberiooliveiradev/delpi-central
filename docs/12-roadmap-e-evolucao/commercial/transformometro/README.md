# Portal Comercial × Transformômetro — base de reconciliação

> **Tipo:** documentação de reconciliação factual e preparação para TÉO/Transformômetro  
> **Baseline inicial:** `bcf23241e058c03fae74dc24231adebdf34d297c` (Fase 1R)  
> **Data:** 2026-09-14  
> **Fonte factual principal:** [`../INVENTARIO-ESTADO-ATUAL.md`](../INVENTARIO-ESTADO-ATUAL.md)  
> **Backlog separado:** [`../PARCIAL-INVENTARIO.md`](../PARCIAL-INVENTARIO.md)

## Objetivo

Esta pasta organiza a relação entre as capacidades atuais do **Portal Comercial**, as aplicações/capacidades que já existiam na Minha DELPI e o futuro cruzamento com os registros do **Transformômetro**.

Ela existe para permitir que outros chats do projeto retomem o trabalho sem depender de memória conversacional e sem confundir:

- estado atual comprovado no repositório;
- origem técnica anterior de uma capacidade;
- hipótese de equivalência com item já cadastrado no Transformômetro;
- necessidade de nova revisão;
- possibilidade de novo cadastro;
- backlog ou melhoria ainda não implementada.

## O que esta pasta NÃO prova

O repositório não prova, sozinho:

- quais macroprocessos/processos/melhorias já estão cadastrados no Transformômetro;
- IDs e revisões atuais desses registros;
- se uma capacidade tecnicamente nova no Portal representa um processo de negócio novo;
- se uma capacidade migrada já possui melhoria correspondente no Transformômetro;
- uso real, frequência, atores reais, handoffs, espera ou resultado operacional por filial.

Esses itens permanecem `PENDING_TRANSFORMOMETRO` ou `TO_INVENTORY_EXTERNAL` até consulta ao Transformômetro e evidência do processo real.

## Classificações usadas

| Classificação | Significado |
|---|---|
| `MIGRATED_LEGACY_MFE` | Capacidade cuja migração de um MFE anterior para o Portal está documentada/provada |
| `EVOLVED_LEGACY_CAPABILITY` | Capacidade anterior existia, mas o Portal alterou modelo, ownership ou amplitude |
| `OVERLAP_LEGACY_SIBLING` | Portal atual possui capacidade que também existe no `dashboard-commercial`, que continua registrado |
| `PORTAL_NATIVE_STATE` | Estado/regra/persistência implementado no domínio `commercial-api`/schema `commercial`; não significa automaticamente processo de negócio novo |
| `PORTAL_NATIVE_EXPERIENCE_ON_EXISTING_DATA` | Experiência nova/consolidada no Portal sobre dados/contratos upstream já existentes |
| `HYBRID` | Combina estado nativo do Comercial com dados/capacidades anteriores/upstream |
| `PENDING_TRANSFORMOMETRO` | Equivalência com cadastro do Transformômetro ainda não verificada |
| `TO_INVENTORY_EXTERNAL` | Exige evidência fora do GitHub, como runtime ou processo humano real |

## Conclusões já comprovadas

1. `pedidos-venda-abertos` e `propostas-comerciais` tiveram seus MFEs removidos no F2c; as experiências canônicas passaram para `/apps/commercial/open-orders` e `/apps/commercial/proposals`. Os contratos TOTVS na `api-delpi` permaneceram.
2. `dashboard-commercial` **não** foi removido no F2c: permanece `LEGACY_BUT_REGISTERED`, com menu/manifest próprios e consumo direto da `api-delpi`. Há overlap com KPIs, OTD e OV/Oportunidades do Portal.
3. Carteiras comerciais já possuíam origem legada associada ao PVA, mas o modelo canônico atual está no schema `commercial`; membership N:N vive em `seller_portfolio_members` e não no schema legado.
4. O Portal possui estado próprio adicional comprovado para tarefas, atividades, anexos, favoritos, perfis, contatos, grupos, SLAs, outbox/checkpoints e salas de interação.
5. Conta 360, produção vinculada, faturamento/NF e parte da gestão à vista são composições do Portal sobre dados existentes na `api-delpi`/TOTVS, combinados em alguns casos com estado próprio do Comercial.
6. Nenhuma dessas conclusões permite afirmar, sem consultar o Transformômetro, que o item deve ser cadastrado como melhoria nova.

## Documentos desta pasta

| Documento | Finalidade |
|---|---|
| [`MAPA-ORIGEM-CAPACIDADES.md`](./MAPA-ORIGEM-CAPACIDADES.md) | Capacidade por capacidade: origem comprovada, estado atual e cautela de classificação |
| [`MATRIZ-RECONCILIACAO.md`](./MATRIZ-RECONCILIACAO.md) | Tabela preparada para cruzar com macroprocessos/processos/melhorias do Transformômetro |
| [`BRIEFING-TEO.md`](./BRIEFING-TEO.md) | Contexto confiável para entregar ao TÉO quando o catálogo do Transformômetro estiver acessível |

## Fontes canônicas usadas

- `../INVENTARIO-ESTADO-ATUAL.md` — Current State comprovado.
- `../F2C-CUTOVER-RUNBOOK.md` — cutover dos MFEs legados para o Portal.
- `../README.md` — índice/status documental do Portal.
- `../PARCIAL-INVENTARIO.md` — backlog, parcial, bloqueado e fora de escopo; não usar como prova de Current State.
- `../PERFIS-E-PERMISSOES.md` — catálogo documental atual de permissões.
- `../DATA-MODEL.md` — modelo/documentação; migrations/repos continuam sendo autoridade para estado implementado.
- Código e manifests citados pelo inventário factual.

## Regra para outros chats

Antes de continuar esta frente:

1. confirmar `main` e HEAD atual;
2. ler `INVENTARIO-ESTADO-ATUAL.md` como baseline factual;
3. ler esta pasta para a reconciliação Portal × Transformômetro;
4. consultar o catálogo real do Transformômetro antes de classificar `nova revisão` ou `novo cadastro`;
5. não transformar `PENDING_TRANSFORMOMETRO` em fato por semelhança de nome;
6. manter processo atual, problemas, hipóteses e proposta futura separados;
7. se houver mais de uma filial/unidade relevante, não selecionar uma silenciosamente.

## Estado da reconciliação

**Status atual:** `PENDING_TRANSFORMOMETRO`.

A etapa GitHub está suficientemente inventariada para iniciar o cruzamento semântico. O próximo dado necessário é a lista/exportação do Transformômetro para a área Comercial contendo, no mínimo, macroprocesso, processo, melhoria, IDs, revisão/status e descrição disponível.