# 121 — CLARA × Portal: matriz de paridade funcional e de conhecimento (29/10/2026)

**Execuções:** `CF-PROC0072-CLARA-PORTAL-PARITY-014` (matriz de conhecimento) e `CF-PROC0072-CLARA-FULL-FUNCTIONAL-PARITY-016` (matriz operacional completa — §14+). **HEAD de referência:** `5144a32583` (main).
**Natureza:** matriz canônica de paridade entre o que o Portal Controladoria & Finanças implementa e o que a CLARA conhece/consulta/executa — **não** é autorização de novas capabilities nem homologação de relatórios.
**Autoridades:** HEAD (implementação), runtime observado em `srv-api`, TÉO (AS-IS), doc 118 (processo), doc 85 (regras de negócio), doc 113 (fluxo canônico), doc 119 (contratos P7), doc 120 (plano de evolução), `pluginRoutes.ts`/`pluginRouteCatalog.ts`/`shellNav.ts` (navegação), `reports_routes.REPORT_CATALOG` (matriz R01–R15), `constants.TOOL_CLASS` (ferramentas MCP).

## 1. Superfícies do Portal — implementadas × planejadas

| Superfície | Rota/Âncora | Estado | Capability |
|---|---|---|---|
| Início (hub) | basePath `/apps/controllership-finance` (`/home` redireciona) | IMPLEMENTADO | access, access.dre |
| Fechamento mensal — Visão geral | `closing/monthly-closing` (`?tab` ausente) | IMPLEMENTADO (aba) | access |
| Fechamento mensal — Documentos e interações | `closing/monthly-closing?tab=documents` | IMPLEMENTADO (aba) | access |
| Fechamento mensal — Relatórios e divergências | `closing/monthly-closing?tab=reports` (`&report=…`) | IMPLEMENTADO (aba) | access |
| Baixas financeiras R01/R02 | `closing/financial-settlements` | IMPLEMENTADO | access |
| Estoque histórico R03/P7 | `closing/stock-inventory` | IMPLEMENTADO | access |
| Checklist da competência | `closing/checklist` (+`/{period}`) | IMPLEMENTADO | access |
| Pendências (P4) | `closing/pendencies` | IMPLEMENTADO | access |
| Pacotes e revisões (P5) | `closing/packages` (+`/{period}`) | IMPLEMENTADO | access |
| Cockpit da competência (P1) | `closing/cockpit` (+`/{period}`) | IMPLEMENTADO | access |
| Minhas tarefas | `closing/my-tasks` | IMPLEMENTADO (rota; fora da top-nav desta release por escopo adiado) | access |
| Consentimento CLARA (ACT) | `closing/clara-consent` | IMPLEMENTADO | access |
| Documentos recebidos (DRE) | `closing/documents` | IMPLEMENTADO | access.dre |
| Meu perfil | `profile` | IMPLEMENTADO | access |
| Administração do checklist | `closing/admin` (+ versão, documento, eventos) | IMPLEMENTADO | manage |
| Documentos do fechamento (catálogo mestre) | `closing/admin/documents` | IMPLEMENTADO | manage |
| Catálogos governados | `closing/admin/catalogs` | IMPLEMENTADO | manage |
| Visão geral **dedicada** | — | PLANEJADO (hoje é aba do Fechamento mensal) | — |
| Sala de interação | — | PLANEJADO (doc 24; sem rota em runtime) | — |
| Ajuda dedicada | — | PLANEJADO (hoje: tooltips contextuais `helpTooltips`) | — |

## 2. Navegação canônica (como orientar o usuário)

- **Top-nav:** apenas «Início» nesta release (interno e DRE). Demais itens entram quando a rota existir.
- **Hub Início:** seções «Portal» (Início, Meu perfil) e «Central de Fechamento» (Fechamento mensal; Documentos e interações `?tab=documents`; Relatórios e divergências `?tab=reports`; sob `manage`: Administração do checklist, Documentos do fechamento, Catálogos governados). Público DRE vê apenas a seção `closing_dre` (Fechamento Mensal → `closing/documents`).
- **Busca global:** `Ctrl+K` no shell abre a paleta de caminhos/funcionalidades indexadas por `pluginRouteCatalog` (keywords PT/EN).
- **Deep routes:** `closing/{checklist|packages|cockpit|monthly-closing}/{AAAA-MM}`; relatório na aba via `?tab=reports&report=<id>`; filtros de documentos na query.
- **Competência:** selecionada na visão (mês de referência `AAAA-MM`); parâmetro `period` das ferramentas CLARA segue o mesmo formato.

