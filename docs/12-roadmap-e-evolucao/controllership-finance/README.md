# Portal Controladoria & Finanças — Fonte de navegação e estado

> **Consolidação documental: 19/10/2026.** Primeira funcionalidade: **Central de Fechamento**, processo **PROC-0072**. Documentação `TARGET`, sem implementação de runtime. Este README é o **único painel de estado vigente**; relatórios antigos de A12/A14/A15/A16 são evidências datadas, não gates atuais.

## 1. Identidade e boundaries congelados

| Contrato | Valor |
|---|---|
| Plugin / produto | `controllership-finance` |
| MFE | `plugins/controllership-finance` |
| basePath MFE | `/apps/controllership-finance` |
| BFF | `controllership-finance-api` |
| baseUrl BFF | `/apps/controllership-finance-api` |
| Permissões, **somente** | `controllership-finance.access` e `controllership-finance.manage` |

**Core API** é owner de identidade, usuários, grupos/RBAC e permissões efetivas; **Portal CF não administra permissões**. A BFF autoriza operações de negócio por capability efetiva **AND** vínculo/ownership **AND** escopo do recurso **AND** regra de negócio; fail-closed. JWT não é authority de permissions. Filial/unidade é dimensão de dado, não permission code. MFE consome sua BFF, nunca chama `api-delpi` do browser. `api-delpi` mantém regras canônicas TOTVS/Protheus e `strategic-indicators-api` mantém indicadores/metas. Integrações por ports/adapters e contratos, sem imports ou bancos de domínios alheios.

Seguir [instruções oficiais do GPT Arquiteto](../../11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md), regras `.cursor` aplicáveis e [padrão visual da plataforma](../../11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md). **`@delpi/plugin-ui` first.**

## 2. Estado **vigente** e gates

| Controle | Estado em 19/10/2026 |
|---|---|
| AS-IS PROC-0072 | `PROVEN / TÉO CLOSED_ACCEPTED` |
| Decisões de produto C2, P5-A..J, DEC-01..04, D-FINAL-02 | `TARGET / PO_APPROVED` |
| Roadmap V1 documentado | `PASS` **somente documental** |
| A12 / A14 / A15 / A16 | `INCONCLUSIVE` — revalidar com evidência de HEAD |
| `PORTAL_DESIGN_FREEZE` / `PRODUCT_CONTRACT_FREEZE` | **`PASS / IMP-F0_ONLY`** — aprovação multi-role declarada em [doc 45 §13](./45-g0-excecao-fastapi-e-fechamento-gates.md); outros slices requerem novo gate |
| `SECURITY_MODEL_FREEZE` / `TEST_STRATEGY_FREEZE` | **`PASS / IMP-F0_ONLY`** — somente dois endpoints públicos e fundação; stale RBAC segue pendente para rotas protegidas ([doc 45 §13](./45-g0-excecao-fastapi-e-fechamento-gates.md)) |
| `FASTAPI_ARCHITECTURAL_EXCEPTION` | **`VALIDATED / IMP-F0_ONLY`** — exceção exclusiva desta BFF, sem alterar padrão global ([doc 45 §13](./45-g0-excecao-fastapi-e-fechamento-gates.md)) |
| `DOCUMENTATION_CLOSURE_COMPLETE` | **`PASS / IMP-F0_ONLY`** — decisão PO após freezes escopados, [doc 45 §13](./45-g0-excecao-fastapi-e-fechamento-gates.md) |
| `IMPLEMENTATION_AUTHORIZED` | **`YES / IMP-F0_ONLY`** — GO restrito à fundação da BFF FastAPI, Compose/gateway e testes; não autoriza MFE nem rotas de negócio ([doc 45 §13](./45-g0-excecao-fastapi-e-fechamento-gates.md)) |
| IMP-F0: escopo técnico aprovado pelo PO | `PO_APPROVED / SCOPE_ONLY` — BFF FastAPI + Docker/Compose/gateway + health/ready + testes; não equivale ao GO transversal ([doc 45 §12](./45-g0-excecao-fastapi-e-fechamento-gates.md)) |
| Portal runtime, smoke, integração live | `NOT_IMPLEMENTED / TEST_NOT_RUN` |

