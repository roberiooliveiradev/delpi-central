# SURI — Plano de correção da ficha técnica e autoconhecimento

**Inventário:** 2026-11-06
**Estado:** levantamento/documentação; runtime e GPT não alterados. Acrônimo **não definido**, aguardando aprovação.

## Identidade e contrato observados (PROVEN)
- Persona no catálogo: **SURI — Especialista em Suprimentos da Minha DELPI**.
- Missão: ajudar no acompanhamento de compras, fornecedores, entregas e estoques com o mesmo escopo e acesso do usuário ao Portal Suprimentos.
- **Acrônimo S-U-R-I: TO_INVENTORY / aprovação pendente**. Não publicar expansão inventada como oficial. Critério: representar compras, Suprimentos, fornecedores e/ou inteligência de abastecimento.
- MCP: `get_context`, `read`, `analyze`, `knowledge`, `execute` (cinco ferramentas; **não** exigir `delete` por padronização artificial).
- `get_context(action=catalog)`: `catalog_version=16`; leitura de pedidos, solicitações, fornecedores, estoque, OTD, mercado, comércio exterior, usuário etc; 4 análises, `knowledge(search|get|sources)`; escrita por `execute` com entidades/ações explicitamente registradas.
- `get_context(action=context)`: contexto do principal, capabilities e unidades autorizadas; **não é ficha de identidade nem AuthZ por si só**.
- `knowledge(action=sources)`: `corpus_version=3`, `item_count=182`, fontes do manual/glossário do Portal, contratos, catálogo de métodos de Suprimentos.
- Evidência documental encontrada: `knowledge(action=get,knowledge_id=suri.boundaries)`, origem declarada `supplies-api/docs/SURI-S1-CONTRACT-FREEZE.md` §2, estado `OWNER_REPORTED`.

## Divergência comprovada entre superfícies
O item `suri.boundaries` diz textualmente que a versão não contém ferramentas de escrita/aprovação/CRUD e é somente leitura. Entretanto, **o catálogo e metadata do MCP nesta sessão** expõem `execute` para `suppliers.create/update` e outras ações governadas (comex, enrichment, session, users). O contrato declarado também descreve criação/atualização de fornecedores com controle de idempotência e acompanhamento de resultado.

**Classificação:** `PROVEN` para conflito entre conteúdo Knowledge vs catálogo/tool metadata; `TEST_NOT_RUN` para execução de mutações; não presumir write efetivo em produção só pelo catálogo, nem afirmar impossibilidade total sem tentar as ferramentas autorizadas quando adequado. Conferir owner, versão dos artefatos, política de AuthZ, rastreamento de operação e read-back antes de corrigir.

## Plano de correção
| ID | Achado | Estado | Proposta |
|---|---|---|---|
| SURI-01 | Acrônimo não identificado no catálogo | TO_INVENTORY | Definir com o usuário nome que represente Suprimentos; atualizar fonte canônica e consumers após aceite |
| SURI-02 | `suri.boundaries` afirma read-only apesar de catálogo com write | **FAIL de consistência**, PROVEN nas respostas consultadas | Localizar owner de `SURI-S1-CONTRACT-FREEZE.md`, versão corrente e corpus; corrigir orientação obsoleta sem apagar histórico, reindexar e testar |
| SURI-03 | `get_context(context)` não expõe ficha de identidade | PROVEN, melhoria TARGET | Descoberta leve de identidade por fonte única, sem usar perfil do usuário como identidade do agente |
| SURI-04 | Catalog/tool/knowledge não reconciliados para capacidades | TO_INVENTORY | Inventariar os cinco tools, entidades, actions, variantes de autorização e retorno; validar contratos e consumidores |
| SURI-05 | Cadastro/atualização fornecedores exige relato confiável | PROVEN no catálogo, runtime write TEST_NOT_RUN | Testar consultas/preview; usar ambiente de teste e confirmação governada para eventual write, verify por operation_id/owner; nunca write de teste em dados reais |
| SURI-06 | Perguntas conversacionais de identidade, capabilities e limites não verificadas | TEST_NOT_RUN | Criar casos positivos/negativos no GPT específico e parity MCP |
| SURI-07 | Regras de execução e estado de resultado de fornecedor precisam ser distinguidas | TARGET | Explicar `confirmed/acknowledged/sent/rejected/indeterminate/replayed`; `indeterminate` precisa investigação, nunca retry cego |

## Critérios de aceite
1. Perguntas "Quem é você?", "O que significa SURI?", "Quais ferramentas tem?", "Você cadastra fornecedores?", "Quais são seus limites?" são respondidas com fonte canônica e autorização correta.
2. Knowledge não contradiz catálogo vivo; `suri.boundaries` é atualizado ou explicitamente classificado como histórico.
3. `execute` de fornecedores é descrito corretamente, sem simular execução ou declarar persistência sem confirmação autoritativa.
4. Resposta é proporcional ao pedido: entender/consultar/analisar/recomendar/escrever autorizado/resultado verificado são coisas distintas.
5. Testes de contrato, regressão, segurança, consulta e resposta conversacional têm resultados no HEAD avaliado.

## Governança de implementação
Respeitar OWNER → FONTE CANÔNICA → CONSUMERS → CONTRATO → IMPLEMENTAÇÃO → RUNTIME → EVIDÊNCIA. Antes do diff: git status, HEAD, Abstraction Gate, menor alteração, testes e residual search. Não mudar backend/GPT Builder/OpenAPI por reflexo. Elaborar relatório de execução completo com postconditions. **Este arquivo é o plano, não prova do fix.**