## 3. Ferramentas MCP vigentes (43 — congeladas por `MCP_TOOL_NAMES`; execução 016 ampliou 18→43)

| Ferramenta | Classe | Cobre |
|---|---|---|
| `get_catalog` | DISCOVERY | Catálogo de ferramentas + agent_directives (persona) |
| `list_knowledge_sources` | DISCOVERY | Fontes/versão do corpus publicado |
| `get_my_context` | READ | Contexto do usuário autenticado |
| `get_competence_state` | READ | Estado da competência (período) |
| `get_checklist_items` | READ | Itens do checklist da competência |
| `list_documents` | READ | Documentos/evidências da competência |
| `get_p3_reconciliation` | READ | Conciliação governada P3 (fonte/estado) |
| `list_pendencies` | READ | Fila P4 de pendências |
| `get_package_review` | READ | Revisão de pacote P5 |
| `get_batch_status` | READ | Estado de lote governado |
| `search_closing_knowledge` | READ | Busca no corpus com citações |
| `get_knowledge_item` | READ | Item do corpus com proveniência |
| `analyze_closing_blockers` | ANALYSIS | Bloqueios da competência |
| `list_competences` | READ | Lista de competências (rota canônica) |
| `get_competence` | READ | Detalhe da competência |
| `get_checklist_item` | READ | Detalhe de item do checklist |
| `get_closing_cockpit` | READ | Cockpit consolidado P1 |
| `list_my_tasks` | READ | Fila «Minhas tarefas» do usuário |
| `get_pendency` | READ | Pendência + histórico de eventos |
| `list_p3_events` | READ | Auditoria/eventos P3 |
| `get_package` | READ | Detalhe do pacote (versões/esclarecimentos) |
| `get_document` | READ | Documento+versões+mensagens+ajustes(+auditoria) |
| `get_item_validation` | READ | Decisões e correções do item |
| `lookup_participants` | READ | Nomes de participantes do documento |
| `get_financial_settlements` | READ | Baixas R01/R02 — dados reais api-delpi |
| `get_financial_settlements_summary` | READ | Totais das baixas no período |
| `get_stock_inventory` | READ | R03/P7 posição de estoque |
| `get_stock_movements` | READ | R05 entradas/saídas (MATR320) |
| `get_work_in_process` | READ | R08/H02 material em processo |
| `get_stock_reconciliation` | READ | Conciliação analítica R05−P7−H02 (IDENTITY_ONLY) |
| `get_report_matrix` | READ | Matriz R01–R15 de cobertura |
| `list_closing_catalogs` | READ | Catálogos governados (manage) |
| `list_catalog_entries` | READ | Entradas de catálogo (manage) |
| `list_checklist_templates` | READ | Templates/versões de checklist (manage) |
| `get_checklist_template_version` | READ | Versão de template com itens (manage) |
| `list_received_deliveries` | READ | Entregas ao destinatário (dre) |
| `get_received_delivery` | READ | Entrega da competência (dre) |
| `get_received_document` | READ | Documento recebido + ajustes (dre) |
| `prepare_governed_operation` / `commit_proposal` | PREPARE/ACT | Operações governadas unitárias |
| `prepare_batch` / `confirm_batch` / `execute_batch` | PREPARE/ACT | Lote governado com confirmação |

Capabilities ACT vigentes (48): `evidence.decide_version`, `evidence.decide_item_set`, `review.record_decision`, `clarification.open`, `clarification.resolve`, `competence.open`, `pendency.create`, `pendency.claim`, `pendency.reassign`, `pendency.transition`, `pendency.confirm_classification`, `p3.confirm_cutoff`, `p3.upsert_reconciliation`, `p3.revalidate`, `package.finalize`, `package.reopen`, `package.complement`, `package.submit_review`, `package.assignment_create`, `package.assignment_deactivate`, `package.start_review`, `package.confirm_terminal_rejection`, `package.revert_terminal_rejection`, `item.reverse_decision`, `item.mark_not_applicable`, `item.revert_not_applicable`, `item.cancel`, `item.create_exceptional`, `item.request_correction`, `item.review_correction`, `document.post_message`, `document.cancel`, `document.answer_adjustment`, `received.post_message`, `received.create_adjustment`, `received.confirm_adjustment`, `catalog.entry_create`, `catalog.entry_update`, `catalog.entry_deactivate`, `catalog.entry_reactivate`, `checklist.draft_create`, `checklist.draft_update`, `checklist.version_submit`, `checklist.version_return`, `checklist.version_discard`, `checklist.version_publish`, `checklist.version_inactivate`, `checklist.doc_requirement` — todas PREPARE → confirmação humana Portal → execução, com recurso/escopo/auditoria (`mcp/clara`).