**Regra humana aprovada (D-FINAL-02):** somente pessoas aprovam. Sem revisores elegíveis ou áreas configuradas, **não** criar trava artificial de finalização, envio ou publicação. O pacote pode entrar em revisão, mas **sem evento humano real de aceite não há conclusão mensal** — o processo permanece pendente. C2 também exige aceite de cada área obrigatória existente na versão vigente, todos os pacotes aplicáveis submetidos, nenhuma clarification aberta e ausência de rejeição terminal. Veja **somente** o [contrato canônico P5 — doc 37](./37-p5-submissao-e-revisao-no-portal.md) para todas as decisões P5.

**Residuais de implementação / inventário:** Core T05 e contrato S2S da informação corporativa usada para elegibilidade de revisor; vínculo do coordenador por competência; snapshots P6, DTO/estados/eventos/OCC P5; fonte canônica ERP T03 para P3; testes de integração, UX e Help. Não são autorização para criar nova permission, CRUD/Core shadow, tabelas ou endpoints sem owner. **Busca sem resultado não prova ausência.**

## 2.1 Decisões posteriores — IMP-MFE-HOME (19/10/2026)

**Registro canônico: [doc 45 §14](./45-g0-excecao-fastapi-e-fechamento-gates.md).** Após inventário READ/VERIFY do MFE + Home, o responsável aprovou expressamente:

| Controle | Estado e consequência |
|---|---|
| **D1=A / D-G0-05** | `APPROVED / IMP-MFE-HOME_ONLY`: reads podem usar somente effective permissions previamente validadas dentro da janela stale máxima de 900s do `delpi_auth`; sem snapshot válido, fail-closed; writes futuros requerem refresh e gate próprio; rotas humanas exigem `principal_type=="user"`. Obrigatória verificação de revogação, expiração e Core indisponível no HEAD. |
| **D2=A** | `APPROVED / CONTRACT TARGET`: BFF `GET /viewer-context` com `firstName` e `capabilities: {access, manage}`, identidade/permissions dos owners Core e autorização humana `access`. DTO/envelope e testes producer/consumer ainda requerem verificação pré-GO. |
| **D3=A** | `APPROVED / DEFERRED`: favoritos não entram no slice inicial; sem persistência fictícia nem botões inertes. |
| **IMP-MFE-HOME** | `DECISIONS_APPROVED / GATE_PREPARATION`. **IMPLEMENTATION_AUTHORIZED = NO para este novo slice até GO humano expresso após G1**, distinto do GO `IMP-F0_ONLY`. |
| Runtime MFE/Home | `NOT_IMPLEMENTED / TEST_NOT_RUN` até evidência executada. |

**Próximo passo:** revalidar no HEAD os contratos e testes do [doc 45 §14](./45-g0-excecao-fastapi-e-fechamento-gates.md), fechar o gate específico e solicitar GO de execução MFE + Home; não antecipar frontend, rota protegida ou deploy antes do gate.

### GO posterior — IMP-MFE-HOME (2026-10-20)

Após o G1 de verificação técnica (HEAD de evidência `6cfb4ea7c3`) e resposta expressa **"autorizo"** à solicitação de GO específico, **`IMPLEMENTATION_AUTHORIZED = YES / IMP-MFE-HOME_ONLY`**, conforme [doc 45 §14.1](./45-g0-excecao-fastapi-e-fechamento-gates.md).

**Escopo exclusivamente autorizado:** MFE/bootstrap/shell/Home real, `GET /viewer-context` protegido na BFF, Compose dev da BFF/MFE e Compose prod do MFE, testes e Help contextual. Decisões D1=A, D2=A e D3=A mantidas. **Não autoriza deploy em produção, registro de manifesto produtivo, páginas futuras, P1–P6 ou novas permissões.** Runtime e testes deste slice permanecem `NOT_IMPLEMENTED / TEST_NOT_RUN` até relatório de execução verificável; revalidar HEAD e worktree na execução.

