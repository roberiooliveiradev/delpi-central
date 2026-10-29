# 121 — CLARA × Portal: matriz de paridade funcional e de conhecimento (29/10/2026)

**Execução:** `CF-PROC0072-CLARA-PORTAL-PARITY-014`. **HEAD de referência:** `5144a32583` (main).
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

## 3. Ferramentas MCP vigentes (18 — congeladas por `MCP_TOOL_NAMES`)

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
| `prepare_governed_operation` / `commit_proposal` | PREPARE/ACT | Operações governadas unitárias |
| `prepare_batch` / `confirm_batch` / `execute_batch` | PREPARE/ACT | Lote governado com confirmação |

Operações ACT vigentes: `evidence.decide_version`, `evidence.decide_item_set`, `review.record_decision`, `clarification.open`, `clarification.resolve` — todas PREPARE → confirmação humana → execução, com recurso/escopo/auditoria.

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
| Dados R01/R02 (baixas) | `closing/…/financial-settlements` + `/summary` | nenhuma | não | — | access | READ_TOOL_GAP | handoff: contrato READ autorizado |
| Dados R03/P7 | `closing/…/stock-inventory` + `/export` | nenhuma | não | — | access | READ_TOOL_GAP | handoff idem |
| Dados R05 (movimentos) | `closing/…/stock-movements` + `/export` | nenhuma | não | — | access | READ_TOOL_GAP | handoff idem |
| Dados R08/H02 | `closing/…/work-in-process` | nenhuma | não | — | access | READ_TOOL_GAP | handoff idem |
| Matriz R01–R15 (estado) | `closing/competences/{period}/reports` | nenhuma direta | não | — | access | READ_TOOL_GAP | handoff idem |
| Exportação CSV/PDF | `…/export` (BFF) | nenhuma | — | não (UI operada pelo usuário) | access | NOT_APPLICABLE | explicar onde fica; não executar |
| Meu perfil | `me` routes | `get_my_context` (parcial) | parcial | — | access | PARITY_PASS (info) | — |
| Minhas tarefas | `me`/`pendencies` | `list_pendencies` (parcial) | parcial | — | access | PARITY_PASS (info) | — |
| Cockpit consolidado | `cockpit` view | `get_competence_state` (parcial) | parcial | — | access | PARITY_PASS (info) | — |
| Superfícies MANAGE | `admin_*` routes | nenhuma | não | não | manage | NOT_APPLICABLE | administração é superfície do Portal |
| Consentimento ACT | `closing/clara-consent` | challenge nativo MCP | — | governado | access | PARITY_PASS | — |

**Leitura da matriz:** a CLARA *conhece* (corpus) e *orienta* (navegação) todas as superfícies implementadas. O que ela *consulta ao vivo* hoje: estado/checklist/documentos/P3/pendências/pacotes/bloqueios/lotes. O que ela **não** consulta ao vivo: datasets dos relatórios operacionais (R01/R02/R03/R05/R08) e a matriz de cobertura — lacuna de ferramenta, não de autorização. Exportações são operação do usuário no Portal.

## 5. Relatórios operacionais — estado e postura

| ID | Título | Origem | Superfície | Escopos/filtros | Export | Paridade oficial |
|---|---|---|---|---|---|---|
| R01 | Baixas a pagar | TOTVS/SE5 | financial-settlements | competência, filtros SE5, agrupamentos, `/summary` | — | PENDING (auxiliar) |
| R02 | Baixas a receber | TOTVS/SE5 | financial-settlements | idem; produtor custom E1 incompleto | — | PENDING (auxiliar) |
| R03/P7 | Posição de estoque | TOTVS/SB9 | stock-inventory | `all_products`/`mp_pi_pa`, filial, armazém, totais por tipo/armazém | CSV/PDF | PENDING (MATR460) |
| R05 | Entradas/saídas | TOTVS/SD1–SD4 | stock-movements | seleção, agrupamentos, saldo (MATR320) | CSV/PDF | PENDING |
| R08/H02 | Material em processo | TOTVS/SD3–SC2 | work-in-process | físico H02, alocado em OP, totais (MATR989) | CSV/PDF | PENDING; alimenta P3 |
| R04, R06, R07, R09, R12, R15 | consumo OP, CPV/Kardex, inventários, Fat×MOD, wizard, cutoff | — | PENDING_CONTRACT | — | — | PLANNED (pacotes 014–017) |
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
| 014 | R06 CPV/Kardex + R07 inventários | PLANNED (gate contratual) |
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
- *O R06 já está implementado?* Não — pacote 014 PLANNED (doc 120). [planejado]
- *Quem valida evidências?* Ações governadas exigem PREPARE + confirmação humana; CLARA propõe, não decide sozinha. [governado]

## 13. Limites declarados

- Nenhuma ferramenta READ de relatório foi criada nesta execução (gate contratual pendente — §11).
- Nenhuma permission, tool, contrato ou capability foi adicionada; `MCP_TOOL_NAMES` permanece com 18 nomes.
- Respostas simuladas não são evidência de runtime; validação conversacional autenticada permanece gate separado.
