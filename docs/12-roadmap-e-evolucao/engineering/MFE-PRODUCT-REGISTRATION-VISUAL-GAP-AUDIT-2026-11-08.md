# PRC MFE — Auditoria de gaps pós-DEV: declaração de conclusão vs tela real

> **Data:** 2026-11-08 · **Owner revisão:** Coordination / Portal Engenharia · **Status:** `VISUAL_ACCEPTANCE_FAIL / EXECUTION_DRIFT / REMEDIATION_REQUIRED / PRODUCTION_DEPLOY_SUSPENDED`
>
> **Origem das evidências:** screenshots DEV/localhost fornecidas pelo PO após entrega `1f1c09f288`, cruzadas com arquivos atuais em GitHub (default branch). **Não foi executada** suíte browser nem inspecionadas respostas HTTP autenticadas nesta auditoria; causas de runtime não demonstradas são hipóteses e exigem debug.
>
> **Decisões originais:** [REF-001..011](./MFE-PRODUCT-REGISTRATION-POST-REDESIGN-REFINEMENT-PLAN.md), [plano Devin](./MFE-PRODUCT-REGISTRATION-DEVIN-IMPLEMENTATION-PLAN.md). Este documento corrige classificação prematura `PASS` da entrega do agente; não reverte os commits.

## 1. Constatações da inspeção visual (não confundir screenshot com evidência de backend)

| ID | Captura/sintoma | Avaliação | Evidência adicional no código |
|---|---|---|---|
| REF-001 | Campo de revisão-base não visto nas capturas desta rodada | `CODE_REPORTED_PASS / BROWSER_NOT_VERIFIED` | validação de update real ainda necessária |
| REF-002 | Ícone da home não exibido nas capturas desta rodada | `BROWSER_NOT_VERIFIED` | commit reporta ícone |
| REF-003 | Tabela atual não exibe coluna Abrir | `VISUAL_PASS` | `DataTableSection onRowClick`; teclado exige teste |
| REF-004 | Botão Colunas aparece | `PARTIAL` | abrir/ocultar/reordenar/persistir não provado |
| REF-005 | Indicadores de sort no cabeçalho aparecem | `PARTIAL` | sort global server-side reportado, sem teste browser multi-page |
| **REF-006** | **Cards mostra “Nenhum resultado para os filtros aplicados” enquanto Tabela contém 6 casos e Kanban mostra os 6** | **`FAIL_RUNTIME`** | `PrcQueuePage.tsx` passa `list.items.map` como children a `EngineeringDataCardsGrid`; suspeita de contrato/slots/estrutura do componente, A VERIFICAR, não supor conserto por CSS |
| REF-007 | Hero detalhado compacto e abas próximas | `VISUAL_PASS_PARTIAL` | conteúdo restante ainda requer review por breakpoints |
| **REF-008** | **Histórico continua sem avatar/nome/e-mail de cada ator; aparece “Responsável não identificado” repetidamente e o evento final ainda mostra `verify_and_complete`** | **`FAIL_UX / LEGACY_IDENTITY_GAP`** | `PrcTimelineSection.tsx` concatena `actorLabel`, `actor_email` e canal em string `meta`, sem `EngineeringInitialsAvatar`; rótulo técnico precisa ser humanizado |
| **REF-009** | Solicitante tem avatar/nome, mas responsáveis ainda são “não identificado” ou `analyst-pg` como texto técnico | `PARTIAL / IDENTITY_CONTRACT_GAP` | snapshot V013 não resolve legados nem subject sem display |
| **REF-010** | **Ficha Nova solicitação continua verticalizada e campos ocupam largura integral, apesar de grid planejado; fornecedores não demonstrados em tabela real** | **`FAIL_VISUAL`** | `PrcCreatePage.tsx` usa `engineering-prc__edit-list`, cuja regra é `display:flex; flex-direction:column`; `engineering-prc__form-grid` existe mas não está aplicado ao `FIELD_GROUPS.map`. Fornecedores usam `<div className=engineering-prc__supplier-row>`, não uma tabela com thead/colunas |
| **REF-011** | **Campos Grupo, Tipo, Unidade, Armazém e Conta aparecem como inputs vazios na captura, não selects oficiais** | **`FAIL_VISUAL_OR_RUNTIME_DEPENDENCY`** | `renderSheetField` só renderiza `EngineeringSelectField` se `catalogs[path]?.length`; quando catálogo falha/vem vazio, faz fallback a `EngineeringTextField`. Necessário investigar 401/403/5xx, schema/URL, resposta, estado; não declarar catálogo oficial entregue sem seleção real; fonte indisponível não deve virar opção livre silenciosa |
| Todos | Nenhuma captura de fornecedores selecionados, browser mobile, clique de linha, sorting, CREATE/UPDATE concluídos | `TEST_NOT_RUN` | ausência de evidência não implica erro, mas impede aceite |

## 2. Causas/problemas objetivos a corrigir

### G-01 / Cards vazio apesar de itens em Tabela e Kanban — P0

Reproduzir na mesma sessão/filtros; inspecionar props do `EngineeringDataCardsGrid` criado via façade `engineeringUi.ts`, verificar se espera `items`, `cards`, children em outro slot, `empty` e requisitos de view-model. Verificar React runtime, logs e DOM; não apenas remover estado vazio. Escrever teste de integração com pelo menos 2 itens reais/fake contratualmente fiéis e garantir mesma cardinalidade do data set da página em Tabela/Cards/Kanban. Não inventar fetch extra.