### IMP-08/P1 — Gate vigente de Cockpit (decisão de 20/10/2026)

**Registro canônico:** [doc 45 §15](./45-g0-excecao-fastapi-e-fechamento-gates.md). O PO aprovou `D1=A, D2=B, D3=C` após o inventário READ/VERIFY de P1:

| Controle | Estado |
|---|---|
| D1=A: rota `/apps/controllership-finance/closing/competence`, `?competence=` | `APPROVED / TARGET_ONLY` — o identificador de competência ainda depende do contrato real |
| D2=B: producers e competência primeiro | `APPROVED / READ_ONLY_PREDECESSOR` — não construir cockpit de três eixos permanentemente indisponíveis |
| D3=C: owner/persistência | `TO_INVENTORY / DECISION_REQUIRED_DEFERRED` — sem banco/migration por antecipação |
| Implementação IMP-08/P1 | **`NO_GO / IMPLEMENTATION_AUTHORIZED=NO`**; T01/T03/T05 e contratos P2/P3/P5 sem produtores comprovados |
| Próximo passo | Inventário com producers e owners Core/api-delpi/P2/P5/P6 e provenance TÉO; reportar contratos físicos, RQ/AC, lacunas e gate do primeiro predecessor de negócio |

A implementação já autorizada de IMP-MFE-HOME **não** autoriza a página P1; readiness documental e screenshot não provam fontes operacionais. Nenhum código runtime é aprovado para P1 nesta decisão.

### T01 — Inventário de relatórios e fontes (20/10/2026)

**Novo documento versionado:** [46 — T01 REPORT-SOURCE-INVENTORY V1](./46-t01-report-source-inventory-v1.md). Levantamento parcial a partir do TÉO (processo/decomposição/diagrama), docs 02/03/17/21/45 do GitHub, inventário técnico CF-CLOSING-PREDECESSORS-01 e discovery do DAVI.

Status: `REPORT_CATALOG=DOCUMENTED_PARTIAL`; `TABLE_COLUMN_BINDINGS=TO_INVENTORY`; `SQL_PARITY=TEST_NOT_RUN`; `VIDEO_TIMECODES=STALE_EVIDENCE`; `T03_STOCK_CLOSED=PENDING_OWNER`; `IMP-08/P1=NO_GO`. Proibido inferir equivalência de saídas com endpoints adjacentes. Próximo passo: confirmar relatórios originais/vídeo e pesquisar metadados SQL tipados DAVI antes dos contratos api-delpi→BFF. Nenhuma nova autorização de runtime.

### Acompanhamento quantitativo T01 — Relatórios, tabelas e colunas

**Controle vivo:** [47 — Tracker de coleta, colunas e paridade](./47-t01-report-column-audit-tracker-v1.md), baseado nos 15 itens do [46](./46-t01-report-source-inventory-v1.md). Cada item possui seis gates objetivos (etapa/evidência, campos/filtros de saída, tipo/owner da fonte, bindings SQL ou contrato externo, paridade/validação, aceite). Percentuais de coleta, auditoria e itens concluídos incluem numerador/denominador; expansão de escopo requer registro e alteração explícita do denominador.

**Baseline de abertura (20/10/2026):** `0/60` coleta, `0/90` auditoria; **após rodada L1.1 FINR190:** `2/60 = 3,3%` de critérios de coleta atestados, `2/90 = 2,2%` de auditoria atestados, `0/15 = 0,0%` de itens encerrados (documento 47 §6). Isso não apaga o inventário documental já existente: apenas distingue catalogação de evidência validada por critério. Nenhuma nova implementação está autorizada por este tracker.

### R01/R02 — contrato documental de rotas (20/10/2026)

