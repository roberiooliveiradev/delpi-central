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

### D4 R01/R02 — auditoria de movimentos (20/10/2026)

Auditoria read-only publicada em [doc 48 §16](./48-r01-r02-financial-settlements-api-contract-target.md) e [doc 47 complemento L1.7](./47-t01-report-column-audit-tracker-v1.md): catálogo FKB, comportamento observado de BA/VL/ES/CP, direções P/R, pareamento de estornos e reconciliação SQL × API. **NET_FORMULA=DECISION_REQUIRED**: F1/F2/F3 são hipóteses de apuração para homologação pela Controladoria, não totais oficiais. `officialTotals:false`; sem alteração de runtime ou liberação adicional. Próxima etapa: homologação do owner financeiro e eventual confronto com FINR190 de competência encerrada.


### T01 — Encerramento operacional R01/R02 e sequência R03 (decisão PO, 20/10/2026)

**R01/R02:** fonte, tabelas/colunas/joins, contratos api-delpi/BFF e tela de baixas implementados; docs 46–48. A consulta real e sua reconciliação com a fonte SQL foram reportadas e os componentes constam no GitHub. **Não existe neste pacote evidência de export FINR190/`_F190C` recebida e comparada; `REPORT_EXPORT_EVIDENCE=NOT_PROVIDED` e `EXPORT_PARITY=TEST_NOT_RUN`.** A paridade oficial será retomada com o arquivo original no fechamento completo. D4 total líquido/estornos permanece pendente do owner; `officialTotals=false`.

**Próximo relatório do catálogo:** **R03 — P7 padrão / layout Bloco H (MATR460)**; R04 é **MATR860** consumo por OP, relatório distinto. Começar por TÉO AS-IS, documentação de evidência/export, DAVI SQL read-only e inventário físico; não inventar correspondência nem permitir deploy por analogia. [Inventário de relatórios doc 46 §9](./46-t01-report-source-inventory-v1.md) · [Registro de decisão e pendência export doc 48 §17](./48-r01-r02-financial-settlements-api-contract-target.md).


### R03 — P7/MATR460: auditoria Fase A registrada (20/10/2026)

[Fonte de evidência: doc 46 §10](./46-t01-report-source-inventory-v1.md). O DAVI comprovou `SB9010` em 30/09/2026 (7.929 linhas; filial 01 com 4.812, filial 02 com 3.117), cadastro `SB1010`, parâmetros em `SX6010` e 19 tabelas históricas `H_%`. Para filial 01, a soma bruta `B9_VINI1=3.884.439,52`; o agrupamento de `B1_TIPO=II` soma **266.321,45**, igual ao subtotal Insumos citado pela análise derivada do NotebookLM. Essa coincidência **não prova paridade completa**: o P7 padrão derivado é **3.776.994,69**, diferença de **107.444,83** ainda não explicada. Vídeo original/timecodes divergentes, sem PDF exportado e sem regra completa MATR460 homologada. `R03_PHASE_A=ACCEPT_WITH_RESIDUAL`; `P7_EXPORT_PARITY=TEST_NOT_RUN`; `R03_IMPLEMENTATION=NOT_AUTHORIZED`. Próximo passo: Fase B de reprodução fundamentada com parâmetros, custo/estoque em processo, ADVPL e comparação com export, quando disponível.

**Regra de persistência aprovada pelo PO:** registrar cada achado comprovado, hipótese, fonte, SQL/período/parâmetros, pendência e decisão nos documentos canônicos do GitHub durante cada rodada, não apenas no relatório da conversa; atualizar o README como índice de estado. Nenhum `PASS` inferido sem evidência.


### R03 — Fase B1, prova de reprodução SQL controlada (20/10/2026)

[Relatório e evidências: doc 46 §11](./46-t01-report-source-inventory-v1.md). A auditoria read-only da filial 01 em 30/09/2026 confrontou `SB9/B9_VINI1`, classificação SB1, armazéns 01/98/99, quantidade zero/negativa, parâmetros reais SX6 e existência de perguntas SX1. **Não reproduziu o total P7** relatado pelo NotebookLM: SB9 bruto 3.884.439,52 versus P7 derivado 3.776.994,69 (diferença 107.444,83), enquanto Insumos/II coincide (266.321,45). Excluir armazéns 98/99 sem evidência produz outro total e **não é regra aceita**. Identificador efetivo das perguntas SX1 e código/versão/customizações MATR460 não foram comprovados. `R03_PHASE_B1=ACCEPT_WITH_RESIDUAL` (auditoria); `P7_FULL_REPRODUCTION=INCONCLUSIVE`; `EXPORT_PARITY=TEST_NOT_RUN`. Prosseguir com inventário SX1/ADVPL/layout e critérios de custeio antes de contratos/runtime.