## 4. Matriz CLARA × Portal

| Funcionalidade | Endpoint/contrato | Ferramenta CLARA | READ | ACT | Permissão | Paridade | Ação |
|---|---|---|---|---|---|---|---|
| Estado da competência | `closing/competences/{period}` | `get_competence_state` | sim | — | access | PARITY_PASS | — |
| Checklist | `closing/competences/{period}/checklist` | `get_checklist_items` | sim | via proposal | access | PARITY_PASS | — |
| Documentos/evidências | `closing/competences/{period}/documents` | `list_documents` | sim | `evidence.decide_*` governado | access | PARITY_PASS | — |
| Conciliação P3 governada | `p3` routes | `get_p3_reconciliation` | sim | sem write (não promove fonte) | access | PARITY_PASS | — |
| Pendências P4 | `pendencies` routes | `list_pendencies` | sim | — | access | PARITY_PASS | — |
| Revisão de pacote P5 | `packages` routes | `get_package_review` | sim | `review.record_decision` governado | access | PARITY_PASS | — |
| Esclarecimentos | validations routes | via proposal `clarification.*` | parcial | governado | access | PARITY_PASS | — |
| Bloqueios/análise | derivado | `analyze_closing_blockers` | sim | — | access | PARITY_PASS | — |
| Conhecimento do processo | corpus publicado | `search_closing_knowledge`/`get_knowledge_item` | sim | — | access | KNOWLEDGE_GAP→resolvido (sync §8) | publicar corpus |
| Dados R01/R02 (baixas) | `closing/…/financial-settlements` + `/summary` | `get_financial_settlements` / `…_summary` | sim | — | access | PARITY_PASS (exec. 016) | — |
| Dados R03/P7 | `closing/…/stock-inventory` + `/export` | `get_stock_inventory` | sim | — | access | PARITY_PASS (exec. 016) | — |
| Dados R05 (movimentos) | `closing/…/stock-movements` + `/export` | `get_stock_movements` | sim | — | access | PARITY_PASS (exec. 016) | — |
| Dados R08/H02 | `closing/…/work-in-process` | `get_work_in_process` | sim | — | access | PARITY_PASS (exec. 016) | — |
| Matriz R01–R15 (estado) | `closing/competences/{period}/reports` | `get_report_matrix` | sim | — | access | PARITY_PASS (exec. 016) | — |
| Conciliação analítica | `…/analytics/stock-reconciliation` | `get_stock_reconciliation` | sim | — | access | PARITY_PASS (exec. 016) | — |
| Exportação CSV/PDF | `…/export` (BFF) | nenhuma | — | não (UI operada pelo usuário) | access | NOT_APPLICABLE | explicar onde fica; não executar |
| Meu perfil | `me` routes | `get_my_context` (parcial) | parcial | — | access | PARITY_PASS (info) | — |
| Minhas tarefas | `me`/`pendencies` | `list_my_tasks` | sim | — | access | PARITY_PASS (exec. 016) | — |
| Cockpit consolidado | `cockpit` view | `get_closing_cockpit` | sim | — | access | PARITY_PASS (exec. 016) | — |
| Superfícies MANAGE | `admin_*` routes | tools READ + capabilities manage (exec. 016) | sim | governado | manage | PARITY_PASS | — |
| Consentimento ACT | `closing/clara-consent` | challenge nativo MCP | — | governado | access | PARITY_PASS | — |

**Leitura da matriz (após exec. 016):** a CLARA *conhece* (corpus), *orienta* (navegação), *consulta ao vivo* e *executa escritas governadas* em todas as superfícies implementadas do Portal — inclusive datasets R01/R02/R03/R05/R08, matriz de cobertura, cockpit e administração manage. Restam fora do canal apenas operações de arquivo/binário (download/upload/export) e superfícies de perfil/viewer — `PORTAL_ONLY` por natureza de payload, não por gap de autorização (§16).

## 5. Relatórios operacionais — estado e postura