[48 — Design TARGET de baixas financeiras e contratos api-delpi → BFF](./48-r01-r02-financial-settlements-api-contract-target.md): endpoints e DTOs **propostos**, campos e fontes do DAVI auditados, limitações dos joins e matriz RQ/AC. `DESIGN_DRAFT=READY_FOR_PO_REVIEW`; `D1..D5=DECISION_REQUIRED`; `IMPLEMENTATION_AUTHORIZED=NO`. Dados `FK1/FK2/FK7/SE1/SE2/SED` comprovados em leitura não demonstram a saída `_F190C`, cuja paridade segue `TEST_NOT_RUN`. Sem alteração de runtime.

## 3. Mapa curto de fontes canônicas

| Assunto | Fonte a ler |
|---|---|
| Autoridades, escopo, AS-IS e provenance | [00 — Governança](./00-governanca-e-authorities.md) · [01 — Produto/naming](./01-visao-produto-naming-e-escopo.md) · [02 — PROC-0072 AS-IS](./02-proc-0072-as-is-e-baseline.md) · [03 — Evidências](./03-evidencias-proveniencia-e-rastreabilidade.md) · [19 — TÉO](./19-rastreabilidade-teo.md) |
| Regras de negócio, arquitetura e UX | [04 — Regras](./04-regras-de-negocio-consolidadas.md) · [05 — Gaps](./05-diagnostico-gaps-e-oportunidades.md) · [06 — TO-BE](./06-arquitetura-funcional-to-be.md) · [07 — Jornadas](./07-ux-jornadas-e-estados-de-experiencia.md) |
| Central P1–P6 | [08 — P1](./08-p1-cockpit-da-competencia.md) · [09 — P2](./09-p2-checklist-e-documentos.md) · [10 — P3](./10-p3-estoque-cutoff-e-conciliacao.md) · [15.1 — Paridade P3](./15.1-p3-criterios-paridade-monetaria.md) · [11 — P4](./11-p4-classificacoes-e-pendencias.md) · [12 — P5](./12-p5-pacote-finalizacao-e-envio.md) · [13 — P6](./13-p6-administracao-e-configuracao.md) |
| **Aprovação e revisão P5 (única authority temática de decisões)** | **[37 — Submissão/revisão no Portal, C2, P5-A..J, DEC-01..04 e D-FINAL-02](./37-p5-submissao-e-revisao-no-portal.md)** |
| Segurança, catálogos, bounded contexts | [14 — Segurança](./14-seguranca-rbac-auditoria-e-ia.md) · [16 — Catálogos/notificações](./16-configuracoes-catalogos-e-notificacoes.md) · [21 — Owners/boundaries](./21-boundaries-produtos-e-owners.md) |
| Páginas comuns (padrão visual) | [24 — Navegação](./24-inicio-e-navegacao-principal.md) · [31 — Página do usuário](./31-pagina-do-usuario.md) · [32 — Início](./32-inicio-home.md) · [25 — Visão geral](./25-visao-geral-indicadores-financeiros.md) · [26 — Sala](./26-sala-de-interacao.md) · [27 — Minhas tarefas](./27-minhas-tarefas.md) · [28 — Administração](./28-administracao.md) · [29 — Ajuda](./29-ajuda.md) · [30 — Reuso UI](./30-plugin-ui-reuse-map.md) |
| **Requisitos, aceites e teste por ID** | **[23 — Ledger RQ/AC/Testes](./23-ledger-rq-ac-testes.md)** · [15 — Critérios gerais](./15-requisitos-criterios-de-aceite-e-testes.md) |
| Pendências técnicas / handoff atual | [17 — Inventários E/T](./17-backlog-de-confirmacoes-e-inventarios.md) · [18 — Readiness](./18-readiness-e-handoff-de-implementacao.md) · [22 — Handoff P1–P6](./22-handoff-implementacao-p1-p6.md) |
| **Roadmap e execução** | **[39 — Roadmap V1](./39-roadmap-mestre-implementacao-v1.md)** · [40 — Slices/dependências](./40-matriz-dependencias-e-slices-v1.md) · [41 — Testes/gates](./41-estrategia-validacao-e-gates-implementacao-v1.md) · [42 — Playbook Cursor](./42-playbook-brief-cursor-execution-report-v1.md) · [43 — Rollout](./43-rollout-operacao-e-handoff-v1.md) |
| Decisões de implementação G0 | [45 — Exceção FastAPI e gates](./45-g0-excecao-fastapi-e-fechamento-gates.md) |