### Consolidação de aprendizado R03 — proveniência, dados e gates (20/10/2026)

**Mapa atualizado:** [doc 03 — proveniência e revisão crítica da resposta NotebookLM](./03-evidencias-proveniencia-e-rastreabilidade.md#r03--p7matr460-proveniência-consolidada-após-fases-a-e-b1-20102026); [doc 46 §§10–11 — consultas, schema, parâmetros, resultados e lacunas](./46-t01-report-source-inventory-v1.md). `TÉO=AS_IS`, `DAVI=SQL_PROVEN`, `NOTEBOOKLM=DERIVED`, `GitHub=TARGET`.

**Aprendizado validado:** P7 padrão (conferência interna) e layout Bloco H (saída distinta) são R03/MATR460, não R04/MATR860; posição em `SB9010` de 30/09/2026 e cadastro `SB1010` existem, com subtotal tipo II de **266.321,45** coincidente com relato NotebookLM, mas `SUM(B9_VINI1)=3.884.439,52` versus total derivado **3.776.994,69**, diferença **107.444,83** sem explicação. Tabelas físicas `H_` e parâmetros `SX6010` inventariados, perguntas `SX1010`/algoritmo ADVPL ainda pendentes. Conciliação final deve chegar a **R$0,00**, não a tolerância suposta. Timecodes derivados conflitantes com MP4 catalogado, original/export P7 não examinados nesta rodada.

**Gate de saída:** `R03_PHASE_A=ACCEPT_WITH_RESIDUAL`; `R03_PHASE_B1=ACCEPT_WITH_RESIDUAL` (auditoria, não reprodução); `P7_REPRODUCTION=INCONCLUSIVE`; `VIDEO_DIRECT_REVIEW=TEST_NOT_RUN`; `EXPORT_PARITY=TEST_NOT_RUN`; `R03_RUNTIME_AUTHORIZATION=NO`. **Próxima ação:** inventariar grupo efetivo SX1/versão e ADVPL/trace da rotina, obter PDF e perguntas originais, explicar diferenças linha/grupo e validar corte operacional antes de contrato ou runtime. Não extrapolar silêncio da busca como ausência de fonte.


### R03 — Alerta de drift da SB9 em setembro/2026 (21/10/2026)

Nova rechecagem DAVI constatou que `SB9010` para **30/09/2026, filial 01** retorna **zero linhas**, embora auditoria de 20/10/2026 tenha comprovado **4.812 linhas e 3.884.439,52** para a mesma seleção. A filial 02 de setembro permanece com 3.117 linhas. Causa não comprovada: `EXECUTION_DRIFT`; a divergência histórica de 107.444,83 contra o P7 relatado pelo NotebookLM é agora `STALE_EVIDENCE` para fins de comparação com o estado atual. Consulta de junho/julho/agosto não reproduziu o total P7 derivado por mera troca de competência. [Detalhes e números: doc 46 §12](./46-t01-report-source-inventory-v1.md). **Bloqueio de paridade:** verificar contexto/alteração na origem com TI-Protheus/api-delpi e obter export original com parâmetros; não inferir causa nem reconstruir dados.


### PROC-0072 — índice de vídeo derivado do NotebookLM (21/10/2026)

O PO forneceu índice de janelas para Acompanha Custos, Custo Reposição, Refaz Saldos, financeiro, CPV/Kardex, Entradas/Saídas, P7 padrão/H, H02, SD1/CC e extratos. **Persistido em [doc 46 §13](./46-t01-report-source-inventory-v1.md)** como `INFORMED_DERIVED`, **não** `OBSERVED_VISUAL`: o NotebookLM afirma vídeo de 01:02:15, enquanto arquivo anteriormente catalogado tem 00:54:44.125; há timecodes sobrepostos e `_F190C` diverge de extração anterior. Usar apenas como roteiro para conferência de prints e vídeo, sem inferir execução concluída, rotina ADVPL, dependência ou regra operacional. `VIDEO_DIRECT_VERIFICATION=TEST_NOT_RUN`; `TIMECODE_PROVENANCE=STALE_EVIDENCE`.


### PROC-0072 — Transcrição NotebookLM recebida, cronologia textual revisada (21/10/2026)

Arquivo anexo do PO `PROC-0072_Transcricao_Integral_Video.md` analisado. **[Doc 46 §14](./46-t01-report-source-inventory-v1.md)** documenta o confronto entre falas e índice: seções do arquivo apresentam horários deslocados (ex.: P7 fala **00:18:50–00:20:10** vs título da seção 00:23–00:32; conciliação falas **00:31–00:38** vs seção 00:40–00:43), e a duração declarada de 01:02:15 conflita com último diálogo 00:54:12 e MP4 original catalogado 00:54:44. O texto derivado indica **Acompanha Custos disparado primeiro para aproveitar processamento demorado em paralelo**, dependência verbal relatada para Kardex/saldo e **não sacramentação** do estoque durante operações da fábrica. `TRANSCRIPT_RECEIVED=PROVEN`, `CONTENTS=INFORMED_DERIVED`, `TIMECODES=STALE_EVIDENCE`, `VIDEO_DIRECT_VERIFICATION=TEST_NOT_RUN`. Antes de citar minuto definitivo, conferir reprodutor e prints; nenhuma regra runtime inferida.


### R03 — Primeiro artefato físico P7 recebido (21/10/2026)

PO forneceu **`Resumo Estoque.pdf`**, página única de `REGISTRO DE INVENTÁRIO`, Matriz, folha 000.074, posição `30/09/2026`. Totais impressos: `EM ESTOQUE=2.699.026,36`, `EM PROCESSO=277.941,20`, **`TOTAL GERAL=2.976.967,56`**, distinto de `3.776.994,69` (NotebookLM derivado; delta `800.027,13`). O PDF foi criado em 01/10/2026 19:37:32 UTC segundo metadados; não inferir data do corte. Subtotal processo diverge em R$0,01 da soma das linhas impressas; PA `190.511,24` corresponde a agregação anterior SB9, PI diverge R$0,01. **[Auditoria detalhada doc 46 §15](./46-t01-report-source-inventory-v1.md).** `REPORT_EXPORT_EVIDENCE=PROVIDED` somente para esse resumo, `REPORT_VARIANT=TO_VERIFY`, `FULL_PARITY=TEST_NOT_RUN`. Próximo: receber individualmente o arquivo `Estoque.pdf` para esclarecer o relatório de origem e a composição, evitando suposições.


### R03 - P7 Layout H e classificacao MP/PI/PA (21/10/2026)

Joici confirmou ao PO que a segunda saida P7 utiliza layout H e atende ao acompanhamento restrito a materia-prima (MP), produto intermediario (PI) e acabado (PA). `SB1010.B1_TIPO` e campo real verificado no Protheus para essas categorias; nao assumir que esse filtro isolado reproduza MATR460. PDFs de 30/09/2026: `Estoque.pdf` amplo 3.946.431,87 e `Resumo Estoque.pdf` restrito 2.976.967,56, com diferencas inclusive em MP. Destinatario Financeiro/Contabilidade e regra completa de parametros ainda pendentes de verificacao; paridade `TEST_NOT_RUN`. Detalhes: [doc 46 secao 22](./46-t01-report-source-inventory-v1.md). Sem alteracoes de runtime.


### R03 — Consulta operacional P7: opcao A aprovada, contrato de design (21/10/2026)

PO aprovou preparar uma consulta inicial de estoque historico read-only para P7, com `all_products` e `mp_pi_pa`, sem alegar reproducao integral da MATR460. **[Doc 49 — contrato e gates R03](./49-r03-p7-operational-stock-query-contract-target.md)**. HEAD do MFE `src/app/pluginRoutes.ts` inclui `home` e `financial_settlements`, nao uma rota P7. Caminho de pagina e BFF sao candidatos de design, nao rotas implementadas. `OPTION_A_APPROVED=YES`; `DOCUMENTATION_DESIGN=TARGET`; `TRANSVERSAL_RUNTIME_GATE=PENDING`; `P7_PARITY=TEST_NOT_RUN`; `SB9_SEPT_FILIAL01=EXECUTION_DRIFT`. Proximo: inventario do executor sobre rotas, contratos `api-delpi`, BFF, auth, dados e testes, depois gate transversal explicito antes de codigo/deploy. Nao apresentar soma SB9 como total P7 oficial.


### R03 — Regra de filial aprovada pelo PO (21/10/2026)

**Filial e apenas filtro nos visuais e consultas**: nao existe segregacao de usuarios, paginas ou dados por filial dentro do Portal Controladoria & Financas. Com `controllership-finance.access` efetiva, a consulta R03 oferece filial individual ou `all`; nao criar permission por filial ou reutilizar `BranchAccessGate` que exija tais permissions. O backend continua a validar permissao efetiva do Core e regras gerais da consulta. Decisao registrada no [doc 49, secao 8](./49-r03-p7-operational-stock-query-contract-target.md). `BRANCH_POLICY=DECIDED`; `TRANSVERSAL_RUNTIME_GATE=PENDING` (sem liberacao automatica de implementacao); `SB9_SEPT_FILIAL01=EXECUTION_DRIFT`.

### R03 — Consulta operacional P7 v1 implementada nas tres camadas (21/10/2026)

Implementacao executada apos gate transversal do briefing: `GET /financeiro/stock-inventory` (api-delpi, S2S `stock-inventory.read` + Bearer delegado), `GET /closing/stock-inventory` (BFF, `.access` efetiva via Core) e pagina `/apps/controllership-finance/closing/stock-inventory` (MFE). Contexto `financeiro_stock_inventory` com snapshot SB9/SB1 por competencia (`B9_DATA` = ultimo dia calendario), filtro de filial sem segregacao, visoes `all_products`/`mp_pi_pa`, totais por tipo e armazem sobre o universo completo do filtro, status `available|incomplete|source_missing|no_matching_items` — snapshot ausente nunca vira `0.00`. Flag `FINANCEIRO_STOCK_INVENTORY_ENABLED` default off (dataset fail-closed). Registro completo e evidencia SQL real no [doc 49, secao 9](./49-r03-p7-operational-stock-query-contract-target.md). `R03_IMPLEMENTATION=EXECUTED_V1`; `P7_PARITY=TEST_NOT_RUN`; `E2E_SMOKE=PASS` (21/10/2026, producao); `S2S_KEYCLOAK_PROVISIONING=DONE`; `SB9_SEPT_FILIAL01=EXECUTION_DRIFT`.

**RCA 403 producao (21/10/2026):** o 403 "Acesso restrito" era `S2S_SCOPE_DENIED` — a BFF solicitava `S2S_SCOPE=settlements.read` e o token nunca carregava `stock-inventory.read`, alem do scope nao provisionado no Keycloak. Corrigido: `CF_S2S_SCOPE` vazio, flags explicitadas, provisioner bounded criado e **aplicado em producao** (scope + default + audience OK), `FINANCEIRO_STOCK_INVENTORY_ENABLED=true`, BFF propaga `error.code` upstream e o MFE distingue RBAC ("Acesso restrito"), credencial S2S ("Integracao de dados pendente") e gate de dataset ("Consulta ainda nao habilitada"). **Smoke E2E real `PASS`**: `2026-09`/`02` → `available` 10.576.487,839 (bate com SQL); `/01` → `source_missing`; `all` → `incomplete`; RBAC negativo 403 sem codigo. Detalhes no [doc 49, secao 10](./49-r03-p7-operational-stock-query-contract-target.md). `S2S_KEYCLOAK_PROVISIONING=DONE`; `FEATURE_FLAG=ON`; `E2E_SMOKE=PASS`.

### PROC-0072 — Consulta automatica por filtros + loading centralizado (21/10/2026)

Melhoria transversal de UX nas duas paginas da Central de Fechamento (R01/R02 baixas e R03/P7 estoque):

- **Consulta automatica**: removido o botao Consultar/Aplicar. Os filtros vigentes sao derivados dos campos — toggles (pagar/receber, todos/MP-PI-PA), seletores (filial, ordenacao) e datas/competencia aplicam na hora; campos digitaveis (natureza, tipo de movimento, armazem) usam `useDebouncedValue` (400ms, `src/utils/`). Consulta inicial automatica quando o conjunto padrao e valido; filtros invalidos/incompletos nao disparam request.
- **Concorrencia**: efeito unico de fetch com `AbortController` + sequencia (`requestId`) — resposta atrasada nunca sobrescreve a mais recente; mudanca de filtro volta para a pagina 1 via ajuste de estado em render-time (fingerprint dos filtros), sem consulta duplicada; `Tentar novamente` em falha refaz a mesma consulta via nonce na queryKey.
- **Loading centralizado**: `CfLoadingCard` (`createDashboardLoadingActivityCard` do `@delpi/plugin-ui`, adaptador ja existente em `controllershipFinanceUi.ts`) passa a ser o indicador unico — `variant="compact"` dentro de secoes, e o `DataTableSection` ja o usa internamente para loading inicial/refresh. Regiao de resultados envolvida em `aria-busy`. Nenhuma biblioteca paralela de componentes criada.
- **Data civil**: `formatCivilDate` (`src/utils/formatters.ts`) formata `YYYY-MM-DD` como data de calendario local — corrige a data-base do P7 que exibia 30/08 e 29/09 em fuso negativo; usada tambem nas datas das baixas.
- Padrao documentado no [mapa de reuso — Feedback e estados](./30-plugin-ui-reuse-map.md). Ajuda contextual atualizada para refletir a consulta automatica. Sem mudanca de contrato, auth ou semantica de dados; paridade MATR460 permanece `TEST_NOT_RUN`.

### PROC-0072 — Padronizacao de cards e mensagens centralizadas (21/10/2026)

Continuacao da melhoria de UX na Central de Fechamento, agora de composicao visual e feedback:

- **Grid de cards centralizado**: `CfMetricStrip` (`createDashboardMetricStrip` do `@delpi/plugin-ui`, bound `cf` em `controllershipFinanceUi.ts`) substitui os `<ul class="cf-settlements-summary">` locais — gap consistente, quebra responsiva por largura, `tabular-nums`/`word-break` para valores financeiros longos (ex.: `12.896.290,89`), `role="group"` + `aria-label` por secao. Aplicado aos indicadores, resumo por tipo e resumo por armazem da R03 (label `Armazem 01 · Filial 02` preserva a associacao) e ao resumo por moeda das baixas. CSS local de summary removido; tokens legados `--delpi-*` do strip boundados aos tokens `--cf-*` do tema (claro/escuro).
- **Mensagens centralizadas**: novo adaptador fino `src/app/cfFeedbackUi.ts` — `CfFeedbackMessage` (intencao semantica `info|warning|error|success` mapeada as variantes reais do `CfStateBanner`) e `CfQueryErrorBanner` (catalogo unico de falhas de consulta: `scope_unavailable`, `S2S_*`, 401, 403, 503, generico — com `Tentar novamente`). Substitui os textos brutos soltos das duas paginas e cobre o gap das baixas (agora distingue S2S/503/401 como a R03); "Qualidade dos vinculos" e nota operacional P7 viram mensagens `info`, snapshot ausente continua estado informativo proprio — nunca saldo zero.
- Sem regressao: auto-query, debounce 400ms, AbortController/requestId, paginacao, loading centralizado e datas civis preservados; sem mudanca de SQL/DTO/contrato/infra. Padroes documentados no [mapa de reuso](./30-plugin-ui-reuse-map.md).

### PROC-0072 — Hero integrado + toolbar de tabela (doc 50, 21/10/2026)

Redesenho de composicao das duas paginas da Central de Fechamento conforme o TARGET do [doc 50](./50-closing-pages-hero-filters-table-ux-target.md):

- **`ClosingHero`** (`src/app/ClosingHero.tsx`) — adaptador fino de composicao sobre `CfPageHero` (`createDashboardPageHero` do kit, ja bound): eyebrow "Central de Fechamento", titulo com `CfTitleWithHelp`, subtitulo, "Atualizado as HH:mm" (timestamp real da consulta) + "Atualizar" (repete a consulta vigente, nao submete), `highlights` com KPIs reais e loading "…", nota `CfFeedbackMessage` e area de filtros delimitada com "Limpar filtros" a direita.
- R01/R02: KPIs Eventos/Movimentacoes por moeda (codigo real da origem)/Naturezas/Tipos de movimento migrados do card "Resumo do periodo" para o hero; nota de leitura dos totais no hero; "Qualidade dos vinculos" segue no stack de resultados. R03: KPIs Disponibilidade/Data-base/Itens/Filiais/Valor historico total no hero (tone warning para nao-disponivel); resumos por tipo e armazem permanecem secoes empilhadas com `CfMetricStrip`; nota P7 operacional permanente no hero.
- Toolbar: `fontSizePreferencesKey` ativado nas duas tabelas (controle nativo de fonte); "Colunas" ja ativo; Excel e view Cards `TO_INVENTORY` — nao implementados (sem backend/mapeamento homologado).
- Regressao do gap corrigida anteriormente mantida; teste de stack preservado. 91/91 vitest, 17/17 estruturais, lint/tsc/build verdes.


### Proposta UX hero/filtros/tabelas R01-R03 — DESIGN TARGET (21/10/2026)

[Documento 50 — especificacao detalhada para Devin](./50-closing-pages-hero-filters-table-ux-target.md): composicao visual de hero com KPIs e filtros nas duas paginas de fechamento; ordenacao e barra de ferramentas da tabela; design responsivo, mensagens, reuso de plugin-ui, contratos de dados e criterios de aceite. Referencias visuais sao mockups ilustrativos, sem autorizacao para inventar numeros, comparativos, layout H ou features nao existentes (Excel/Cards/MP/PI/PA isolados). `DESIGN=TARGET`; `RUNTIME_GATE=PENDING` ate execucao autorizada; nenhum backend ou runtime alterado neste registro.