| ID | Título | Origem | Superfície | Escopos/filtros | Export | Paridade oficial |
|---|---|---|---|---|---|---|
| R01 | Baixas a pagar | TOTVS/SE5 | financial-settlements | competência, filtros SE5, agrupamentos, `/summary` | — | PENDING (auxiliar) |
| R02 | Baixas a receber | TOTVS/SE5 | financial-settlements | idem; produtor custom E1 incompleto | — | PENDING (auxiliar) |
| R03/P7 | Posição de estoque | TOTVS/SB9 | stock-inventory | `all_products`/`mp_pi_pa`, filial, armazém, totais por tipo/armazém | CSV/PDF | PENDING (MATR460) |
| R05 | Entradas/saídas | TOTVS/SD1–SD4 | stock-movements | seleção, agrupamentos, saldo (MATR320) | CSV/PDF | PENDING |
| R08/H02 | Material em processo | TOTVS/SD3–SC2 | work-in-process | físico H02, alocado em OP, totais (MATR989) | CSV/PDF | PENDING; alimenta P3 |
| R04, R09, R12, R15 | consumo OP, Fat×MOD, wizard, cutoff | — | PENDING_CONTRACT | — | — | PLANNED (pacotes 016–017; R04/R13/R14 depois) |
| R06, R07 | CPV/Kardex (MATR910), inventários | — | PENDING_CONTRACT (gate 014 executado — contratos TARGET no doc 122) | — | — | PLANNED — implementação aguarda `CF-PROC0072-R06-R07-IMPLEMENTATION-015` |
| R10, R11 | centro de custo, NF a desconsiderar | Controladoria | MANUAL_EVIDENCE | — | — | evidência documental P2 |
| R13, R14 | extratos/aplicações, importações/câmbio | instituições financeiras | EXTERNAL | — | — | evidência anexada validada |

P7 — medidas distintas a não misturar: histórico SB9 (ex-99), em estoque, em processo físico, material alocado e total geral; escopo `mp_pi_pa` filtra MP/PI/PA pelo tipo canônico B1_TIPO; `all_products` cobre o universo completo. Competências sem posição histórica não inventam dados — explicar ausência.

## 6. Conciliação analítica (`IDENTITY_ONLY`) e P3 governado

- A composição `R05 − P7 − H02 = R$ 0,00` é identidade **entre parcelas do mesmo universo SB9** — composição de saldos consistente, não paridade entre emissões oficiais independentes. `IDENTITY_ONLY` **não** é homologação.
- Homologação oficial compara período, filial, escopo, versão e `as_of` contra os relatórios oficiais (MATR320/MATR460/MATR989) — frente separada, ainda `PENDING`.
- P3 governado tem registro próprio (fonte registrada/não registrada, elegível, incompleta, divergência, cutoff, bloqueios, revalidação, conclusão). **Ausência de registro P3 ≠ relatório indisponível**; consulta operacional não vira fonte governada automaticamente.
- A CLARA consulta o estado P3 via `get_p3_reconciliation`; **não recalcula** operandos e não declara fechamento por divergência zero.

## 7. Independência documental (regra aprovada)

Consulta operacional, cálculo analítico e exportação **não dependem** de documento cadastrado. Fluxo: consultar → analisar → exportar PDF → «Documentos e interações» → anexar → validar → disponibilizar. Anexo é posterior; envio à DRE segue fluxo próprio (`closing/documents`, `access.dre`). PDF operacional com paridade pendente **não é** relatório oficial homologado e não gera documento automaticamente.

## 8. Conhecimento — sincronização do corpus (esta execução)

- Corpus anterior: `5d546360-ab37-410c-80e8-e1a5748ed56e` (27/10/2026 09:11 -03; 56 fontes, 1.713 itens) — anterior aos REWORK-010/011/012, ao P7 gate-final e ao doc 120.
- Fontes do manifest alteradas desde a publicação (re-ingestão automática por supersede): docs 23, 85, 94, 112, 113, README.
- Fontes novas autorizadas por esta execução (adicionadas ao manifest): docs **49** (contrato P7), **91** (gate documentos históricos/DRE), **115** (DRE-ACCESS-019), **116/117** (inteligência do processo real), **118** (base canônica), **119** (contratos P7 definitivos), **120** (plano R06–R15 + CLARA) e **121** (esta matriz).
- Procedimento governado: `corpus_ingestion --docs-root <repo>` no ambiente com acesso a docs e `postgres-plugins`; nova versão/hash comprovados por `list_knowledge_sources` + buscas com citação. **Não** editar versão/hash manualmente.

## 9. Segurança e permissões (preservadas)

`controllership-finance.access`, `controllership-finance.manage`, `controllership-finance.access.dre` — nenhuma permission nova por relatório, página ou unidade. Analista `.access`: consultas internas autorizadas. `.manage`: somente administração compatível. `.access.dre`: somente documentos disponibilizados (seção `closing_dre`) — sem dados internos. Sem permissão: negação fail-closed. JWT nunca é autoridade final; effective permission do Core decide.

## 10. Plano de evolução — PLANNED (doc 120)