**Histórico de análise, não normas atuais nem PASS inferido:** [20 — cobertura histórica](./20-transforma-plus-coverage.md), [33 — fechamento documental](./33-plano-mestre-fechamento-documental.md), [34 — review A14](./34-revisao-transversal-gate-v2.md), [35 — review A15](./35-contratos-regras-scripts-test-matrix-gate-v2.md), [36 — delivery externo superseded](./36-e04-t04-package-delivery-decision-packet.md), [38 — rebaseline após merge](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md), [44 — evidências A16](./44-a16-revalidacao-final-transversal-2026-10-16.md). Preservados para proveniência; se conflitarem com 37/23/39 e HEAD, prevalecem sources mais altas.

### R01/R02 — decisão de filial nullable e próximo gate (20/10/2026)

[Doc 48 §§9–11 — rotas financeiras, decisão D3.1 e gate](./48-r01-r02-financial-settlements-api-contract-target.md): PO aprovou campo `branchCode` nullable no DTO e evolução backend-first, sem preencher filial artificialmente ou exigir paridade com `_F190C`. **Separação de acesso não foi dispensada**: fontes têm filial vazia nas probes, portanto `BRANCH_ENFORCEMENT=PENDING`, `API_DELPI_PERMISSION=DECISION_REQUIRED`, `IMPLEMENTATION_AUTHORIZED=NO` para endpoints com dados reais. Próximo passo: fechamento de contrato e testes de isolamento antes do GO explícito. BFF, MFE e exportação permanecem fora do slice.

## 4. Sequência de coordenação para o próximo chat

1. **IMP-00 — READ/INVENTORY/VERIFY (sem runtime):** HEAD + `git status` no checkout, Project Instructions, `.cursor`, contratos/Core e owners, diff e CI; confirmar gates A12/A14/A15/A16 aplicáveis **sem reabrir escolhas já aprovadas**. Produzir brief preciso do primeiro slice e decisão `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.
2. **Gate IMP-F0 aprovado e restrito:** GO documental no [doc 45 §13](./45-g0-excecao-fastapi-e-fechamento-gates.md). Executar apenas a fundação da BFF, Compose/gateway, testes e smoke. Para novos slices, renovar o gate e avaliar residuais específicos; autorização inicial não se propaga.
3. **Após aceite técnico da BFF IMP-F0:** abrir autorização específica de MFE + Home (doc 32). IMP-01 / A01 permanece planejado como deep route, sem implementação nesta autorização. UI PT-BR, mobile/desktop, claro/escuro, teclado/foco e Help no mesmo gate.

Navegação comum: **Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda** (ordem do menu, não necessariamente ordem de PRs). Nenhuma route/page future placeholder sem capability real. A Ajuda acompanha cada slice, não só a página Ajuda final.

**Conclusão:** **IMP-F0 autorizado documentalmente, apenas para a BFF de fundação**; código, container e smoke seguem `NOT_IMPLEMENTED / TEST_NOT_RUN` até execução com evidência. Demais slices sem GO. Revalidar HEAD no novo chat.

### D3 R01/R02 — decisão de audiência (20/10/2026)

PO aprovou dataset financeiro compartilhado read-only para baixas a pagar/receber. A audiência é o conjunto de usuários humanos designados com effective `controllership-finance.access` pelo Core; sem lista/permissão extra por relatório ou filial. `manage` isolado não permite leitura. Ver [doc 48 §13](./48-r01-r02-financial-settlements-api-contract-target.md). **Ainda sem GO de exposição em produção:** enforcement, testes e smoke reais pendentes; `branchCode=null`, D4 e ausência de totais oficiais preservados.
