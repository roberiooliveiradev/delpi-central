# GLPI #1353 — Evolução da Auditoria de Consumo: busca, filtros e comparação de OPs

> **Estado:** PLANNED / DOCUMENTATION ONLY — proposta de evolução da página existente, sem código ou deploy neste commit.
> **Origem:** feedback do Product Owner sobre a página publicada em `/apps/supplies/consumption-audit?unit=01&op=...` (captura de tela em 2026-10-29).
> **Baseline remoto da consulta:** `main` em `7d81aa2785acbdd5d2fe3fb9c768549ea3e2259f`. O Devin precisa revalidar HEAD, `origin/main` e `git status` antes de implementar.
> **Relacionados:** [plano mestre GLPI #1353](./GLPI-1353-END-TO-END-DEVIN-IMPLEMENTATION-PLAN.md), [D1 fluxo](./GLPI-1353-PRODUCTION-CONSUMPTION-AUDIT-FLOW-20261029.md), [D2.1](./GLPI-1353-CONSUMPTION-AUDIT-BUSINESS-RULES-D2.md), [D2.2](./GLPI-1353-CONSUMPTION-AUDIT-CONTRACTS-D2.md), [MATRIZ-BOUNDARIES](./MATRIZ-BOUNDARIES.md), [ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md).

## 1. Objetivo e decisões de produto

Hoje a página permite consultar uma OP conhecida por número e filial. O PO deseja **remover o botão “Consultar”** e disparar busca automaticamente conforme a digitação, permitir encontrar OPs por **data e outros atributos sem conhecer o código**, e futuramente **selecionar e comparar várias OPs**.

Evoluir **a mesma página**, preservando o detalhe já implantado, sem confundir esta capacidade com E12 (consumo produto×período), nem autorizar escrita de dados Protheus. O pedido é de **planejamento/documentação**; execução de código e deploy exigem autorização expressa subsequente, além de gates técnicos.

O print da página mostra cabeçalho alto, filtro filial+número+botão, resumo da OP, lista de operações e sinalização de qualidade parcial. Melhorias complementares candidatas: reduzir altura do filtro, resumo mais escaneável e operações recolhíveis; não ampliar o diff de busca sem critério.

## 2. RQ / AC / prioridades

| ID | Requisito | Critério de aceite |
|---|---|---|
| RQ-S01 | Remover botão “Consultar” | AC-S01: nenhuma ação de consulta exige clique no botão; seleção/Enter e URL disparam detalhe automaticamente |
| RQ-S02 | Busca incremental por número | AC-S02: debounce (~350ms como parâmetro sugerido), mínimo de caracteres aprovado, cancelamento de stale requests e resultado que não pisca |
| RQ-S03 | Sugestões de OP | AC-S03: exibir código, produto/descrição, data com seu tipo e situação; teclado/foco/Enter/Escape; nada de consultar o detalhe completo para cada sugestão |
| RQ-S04 | Busca sem conhecer OP | AC-S04: pesquisar por filial, período e tipo de data (emissão, apontamento/produção, encerramento), produto/código/descrição, situação e centro de trabalho/operação quando suportado pelo contrato real |
| RQ-S05 | Filtros combinados | AC-S05: intersecção de filtros, parâmetros explícitos, paginação estável, estados loading/empty/partial/error/403; limpar filtros; URL compartilhável |
| RQ-S06 | Seleção de uma OP | AC-S06: escolher resultado abre detalhe na página existente, preserva filial+OP na URL e funciona após F5 |
| RQ-S07 | Seleção múltipla | AC-S07: escolher várias OPs (limite inicial PROPOSED: 2–10), remover seleção, preservar chaves filial+OP, não misturar dados entre filiais |
| RQ-S08 | Comparação | AC-S08: diferenças de medidas comparáveis por OP/operação/componente/UM, sem somar UMs incompatíveis ou inferir erro físico; preservar evidências e qualidade por OP |
| RQ-S09 | Segurança e ownership | AC-S09: Core effective `supplies.access` e scope de filial/recurso no BFF, S2S individual conforme contrato, SQL/cálculo TOTVS somente api-delpi, sem nova permissão |
| RQ-S10 | Qualidade | AC-S10: testes positivos/irmãos/negativos, regressão E12 e detalhe atual, Help sincronizada, build, desktop/mobile, temas, teclado/foco e smoke federado autenticado |

## 3. Jornada funcional

**Modo 1 — OP conhecida:** usuário seleciona filial e digita número. Sugestões são solicitadas com debounce; ao selecionar uma OP ou confirmar código canônico completo com Enter, a consulta de detalhe carrega automaticamente. Não executar detail-per-keystroke; somente a busca leve de sugestões. Com OP já presente na URL, carregar o detalhe sem ação adicional.

**Modo 2 — Não conhece OP:** o usuário escolhe tipo de data (não confundir `C2_EMISSAO`, apontamento e encerramento), intervalo, produto e filtros adicionais. Os resultados vêm de lista paginada ordenada com descrições e situações. Ele escolhe uma OP e abre o detalhe. Campo de busca por código é apenas uma das entradas para o mesmo catálogo filtrado.

**Modo 3 — Comparar grupo de OPs:** nos resultados, usuário seleciona de 2 a N OPs. A visão de comparação mostra resumo por OP e diferenças por componente comparável, mantendo origem/destino de OPs relacionadas e unidades. Não declarar “sobreconsumo” quando execução ou baseline teórico forem inconclusivos.

**URL e estado:** separar `/consumption-audit?unit=01&op=...` de consultas exploratórias (query params versionáveis, preservando deep links antigos); estado de comparação pode usar query params compactos/bounded, evitando URLs enormes. Não colocar dados sensíveis no URL.

## 4. Arquitetura e contratos C1/C3/C4 (PROPOSED, não implementados por este documento)

- **Producer `api-delpi`:** candidato `GET /supplies/consumption-audit/orders`, com `branch`, `search`, `date_type`, `period_start`, `period_end`, `product`, `status`, `work_center`, `page`, `page_size`. Confirmar schemas/índices reais e semântica de data, status e produto antes de congelar parâmetros; não inventar filtro não suportado.
- **BFF `supplies-api`:** candidato `GET /consumption-audit/orders` com `unit` e projeção dos parâmetros autorizados, leitura via gateway S2S, validação estrita, Core AuthZ e resource scope. Sem query direta à api-delpi pelo MFE.
- **Detalhe existente C2:** manter GET por OP, sem alterar cálculos do domínio; reutilizar no clique de resultado.
- **Comparação posterior:** preferir endpoint batch bounded no producer ou composição BFF validada sem N+1; escolher owner do cálculo por domínio. Contrato batch é PROPOSED e deve preservar filial, OP, componente, UM e completeness por item.
- **Respostas:** lista paginada com `items`, `page`, `page_size`, `total` quando computável, `has_more`, `quality`/warnings se necessário. OP string 11 posições, zeros preservados. Sem “total = 0” inventado quando contagem indisponível.
- **Performance:** debounce, cancelamento de requests, limite de período e paginação; evitar scan caro de SG1/SD3 para autocomplete, N+1 e consulta de detalhe por item; instrumentar latência/query count sem estimativas.
- **Auth:** `supplies.access` efetiva via Core, manage-only não confere acesso, filiais 01/02 como filtros operacionais e trusted S2S conforme contrato atual. Nunca introduzir permission por tela ou ação.

## 5. Ordem de execução Devin e gates

| Etapa | Escopo | Gate |
|---|---|---|
| P0 | Rebaseline HEAD/status, conferir página/contratos e regras `.cursor` no código atual, inventariar C1/listagem existente e possibilidades SQL para datas/status/filtros | INVENTORY PROVEN; drift explícito |
| F1 | Producer+BFF busca leve/paginada por OP/produto, filial e período básico; OpenAPI, auth e performance | tests contract/security + integração |
| F2 | MFE remover botão, autocomplete acessível com debounce/cancelamento, seleção e URL/F5, estados completos, Help | unit/integration UI + build + smoke |
| F3 | Filtros combinados (tipo de data, status, centro/operac etc.) à medida que contratos estiverem provados; backend+UI e paginação | positive/sibling/negative + queries bounded |
| F4 | Seleção múltipla e comparação por OP, com contrato batch e regras de equivalência por UM/produto/operação | contrato + regressão + sem falsos positivos |
| F5 | Verificar end-to-end, corrigir até passar, atualizar documentação/Help e evidências, commits separados por owner | RQ/AC cobertos; regressões |
| F6 | Deploy oficial em produção somente se autorizado e após gates técnicos; smoke autenticado, SHAs/digests, rollback e avaliação visual pelo PO | DEPLOYED/TECHNICAL_GATE_PASS ou INCONCLUSIVE |

Recomenda-se **primeiro F1–F3** para que o usuário consiga encontrar OPs sem número e abrir o detalhe; comparar (F4) depois de estabilizar lista e parâmetros. Não converter requisito de comparação em permissão para implementar workflow de investigação/write no ERP.

## 6. Test matrix

| Tipo | Caso | Esperado |
|---|---|---|
| Positivo | Buscar parte do código em filial 01 | sugestões limitadas e corretas; escolher abre detalhe |
| Positivo | Buscar OPs por emissão em intervalo | itens seguem datas e filial informadas |
| Positivo | Buscar OP por apontamento | usa semântica comprovada de data de apontamento, não data de emissão |
| Irmão | OPs com mesmo produto, datas e status diferentes | filtros combinados preservam intersecção e ordenação estável |
| Irmão | OP-mãe e filhas via D4_OPORIG | não duplicar movimentos ou colapsar OPs |
| Negativo | Digitar rápido, mudar filial durante fetch | stale response ignorada/cancelada; sem vazamento |
| Negativo | Usuário manage-only/no-access, Core down, S2S inválido | 403/503/401 conforme contrato, fail-closed |
| Negativo | Intervalo invertido ou amplo, strings malformadas, paginação inválida | 400/422 e limites declarados |
| Negativo | Comparar UMs diferentes, fontes parciais | exibir separado/unknown, sem somar incompatíveis |
| Regressão | C2 detalhe via URL antiga + E12 | mesmo comportamento e sem alteração de domínio |
| UI/Runtime | mobile, teclado/foco, tema claro/escuro, F5, deep link, Help, smoke | testes/build PASS; smoke não executado = INCONCLUSIVE |

## 7. Stop conditions e evidências

Stop `EXECUTION_DRIFT` se authority/owner/contrato atual não permitir a estratégia. Não implementar filtro cujo campo SQL ou interpretação histórica não foi comprovado; sinalizar `TO_INVENTORY` e desenvolver fatias independentes. Não usar cliente-side filtering como substituto de lista paginada completa. Não criar novos grants Keycloak/RBAC, nem escrita em Core PG. Não fazer deploy sem autorização explícita e rollback conhecido.

Relatório Devin por etapa: BASE/FINAL HEAD, origin/main/status, facts PROVEN, TO_INVENTORY, files inspected/changed, contract impact, security, RQ/AC, testes com comandos, positive/sibling/negative, residual search, performance, integração, SHAs, outcome e next step. GPT review: ACCEPT / ACCEPT_WITH_RESIDUAL / REWORK / EXECUTION_DRIFT / INCONCLUSIVE.