| Pacote | Escopo | Estado |
|---|---|---|
| 014 | R06 CPV/Kardex + R07 inventários | PLANNED — gate contratual executado (doc 122); implementação aguarda aprovação IMPLEMENTATION-015 |
| 015 | R10 centro de custo + R11 NF a desconsiderar | PLANNED |
| 016 | R09 Faturamento × MOD | PLANNED (lacunas E9/G5) |
| 017 | R12 estado de custos + R15 cutoff | PLANNED (READ-only de estado) |
| depois | R04, R13, R14 | PLANNED (dependem de produtores/fontes) |

A CLARA não oferece consultas de relatórios futuros como publicados; distingue sempre IMPLEMENTADO de PLANNED/PENDING_CONTRACT.

## 11. Gaps e handoffs

| Gap | Classificação | Owner | Ação |
|---|---|---|---|
| Datasets R01/R02/R03/R05/R08 e matriz de cobertura não legíveis via MCP | READ_TOOL_GAP | owner CLARA+BFF | `DECISION_REQUIRED`: contrato READ autorizado (adapter ao contrato BFF vigente, sem SQL direto nem duplicação de cálculo) |
| Export CSV/PDF fora do MCP | NOT_APPLICABLE | Portal | permanece operação do usuário na UI |
| Sala de interação / Ajuda dedicada / Visão geral dedicada | PLANNED | Portal | sem rota; não anunciar |
| Corpus desatualizado | KNOWLEDGE_GAP | CLARA pipeline | resolvido nesta execução (§8) |
| Doc 30 (reuse map) e 114 (proposta DR-1/DR-2) | NOT_APPLICABLE | — | fora do corpus: dev/proposta, não conhecimento de paridade |

## 12. Matriz de perguntas de referência (CP12)

- *Onde encontro Relatórios e divergências?* Início → Central de Fechamento → «Relatórios e divergências» (Fechamento mensal, aba `?tab=reports`). [implementado]
- *Como seleciono uma competência?* Campo «Mês de referência» (`AAAA-MM`) na visão; relatórios e deep routes carregam o período. [implementado]
- *Como abro o P7?* Aba Relatórios e divergências → matriz → R03, ou `closing/stock-inventory`; escopos `all_products`/`mp_pi_pa`, filial, armazém; exportação CSV/PDF no topo da consulta. [implementado]
- *Qual a diferença entre P7 completo e MP/PI/PA?* `all_products` = universo; `mp_pi_pa` = matéria-prima/produto intermediário/produto acabado via tipo canônico. Medidas distintas (§5). [implementado]
- *Onde exporto PDF?* Botão de exportação da própria consulta no Portal (R03/R05/R08); a CLARA explica, não exporta. [implementado; NOT_APPLICABLE para MCP]
- *Quais relatórios existem?* §5 — cinco consultas operacionais (R01/R02/R03/R05/R08) + matriz R01–R15 com cobertura; demais R-IDs pendentes de contrato ou evidência manual. [implementado+planejado]
- *Divergência zero significa conciliado?* Não — `IDENTITY_ONLY` é composição consistente de saldos SB9, não paridade oficial (§6). [conhecimento]
- *O que falta para homologação oficial?* Comparação contra emissões oficiais com mesmo período/filial/escopo/`as_of` — frente PENDING. [conhecimento]
- *Preciso cadastrar documento para consultar relatório?* Não — consulta/análise/exportação independentes (§7). [implementado]
- *O que um usuário DRE vê?* Somente «Fechamento Mensal → Documentos e interações» do que a Controladoria disponibilizou. [implementado]
- *O R06 já está implementado?* Não — pacote 014 com contratos TARGET aprovados em design (doc 122); implementação aguarda gate de execução. [planejado]
- *Quem valida evidências?* Ações governadas exigem PREPARE + confirmação humana; CLARA propõe, não decide sozinha. [governado]

## 13. Limites declarados (execução 014 — histórico)

- Nenhuma ferramenta READ de relatório foi criada na execução 014 (gate contratual pendente — §11 histórico). O gap foi resolvido pela execução 016: os mesmos contratos BFF passaram a ser servidos por ferramentas READ (§14).
- Respostas simuladas não são evidência de runtime; validação conversacional autenticada permanece gate separado.

## 14. Matriz operacional completa Portal × CLARA (execução 016)

Matriz verificável de **toda** operação do BFF no HEAD. Classes: **A**=READ (sem confirmação), **B**=escrita rotineira reversível, **C**=escrita governada (PREPARE→consentimento Portal→ACT obrigatório pela política vigente), **D**=destrutiva/irreversível (confirmação explícita + governança). Política vigente (CLARA-D01=B, docs 94/106): **toda** escrita MCP passa pelo fluxo governado — classes B/C/D convergem em PREPARE/ACT hoje; execução direta de classe B é mudança de política (`DECISION_REQUIRED`, §16). GATE = permission efetiva revalidada no backend: `access` / `manage` / `dre` (`access.dre`).