### G-02 / Wizard permanece lista vertical — P0

Refatorar `FIELD_GROUPS.map` em `PrcCreatePage.tsx` para usar **grid no wrapper real de `renderSheetField`**, com span específico para descrição, proporções para grupo/tipo/unidade e armazém/conta/terceiros/referência. Remover/diversificar bordas da classe `engineering-prc__edit-row` que reforçam estilo de lista. Testar com largura DEV 1600px, 1024px, 390px e zoom 200%. `engineering-prc__form-grid` ociosa não equivale a grid implementado.

### G-03 / Fornecedores não estão em tabela editável — P0

Implementar `table` semanticamente acessível ou componente real do kit com célula editável, com `thead`: `Fornecedor (busca código/nome)`, `Loja`, `Nome`, `Part Number`, `Catálogo`, `Ações`. Uma linha por vínculo; código/loja/nome decorrentes de seleção SA2 e read-only após seleção; PN/catálogo editáveis; adicionar/remover com foco; atualização seletiva/motivo, identidades code+store e zeros à esquerda. Não declarar PASS por `display:grid` em uma div. Em mobile adaptar por cards de fornecedor com rótulos, mesma semântica e dados.

### G-04 / Seletores TOTVS falham em runtime — P0

Inspecionar no browser autenticado URL, resposta, Authorization, permissões, query, kind, payload DTO de cada catálogo (grupo, unidade, armazém, conta), enum oficial de Tipo/Terceiros. Corrigir owner correto (Engineering API / api-delpi) e testes do router novo que anteriormente ficaram `TEST_NOT_RUN`. Não manter fallback para texto livre **silencioso** como se tivesse seleção oficial. Quando a fonte não responder, apresentar erro de referência + retry e impedir escolha não validada, salvo regra formal de exceção e verificação backend. Logs sem tokens.

### G-05 / Timeline de identidade — P1

Na UI, renderizar `EngineeringInitialsAvatar` + nome + e-mail autorizado em um componente de evento, não apenas `meta` string. Verificar suporte a rich content/slots do `EngineeringTimeline`; se inadequado, compor uma timeline semântica local usando componentes do kit com a11y. Legados pré-V013 não possuem display: verificar contrato batch de diretório governado; nunca inventar identidade ou usar usuário logado como ator. Converter `verify_and_complete` em “Verificação oficial e conclusão” mantendo metadata técnica em detalhe.

### G-06 / Assignee legado — P1

Resolver apresentações de `assignedTo` para fila, cards, board e hero via projeção autorizada/batch; não exibir login técnico `analyst-pg` como nome de exibição; sem N+1 não autorizado. Distinção `Não atribuído` vs `Identidade indisponível`.

### G-07 / Cobertura insuficiente e release gate — P0

Executar browser E2E real em DEV com JWT de usuário autorizado, screenshots em desktop/tablet/mobile, testes de teclado, cadastro CREATE/UPDATE, fornecedores SA2, falhas dos catálogos, ordenação/paginação, view switching, V013 legados e tokens válidos/403. Executar suite dedicada do router novo `api-delpi`, PostgreSQL real, e regressão `httpClient`; testes no SHA final. Contrato entre owners em revisão antes de extensão. Atualizar/recriar **somente** containers DEV afetados, conferir bundle fingerprint/response, não deploy em PROD.

## 3. Critérios de reaceite obrigatórios

- [ ] Same filters: 6 itens na Tabela = 6 cards = 6 cards Kanban (apenas como exemplo da fixture de 6); números globais permanecem agregados e honestos.
- [ ] Campo descrição amplo; grupo/tipo/unidade na mesma linha desktop; armazém/conta e terceiros/referência lado a lado; fornecedores em tabela editável.
- [ ] Catálogos TOTVS comprovados com code+description e seleção real; indisponibilidade **não** se converte em texto livre silencioso.
- [ ] Busca SA2 por código/nome com código+loja+nome e seleção oficial; PN e catálogo complementados pelo usuário.
- [ ] Timeline tem avatar/nome/e-mail quando autorizados; legacy fallback diferenciado; ações humanizadas.
- [ ] Responsável exibe identidade resolvida ou fallback correto, sem atribuição indevida.
- [ ] Screenshots reais desktop/tablet/mobile, URL e SHA servidos, video/steps de interações críticas.
- [ ] Nenhum regression de CAS, idempotência, allowedActions, histórico imutável, REST/EVA, BFF-only.
- [ ] `PRODUCTION_DEPLOY_SUSPENDED` até aceite visual explícito do PO e homologação funcional governada.

## 4. Outcome corrigido

**Não classificar os 11 itens como PASS.** Estado `EXECUTION_DRIFT` entre “entregue” e “comportamento observado”; revisar matriz REF por evidência. `BUILD_PASS` e `VITEST_PASS` não substituem captura/browser runtime. **Próxima tarefa:** `ENG-PRC-D6-REMEDIATE-VISUAL-AND-RUNTIME-GAPS`, somente DEV, com P0 antes de P1 e evidência de regressão.