### 14.1 Competi­cia / fechamento

| Operação | Endpoint BFF | Classe | Gate | MCP | Confirmação |
|---|---|---|---|---|---|
| Listar competências | `GET /closing/competences` | A | access | tool `list_competences` | — |
| Abrir competência | `POST /closing/competences/open` | C | access | cap `competence.open` | consentimento Portal |
| Detalhe da competência | `GET /closing/competences/{period}` | A | access | tool `get_competence` | — |
| Itens do checklist | `GET …/{period}/items` | A | access | tool `get_checklist_items` | — |
| Detalhe do item | `GET …/{period}/items/{key}` | A | access | tool `get_checklist_item` | — |
| Estado mensal | `GET …/packages/{period}/monthly-state` | A | access | tool `get_competence_state` | — |
| Cockpit | `GET …/packages/{period}/cockpit` | A | access | tool `get_closing_cockpit` | — |
| Minhas tarefas | `GET /me/tasks` | A | access | tool `list_my_tasks` | — |

### 14.2 Validações / evidências / itens

| Operação | Endpoint BFF | Classe | Gate | MCP | Confirmação |
|---|---|---|---|---|---|
| Validar evidência | `POST …/documents/{id}/evidence` | C | manage | cap `evidence.decide_version` | consentimento |
| Decidir conjunto do item | `POST …/items/{key}/evidence-set` | C | manage | cap `evidence.decide_item_set` | consentimento |
| Reverter rejeição | `POST …/decisions/{id}/reverse` | C | manage | cap `item.reverse_decision` | consentimento |
| Marcar N/A | `POST …/items/{key}/not-applicable` | C | access | cap `item.mark_not_applicable` | consentimento |
| Reverter N/A | `POST …/not-applicable/revert` | C | access | cap `item.revert_not_applicable` | consentimento |
| Cancelar item | `DELETE …/items/{key}` | D | access | cap `item.cancel` | consentimento (destrutivo) |
| Item excepcional | `POST …/items/exceptional` | C | access | cap `item.create_exceptional` | consentimento |
| Pedir correção | `POST …/items/{key}/corrections` | C | access | cap `item.request_correction` | consentimento |
| Revisar correção | `POST …/corrections/{id}/review` | C | manage | cap `item.review_correction` | consentimento |
| Validação do item | `GET …/items/{key}/validation` | A | access | tool `get_item_validation` | — |
| Correções do item | `GET …/items/{key}/corrections` | A | access | tool `get_item_validation` | — |

### 14.3 Pendências P4

| Operação | Endpoint BFF | Classe | Gate | MCP | Confirmação |
|---|---|---|---|---|---|
| Listar | `GET …/pendencies` | A | access | tool `list_pendencies` | — |
| Detalhe + histórico | `GET …/pendencies/{id}` (+`/history`) | A | access | tool `get_pendency` | — |
| Criar | `POST …/pendencies` | C | access | cap `pendency.create` | consentimento |
| Assumir | `POST …/{id}/claim` | C | access | cap `pendency.claim` | consentimento |
| Reatribuir | `POST …/{id}/reassign` | C | manage | cap `pendency.reassign` | consentimento |
| Transicionar | `POST …/{id}/transition` | C | access (DISMISSED→manage) | cap `pendency.transition` | consentimento |
| Confirmar classificação | `POST …/{id}/classification` | C | manage | cap `pendency.confirm_classification` | consentimento |

### 14.4 P3 — cutoff e conciliação governada

| Operação | Endpoint BFF | Classe | Gate | MCP | Confirmação |
|---|---|---|---|---|---|
| Estado P3 | `GET …/p3/{period}` | A | access | tool `get_p3_reconciliation` | — |
| Eventos P3 | `GET …/p3/{period}/events` | A | access | tool `list_p3_events` | — |
| Confirmar cutoff | `POST …/p3/{period}/cutoff` | C | manage | cap `p3.confirm_cutoff` | consentimento |
| Registrar fonte | `PUT …/p3/{period}/reconciliations/{domain}` | C | manage | cap `p3.upsert_reconciliation` | consentimento |
| Revalidar | `POST …/p3/{period}/revalidate` | C | manage | cap `p3.revalidate` | consentimento |

### 14.5 Pacotes e revisão P5

| Operação | Endpoint BFF | Classe | Gate | MCP | Confirmação |
|---|---|---|---|---|---|
| Listar pacotes | `GET …/packages/{period}` | A | access | tool `get_package_review` | — |
| Detalhe do pacote | `GET …/packages/{period}/{id}` | A | access | tool `get_package` | — |
| Finalizar pacote | `POST …/finalize` | C | manage | cap `package.finalize` | consentimento |
| Reabrir versão | `POST …/versions/{id}/reopen` | C | manage | cap `package.reopen` | consentimento |
| Criar complemento | `POST …/versions/{id}/complement` | C | manage | cap `package.complement` | consentimento |
| Submeter à revisão | `POST …/versions/{id}/submit` | C | manage | cap `package.submit_review` | consentimento |
| Atribuir revisor | `POST …/assignments` | C | manage | cap `package.assignment_create` | consentimento |
| Desativar atribuição | `POST …/assignments/{id}/deactivate` | C | manage | cap `package.assignment_deactivate` | consentimento |
| Iniciar revisão | `POST …/versions/{id}/start-review` | C | access | cap `package.start_review` | consentimento |
| Registrar decisão | `POST …/versions/{id}/decisions` | C | access | cap `review.record_decision` | consentimento |
| Abrir esclarecimento | `POST …/versions/{id}/clarifications` | C | access | cap `clarification.open` | consentimento |
| Responder esclarecimento | `POST …/clarifications/{id}/resolve` | C | manage | cap `clarification.resolve` | consentimento |
| Rejeição terminal | `POST …/terminal-rejection` | D | access | cap `package.confirm_terminal_rejection` | consentimento (destrutivo) |
| Reverter rejeição terminal | `POST …/terminal-rejection/revert` | C | access | cap `package.revert_terminal_rejection` | consentimento |

### 14.6 Documentos internos (Controladoria)

| Operação | Endpoint BFF | Classe | Gate | MCP | Confirmação |
|---|---|---|---|---|---|
| Listar | `GET …/documents` | A | access | tool `list_documents` | — |
| Detalhe+versões+mensagens+ajustes+auditoria | `GET …/documents/{id}` (+versions/messages/adjustments/audit) | A | access | tool `get_document` | — |
| Download binário | `GET …/documents/{id}/versions/{n}/download` | A | access | **PORTAL_ONLY** (bytes não trafegam no canal) | — |
| Upload/substituição de arquivo | `POST …/documents` / `…/versions` | C | access | **PORTAL_ONLY** (multipart; CLARA direciona à superfície) | — |
| Cancelar documento | `POST …/documents/{id}/cancel` | D | access (uploader-ou-manage) | cap `document.cancel` | consentimento (destrutivo) |
| Mensagem interna | `POST …/documents/{id}/messages` | B→governado | access | cap `document.post_message` | consentimento (política vigente) |
| Responder solicitação de ajuste | `POST …/adjustment-requests/{id}/answer` | B→governado | access | cap `document.answer_adjustment` | consentimento |
| Buscar participantes | `POST …/documents/{id}/participants/lookup` | A | access | tool `lookup_participants` | — |
| Avatar participante | `GET …/participants/{uid}/avatar` | A | access | **PORTAL_ONLY** (binário) | — |

### 14.7 Documentos recebidos (experiência DRE)

| Operação | Endpoint BFF | Classe | Gate | MCP | Confirmação |
|---|---|---|---|---|---|
| Entregas | `GET /received/deliveries` | A | dre | tool `list_received_deliveries` | — |
| Entrega por competência | `GET /received/{period}` | A | dre | tool `get_received_delivery` | — |
| Documento+mensagens+pedidos | `GET /received/{period}/documents/{id}` | A | dre | tool `get_received_document` | — |
| Download | `GET …/download` | A | dre | **PORTAL_ONLY** | — |
| Mensagem DRE | `POST …/messages` | B→governado | dre | cap `received.post_message` | consentimento |
| Pedido de ajuste | `POST …/adjustment-requests` | B→governado | dre | cap `received.create_adjustment` | consentimento |
| Confirmar ajuste | `POST …/adjustment-requests/{id}/confirm` | B→governado | dre | cap `received.confirm_adjustment` | consentimento |

### 14.8 Administração (manage)

| Operação | Endpoint BFF | Classe | Gate | MCP | Confirmação |
|---|---|---|---|---|---|
| Catálogos | `GET /admin/catalogs` | A | manage | tool `list_closing_catalogs` | — |
| Entradas de catálogo | `GET /admin/catalogs/{key}/entries` | A | manage | tool `list_catalog_entries` | — |
| Criar entrada | `POST /admin/catalogs/{key}/entries` | C | manage | cap `catalog.entry_create` | consentimento |
| Atualizar entrada | `PUT …/entries/{code}` | C | manage | cap `catalog.entry_update` | consentimento |
| Desativar entrada | `DELETE …/entries/{code}` | C (soft-delete reversível) | manage | cap `catalog.entry_deactivate` | consentimento |
| Reativar entrada | `POST …/entries/{code}/reactivate` | C | manage | cap `catalog.entry_reactivate` | consentimento |
| Templates de checklist | `GET /admin/checklist/templates` (+versions/version/events) | A | manage | tools `list_checklist_templates`, `get_checklist_template_version` | — |
| Criar rascunho | `POST …/templates/{id}/drafts` | C | manage | cap `checklist.draft_create` | consentimento |
| Editar rascunho | `PUT …/versions/{v}/items` | C | manage | cap `checklist.draft_update` | consentimento |
| Submeter versão | `POST …/versions/{v}/submit-review` | C | manage | cap `checklist.version_submit` | consentimento |
| Devolver a rascunho | `POST …/versions/{v}/return-to-draft` | C | manage | cap `checklist.version_return` | consentimento |
| Descartar versão | `DELETE …/versions/{v}` | D | manage | cap `checklist.version_discard` | consentimento (destrutivo) |
| Publicar versão | `POST …/versions/{v}/publish` | C | manage | cap `checklist.version_publish` | consentimento |
| Inativar versão | `POST …/versions/{v}/inactivate` | C | manage | cap `checklist.version_inactivate` | consentimento |
| Requisito de documento | `PUT …/templates/{id}/items/{key}/document-requirement` | C | manage | cap `checklist.doc_requirement` | consentimento |

### 14.9 Relatórios e análises operacionais (api-delpi delegado)

| Operação | Endpoint BFF | Classe | Gate | MCP | Confirmação |
|---|---|---|---|---|---|
| Baixas R01/R02 | `GET …/financial-settlements` | A | access | tool `get_financial_settlements` | — |
| Totais R01/R02 | `GET …/financial-settlements/summary` | A | access | tool `get_financial_settlements_summary` | — |
| P7 estoque R03 | `GET …/stock-inventory` | A | access | tool `get_stock_inventory` | — |
| Movimentos R05 | `GET …/stock-movements` | A | access | tool `get_stock_movements` | — |
| H02/R08 | `GET …/work-in-process` | A | access | tool `get_work_in_process` | — |
| Conciliação analítica | `GET …/analytics/stock-reconciliation` | A | access | tool `get_stock_reconciliation` | — |
| Matriz R01–R15 | `GET …/reports` | A | access | tool `get_report_matrix` | — |
| Exportações CSV/PDF | `…/export` | A | access | **PORTAL_ONLY** (binário; CLARA entrega link da superfície) | — |

Todos os READ de relatório invocam a **mesma função de rota BFF** com a request reconstruída — mesma autorização, mesmo bearer delegado ao api-delpi, mesmo envelope e mesmos erros tipados; nenhum SQL/cálculo duplicado no MCP.

## 15. Comportamento de consentimento (política aplicada)

- Classe A: executa direto, sem confirmação — cobre «sem confirmações redundantes» para todo READ.
- Classes B/C/D: PREPARE → consentimento Portal (`clara-consent`) → ACT, ou `prepare_batch` → uma confirmação consolidada → `execute_batch`. Para planos com várias operações o lote já elimina confirmação por operação — a UX sem redundância é satisfeita **pelo mecanismo aprovado**.
- `DECISION_REQUIRED` — execução direta de classe B sem desafio Portal: exigiria alterar a política de consentimento (owner: segurança/plataforma, doc 106 §3). Alternativa recomendada **sem mudança de política**: `prepare_batch` com confirmação consolidada única. Recomendação: manter step-up para qualquer efeito externo; avaliar extensão do consentimento a «sessão autorizada» somente com análise de segurança dedicada.
- Apertos de paridade AuthZ corrigidos na execução 016: `evidence.decide_version`, `evidence.decide_item_set`, `item.reverse_decision`, `item.review_correction` e `clarification.resolve` passam a exigir `manage` — igual às rotas Portal (antes qualquer `access` chegava ao PREPARE).

## 16. Operações fora do canal MCP (PORTAL_ONLY)

| Operação | Motivo |
|---|---|
| Download de binários (documento interno/DRE, avatar) | bytes não trafegam no MCP; CLARA entrega deep-link autenticado |
| Upload/substituição de evidência | multipart/antivírus/tamanho; fluxo autenticado do Portal preservado (§10 do pedido) |
| Export CSV/PDF de relatórios | payload binário + runtime dedicado; CLARA explica/localiza |
| `me` perfil completo, `viewer-context`, fotos | superfícies de UI; `get_my_context` cobre identidade mínima |
