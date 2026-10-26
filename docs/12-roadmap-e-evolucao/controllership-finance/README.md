# Portal Controladoria & Finanças — Fonte de navegação e estado

> **DECISÃO DE PRODUTO SUPERSEDE PREMISSA DE ENTRADA — 26/10/2026 (PO, PROC-0072):** no workspace **Fechamento mensal**, o usuário seleciona um **mês de referência** para consultar a Visão geral, os relatórios calculados pelo owner canônico e a lista de documentos aplicável ao mês, **sem exigir abertura prévia de `monthly_competence`, template PUBLISHED ou anexos existentes**. A lista de **tipos/entregáveis exigidos** é um cadastro geral versionado, com inclusões/retiradas e início de vigência por competência; não deve ser recriada a cada mês. Arquivos/evidências anexados são próprios do mês, sob AuthZ. Fechamentos finalizados preservam sua lista e evidências históricas (sem mutação retroativa). Permanecem **exatamente três abas**: Visão geral; Documentos e interações; Relatórios e divergências. Esta é uma decisão de **TARGET**, **não descreve o runtime atual**. O fluxo existente de `POST /closing/competences` com template PUBLISHED continua sendo AS-IS técnico até reconciliação contratual; não publicar template, abrir competência, migrar dados ou executar deploy automaticamente. Ver [doc 112](./112-design-visual-fechamento-mensal-wireframes.md). **Gates:** inventário de owners/contratos/RQ-AC e implementação autorizada antes de alterar runtime. Qualquer trecho abaixo que pressuponha abertura/publicação como requisito para **consulta mensal** fica superado apenas nesse ponto; a necessidade de snapshot para operações formais P2/P5 segue em reconciliação.


> **Design em elaboração (26/10/2026):** [Documento 112 — Fechamento mensal, wireframes página por página](./112-design-visual-fechamento-mensal-wireframes.md). PO solicitou consolidar uma mesa operacional com divergências, documentos, pendências e revisão; **wireframe V0.1 é proposta, sem aprovação visual ou GO de runtime**. Cada componente/página será revisado no chat e versionado com evidências e SHAs.

> **Atualização de 26/10/2026 — CLARA funcional no ChatGPT (READ autenticado):** [Documento 111 — smoke MCP autenticado e retomada P1–P6](./111-clara-chatgpt-smoke-autenticado-retomada-central-2026-10-26.md). Nesta sessão foram descobertas **18 definições de tools** e executadas com `success=true` as ferramentas `get_catalog`, `get_my_context` e `search_closing_knowledge` (corpus publicado: 52 fontes/1.298 itens, com citações por locator). **`ACCEPT_WITH_RESIDUAL` somente para discovery e READ autenticado da CLARA**; publicação no workspace, leitura operacional de competência, ACT/consentimento V014 e reconciliação IAM plena permanecem pendentes. **Retomada do desenvolvimento da Central:** fazer inventário READ-ONLY P1–P6 / RQ-AC / owners / gates e propor próximo slice antes de novo GO; o êxito da CLARA não implica aceite global P1–P6.

> **Handoff de arquitetura em 24/10/2026:** [Doc 101 — continuidade pós-runtime P6-MIN + P2-READ](./101-ciclo3-handoff-arquitetura-pos-runtime-p6-min-p2-read.md). Execução relatada no [doc 100](./100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md), commit de runtime `f27dc307a48a5c9b37e6469e1c12d5f56ddbd896`. **Próxima ação obrigatória: GPT REVIEW independente do runtime no HEAD atual.** Testes reportados: BFF 131 incluindo PG real 10; MFE 100, estruturais 25, typecheck/build OK. `SMOKE_AUTHENTICATED=TEST_NOT_RUN`, `DEPLOY_PRODUCTION_AUTHORIZED=NO`, `NEXT_SLICE_GO=NO`. Não confundir relato do executor com aceite arquitetural definitivo.

> **Estado atualizado em 24/10/2026.** Primeira funcionalidade: **Central de Fechamento**, processo **PROC-0072**. **Existem** MFE, BFF e páginas read-only Home, Baixas financeiras, Estoque histórico e **Checklist da competência (P2-READ)** no HEAD, mais persistência governada `P6-MIN` (template versionado + publicação por API) — evidência no [doc 100](./100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md); **isso não é a Central P1–P6 completa nem homologada em produção**. Este README é o **painel de estado**; relatórios antigos A12/A14/A15/A16 são evidências datadas, não gates atuais.

## Estado executivo vigente — 24/10/2026

**Roteiro único para implementação E2E da Central:** [Documento 93 — Roadmap executivo E2E com checkpoints reais](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md). O documento 39 permanece plano de base anterior aos Ciclos 1–3; docs 40–43 mantêm dependências, testes, playbook e rollout, com precedência de sequenciamento/checkpoints atualizada pelo 93. **Não confundir CODE_PRESENT das duas consultas com documentos automatizados, aceitos ou pacotes publicados.**

**Estado de prova:** Ciclo 1 `PO_ACCEPTED_WITH_RESIDUAL` (doc 79); Ciclo 2 coleta **47/60**, auditoria **55/90**, **G6=0/15** (docs 47/86); C3 docs 90–92 consolidaram workflow e decisões com gaps físicos. `CP00=PASS_DOCUMENTAL`, `CP01_OPERATIONAL_TESTS=PASS/REPORT_EQUIVALENCE=FAIL/HUMAN_E2E=TEST_NOT_RUN`; **primeiro incremento de runtime executado**: `P6-MIN + P2-READ` sob GO `CF-C3-P6-MIN-P2-READ-RUNTIME-GO-001` — schema `controllership_finance` no `postgres-plugins`, migrations V001/V002 (53 itens DRAFT), API admin governada, abertura idempotente de competência com snapshot 53 `EXPECTED`, página de checklist no MFE — `ACCEPT_WITH_RESIDUAL`, [doc 100](./100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md); smoke autenticado `TEST_NOT_RUN`, deploy de produção **não realizado**. Runtime P1–P6 restante `TARGET` e precisa de gates transversais + GO por página. **Nova permission/página de Contabilidade/DRE: DECIDIDA PELO PO, IMPLEMENTAÇÃO ADIADA** (doc 91); manifesto atual continua com 2 permissions. `IMPLEMENTATION_AUTHORIZED=NO` para novos slices.

**CLARA — trilho obrigatório do roadmap:** a [CLARA, especialista MCP (doc 94)](./94-clara-especialista-mcp-controladoria-financas.md), integrada ao Chat no padrão TÉO/VISTA, evoluirá em checkpoints **M00–M06 do [Documento 93](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md)**, com conhecimento rastreável de PROC-0072 e regras de negócio e paridade do usuário na UI/BFF. **Decisão CLARA-D01=B aprovada pelo PO em 24/10/2026:** a CLARA **poderá validar, rejeitar e concluir** pelo chat com **aval explícito do usuário por operação**, AuthZ fresca no Core/BFF, auditoria e verificação de resultado. A [regra IA do doc 14](./14-seguranca-rbac-auditoria-e-ia.md) foi alinhada para execução delegada, não decisão autônoma. Contratos e GO runtime pendentes; **nenhuma tool ACT sensível implementada ou autorizada**.

**Próximo pacote para executor:** pendente de nova decisão do PO — revisão GPT do incremento `P6-MIN + P2-READ` (doc 100) e definição do próximo gate (candidatos: smoke/homologação autorizada, P2-Upload, P3). **Não prossiga para P2-Upload, P3, P4, P5 ou CLARA sem novo gate e autorização.**

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

## 2. Estado histórico dos gates (19/10) — interpretar com rebaseline do Documento 93

| Controle | Registro histórico de 19/10/2026 |
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

## Diretriz operacional vinculante — pesquisa de reuso entre contextos (Ciclo 2, 23/10/2026)

**Antes de avançar qualquer R01–R15 ou registrar nova regra no doc 85, o Devin deve executar a verificação transversal documentada no [doc 80 §0](./80-ciclo2-registro-vivo-investigacao-devin.md):** procurar no **código e contratos do HEAD** regras, endpoints, services, SQL, testes e consumidores já presentes em **Suprimentos, api-delpi e demais contextos Minha DELPI**, e confrontá-los com instruções oficiais, `.cursor`, ADRs e padrões de desenvolvimento. Isso é uma **etapa da investigação vigente**, não uma nova frente de catálogo. Registar o resultado e referências de evidência no doc 80/85 da rodada; não duplicar regras canônicas nem inferir ausência por search miss.

**Pendência já identificada para a próxima interação:** o PO informou que **o CPV já é calculado em Suprimentos e possui regra na API**. A implementação e o contrato específicos ainda **não foram verificados** neste recorte; revisar esse reuso antes de propor medida ou fórmula nova para R06. Separadamente, examinar as **11 linhas de custo de R06** não vinculadas individualmente; a existência do CPV não resolve sua paridade automaticamente. **Sem mudança de gates ou autorização de runtime decorrente desta atualização.**

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

<GESTORA-PROC> confirmou ao PO que a segunda saida P7 utiliza layout H e atende ao acompanhamento restrito a materia-prima (MP), produto intermediario (PI) e acabado (PA). `SB1010.B1_TIPO` e campo real verificado no Protheus para essas categorias; nao assumir que esse filtro isolado reproduza MATR460. PDFs de 30/09/2026: `Estoque.pdf` amplo 3.946.431,87 e `Resumo Estoque.pdf` restrito 2.976.967,56, com diferencas inclusive em MP. Destinatario Financeiro/Contabilidade e regra completa de parametros ainda pendentes de verificacao; paridade `TEST_NOT_RUN`. Detalhes: [doc 46 secao 22](./46-t01-report-source-inventory-v1.md). Sem alteracoes de runtime.


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

- **`ClosingHero`** (`src/app/ClosingHero.tsx`) — adaptador fino de composicao sobre `CfPageHero` (`createDashboardPageHero` do kit, ja bound): eyebrow "Central de Fechamento", titulo com `CfTitleWithHelp`, subtitulo, "Atualizado em DD/MM/AAAA, HH:mm" (timestamp real da consulta, sem botao), grid `cf-hero-kpis` de `CfMetricKpiCard` (icone+label+valor+hint+tone) com KPIs reais ("…" em loading), nota `CfFeedbackMessage`, painel de filtros `cf-hero-filters` e acoes a direita: "Limpar filtros" (ghost) + "Atualizar consulta" (primary, repeticao unica da consulta vigente — nao submete).
- R01/R02: KPIs Eventos/Movimentacoes por moeda (codigo real da origem)/Naturezas/Tipos de movimento migrados do card "Resumo do periodo" para o hero; nota de leitura dos totais no hero; "Qualidade dos vinculos" segue no stack de resultados. R03: KPIs Disponibilidade/Data-base/Itens/Filiais/Valor historico total no hero (tone warning para nao-disponivel); resumos por tipo e armazem permanecem secoes empilhadas com `CfMetricStrip`; nota P7 operacional permanente no hero.
- Toolbar: `fontSizePreferencesKey` ativado nas duas tabelas (controle nativo de fonte); "Colunas" ja ativo; Excel e view Cards `TO_INVENTORY` — nao implementados (sem backend/mapeamento homologado).
- Regressao do gap corrigida anteriormente mantida; teste de stack preservado. 91/91 vitest, 17/17 estruturais, lint/tsc/build verdes.


### Proposta UX hero/filtros/tabelas R01-R03 — DESIGN TARGET (21/10/2026)

[Documento 50 — especificacao detalhada para Devin](./50-closing-pages-hero-filters-table-ux-target.md): composicao visual de hero com KPIs e filtros nas duas paginas de fechamento; ordenacao e barra de ferramentas da tabela; design responsivo, mensagens, reuso de plugin-ui, contratos de dados e criterios de aceite. Referencias visuais sao mockups ilustrativos, sem autorizacao para inventar numeros, comparativos, layout H ou features nao existentes (Excel/Cards/MP/PI/PA isolados). `DESIGN=TARGET`; `RUNTIME_GATE=PENDING` ate execucao autorizada; nenhum backend ou runtime alterado neste registro.


### Auditoria de lacunas das tabelas R01/R02 e R03 — TARGET (21/10/2026)

[Documento 51 — auditoria e gates Table UX](./51-r01-r03-table-ux-gap-audit-and-implementation-gates.md): matriz T01-T19 das diferencas observadas nas capturas atuais versus mockups ilustrativos, capacidades reais de `DataTableSection`, restricoes de contrato/seguranca, blueprint de toolbar, verificacao visual e handoff ao Devin. `VISUAL_REWORK=TARGET`; `RUNTIME_GATE=PENDING`. Exportacao Excel, view Cards e links/acoes por linha dependem de gates especificos: nao sao bugs nem autorizacao implicita.


### Blueprint detalhado das tabelas de fechamento (design target, 21/10/2026)

[Doc 52 - R01/R02 e R03: tabelas, colunas, toolbar, regras de visualizacao e gates](./52-r01-r03-table-visual-blueprint-and-acceptance.md). Especificacao detalhada para Devin, com mockups somente como referencia visual, sem inventar dados, exportacao, Cards, links ou outros recursos sem contrato. `DESIGN=TARGET`; `RUNTIME_GATE=PENDING`.


## Roadmap executivo Table UX — ate 3 interacoes (21/10/2026)

[Doc 53 — Table UX final em tres interacoes](./53-table-ux-final-3-interactions-execution-roadmap.md) e o plano de execucao V7: 1/3 Baixas financeiras R01/R02; 2/3 Estoque historico P7 R03; 3/3 homologacao transversal e correcoes finais. Em cada interacao: implementar, testar, comparar no navegador, commit, push, deploy MFE via runbook SSH e smoke registrado. Estado inicial `TARGET / EXECUTION_PENDING`; nao inferir PASS de bundle HTTP 200 ou capturas antigas. Features dependentes de contrato/decisao permanecem em gate separado.


## Mapeamento consolidado Estoques e Custos (21/10/2026)

[Doc 55 — Matriz de conferencias e evidencias AS-IS](./55-proc0072-matriz-conferencias-estoques-custos-asis.md): consolida o recorte do video 19–33min, Kardex 01/99, R05 MATR320, inventarios, previa CPV, terceiros, MOD, saldos em processo, parametros, formulas candidatas e criterios que ainda precisam de comprovacao. Status `DOCUMENTED_PARTIAL`, reconciliacao `INCONCLUSIVE`, SQL parity `TEST_NOT_RUN`, sem GO runtime. Complementa docs 46 e 54 e nao autoriza paginas isoladas adicionais.


## Observacoes guiadas do PO - fluxo de fechamento de custos (21/10/2026)

[Doc 56 - Registro incremental do Acompanha Custos](./56-proc0072-observacoes-guiadas-fechamento-custos.md): primeiro trecho narrado pelo PO (aprox. 01:25-02:08): processamento demorado e paralelo a outras tarefas, ajuste operacional de data ao fim do mes, wizard TOTVS, metodo Diario, filial corrente e proximo passo. Campos do screenshot PROVEN; fala OWNER_REPORTED_VIA_PO; algoritmo e job TO_INVENTORY; nenhum GO de automacao.


## PROC-0072 - Matriz-mestra do video e roadmap de levantamento (22/10/2026)

[Doc 57 - Rastreabilidade integral V01-V23, reconciliacoes RC-01 a RC-09, riscos X01-X12 e tres ciclos de inventario](./57-proc0072-matriz-mestra-revalidacao-video-e-roadmap-inventarios.md). Consolidacao documental de todos os registros 01-18 do doc 56, em conjunto com docs 46 e 55, atraves das explicacoes guiadas do PO e prints. **Authority AS-IS = TEO/<GESTORA-PROC>; authority TARGET = GitHub.** O doc 55 permanece como recorte tecnico especifico 19-33 minutos; o doc 57 e a matriz geral vigente para controlar lacunas e evidencias. A validacao do MP4 original, as verificacoes de dados e a custodia de prints ainda estao pendentes; nao declarar paridade TOTVS/SQL nem audio/timecodes como PASS. Matriz = DOCUMENTED_WITH_RESIDUAL; dados = TO_INVENTORY / TEST_NOT_RUN; novas capacidades = DECISION_REQUIRED.


### Ciclo 1 - checklist de entregaveis por aba (22/10/2026)

[Doc 59 - Tres abas e crosswalk P2/P5/P6](./59-ciclo1-checklist-abas-e-entregaveis-sanitizado.md): resumo sanitizado da referencia operacional de envio; abas Eletronico (arquivos/relatorios digitais), Fisico (documentacao comprobatória) e Planilha1 (taxonomia auxiliar de consumo/despesas). Legenda verde `Enviar` significa exigencia de envio no escopo da coluna, **nao** prova de submissao/aceite. Somente matriz e filial da empresa de componentes no escopo vigente; antiga empresa industrial e contexto legado. O [doc 57 §8](./57-proc0072-matriz-mestra-revalidacao-video-e-roadmap-inventarios.md) registra as correcoes e o vinculo com os fluxos existentes. `CHECKLIST_PURPOSE=PO_CONFIRMED`; `CATALOG_MAPPING=TO_INVENTORY`; `RUNTIME=NOT_AUTHORIZED`. Nenhuma informacao fiscal, financeira, identificador individual ou documento original foi versionado.


### Ciclo 1 - rotinas fiscais e contabeis TOTVS

[Doc 60 - Inventario sanitizado de rotinas e privilegios](./60-ciclo1-rotinas-contabeis-fiscais-totvs.md): duas abas, 14 rotinas fiscais e 7 contabeis. Codigos candidatos MATR460, MATR989, MATR910, DLP204, FINR150/FINR130/FINR190, EDAPP, cadastros e configuracoes fiscais. Lista de privilegios da planilha NAO e grant efetivo nem autorizacao para writes. Paridade ERP e contratos de API `TO_INVENTORY/TEST_NOT_RUN`; nenhum dado transacional ou documento privado versionado.


### Ciclo 1 - CPV da matriz: Kardex fisico-financeiro (22/10/2026)

[Doc 61 - Inventario conceitual do arquivo de CPV](./61-ciclo1-cpv-kardex-matriz-inventario.md): uma aba de Kardex com blocos por produto, movimentos, TES/codigo fiscal, entradas/saidas, custo medio, saldos e resumo por tipo. O nome da amostra indica setembro e cabecalho de referencia/emissao e de outubro; cutoff `TO_INVENTORY`. Vínculo candidato MATR910/doc 60, contraponto video/doc 57, roteiro CPV-01..08 de dados, elegibilidade e paridade. **Nao publicar valores, registros fiscais, produtos, documentos ou planilha original; runtime nao autorizado.**


### Ciclo 1 - Resumo de entradas e saidas MATR320 (22/10/2026)

[Doc 62 - Inventario conceitual MATR320](./62-ciclo1-matr320-resumo-entradas-saidas.md): PDF de uma pagina com resumo financeiro de entradas/saidas por tipo de material, incluindo saldo inicial/final, compras, movimentos internos, producao, vendas, devolucoes e poder de terceiros; competencia de movimento distinta da data de emissao/referencia. Cruzamento conceitual com Kardex/MATR910 (doc 61), P7/MATR460 e material em processo, sem inferir igualdade de escopo ou CPV de DRE. Paridade e fontes fisicas pendentes; dados e PDF original nao versionados.


### Ciclo 1 - Registro de Inventario, estoque e em processo (22/10/2026)

[Doc 63 - Resumo do registro de inventario](./63-ciclo1-p7-resumo-estoque-em-processo.md): PDF privado de uma pagina, com posicao da matriz em 30/09/2026, secao EM ESTOQUE e secao EM PROCESSO por categoria de material, mais TOTAL GERAL. Relacionado conceitualmente ao P7 narrado no video, mas identificador MATR460 e variante Bloco H nao aparecem no PDF e seguem `TO_INVENTORY`. Confronto pendente com MATR320/doc 62 e Kardex/doc 61; valores/documento original nao versionados.


### Ciclo 1 - Material em processo (22/10/2026)

[Doc 64 - Inventario conceitual do saldo analitico em processo](./64-ciclo1-material-em-processo-inventario.md): uma aba XLSB, campos produto/local/OP/tipo RE-DE/quantidade/valor, muitos registros zerados, cabeçalhos repetidos e duas dimensoes de local observadas. Produtor MATR989 candidato, nao comprovado; semantica RE0/RE1/RE2/RE9, elegibilidade e confronto com secao EM PROCESSO do Registro de Inventario (doc 63) permanecem `TO_INVENTORY/TEST_NOT_RUN`. Fonte e valores privados nao versionados.


### Ciclo 1 - Faturamento x MOD (22/10/2026)

[Doc 65 - Inventario conceitual das duas filiais](./65-ciclo1-faturamento-mod-inventario.md): duas abas de desdobramento PA/componentes MOD; campos de faturamento, quantidade, horas, custo unitario e custo total. Formulas observadas na amostra `Horas ~= Qtd Fat. * Quantidade` e `Custo Total ~= Horas * Custo Unitario`, sem confirmacao de horas efetivas nem homologacao da rotina candidata `DLP204`. Paridade e fontes ERP pendentes; nenhum registro financeiro/produto privado versionado.


### Ciclo 1 - movimentos de inventario (22/10/2026)

[Doc 66 - Invent / ajustes de inventario](./66-ciclo1-invent-movimentos-inventario.md): planilha privada com 45 movimentos de documento `INVENT`, combinacoes tecnicas `TES 999 / RE0` (saida) e `TES 499 / DE0` (entrada), e duas linhas finais de agregacao sem a mesma estrutura. Analise do efeito liquido, produtor, cobertura de armazens 01/99 e reconciliacao com Kardex, MATR320 e P7 seguem `TO_INVENTORY/TEST_NOT_RUN`. Somente regras e metadados conceituais foram versionados.


### Ciclo 1 - notas fiscais a desconsiderar (22/10/2026)

[Doc 67 - Inventario conceitual SD2](./67-ciclo1-nf-a-desconsiderar-sd2.md): uma aba de itens de nota fiscal de saida, exportacao SD2, 184 colunas e 11 itens na amostra. Identificada uniformidade de tipo de saida e codigo fiscal sem provar que essa combinacao seja criterio oficial de exclusao. Motivo, apuracao afetada, joins, filtros e paridade continuam pendentes; nenhum documento fiscal individual ou valor foi versionado.


### Ciclo 1 - Resumo Estoque, comparacao de variantes (22/10/2026)

[Doc 68 - Resumo reduzido e divergencia de abrangencia](./68-ciclo1-resumo-estoque-variante-reduzida.md): PDF privado de Registro de Inventario com secao EM ESTOQUE (MP, PA, PI) e EM PROCESSO (MP, PI), mesma data/contexto do PDF anterior doc 63. Os valores de PA e PI coincidem entre os arquivos, mas os de **MP em estoque e em processo divergem**: nao se trata comprovadamente apenas de ocultar outras categorias. Hipotese de variante de entrega contábil/Bloco H depende de parametros e rotina de origem; `TO_INVENTORY/TEST_NOT_RUN`. Sem valores ou PDF original no repositorio.


### Ciclo 1 - posicao de contas a pagar (2026-10-22)

[Doc 69 - Inventario estrutural da posicao financeira](./69-ciclo1-contas-a-pagar-posicao-titulos.md): 1 aba com campos de situacao de titulos, datas, vencimentos e naturezas. FINR150 candidato de origem; FINR190 representa baixas e nao equivale a saldos abertos. Paridade pendente. Sem dados de origem versionados.


### Ciclo 1 - contas a receber em aberto (22/10/2026)

[Doc 70 - Posicao de titulos a receber](./70-ciclo1-contas-a-receber-posicao-titulos.md): estrutura do snapshot financeiro, vencimentos, natureza e tipos de titulo, com 17 colunas, 560 registros na amostra e cabecalhos repetidos. FINR130 e candidato funcional; fontes, parametros e paridade com relatorios de recebimento/FINR190 permanecem pendentes. Sem dados transacionais originais no repositorio.


### Ciclo 1 - Pagamentos por natureza (22/10/2026)

[Doc 72 - Pagos por natureza](./72-ciclo1-pagos-por-natureza.md): inventario conceitual do relatorio privado `nat.prt`, agrupado por natureza financeira, com subtotais por classificacao e eventos de baixa de tipos distintos. Comparacao com `DLP06R01` por data, log de inconsistencias, rotina de menu e paridade com R01/R02 ainda nao homologados. Documento de origem e valores nao versionados.


### Ciclo 1 - relação tabular de baixas (23/10/2026)

[Doc 73 - Pagamentos setembro/2026: inventário de baixas](./73-ciclo1-pagos-0926-relacao-baixas.md): estrutura de uma aba XLSB com eventos de baixas, motivos DEB/CMP/FAT/NOR/DAC, datas, natureza, componentes financeiros e diferenças entre valor original e total baixado. Confronto com os PDFs por data (`DLP06R01`) e natureza (`nat.prt`), rotina FINR190 e contratos R01/R02 ainda `TO_INVENTORY/TEST_NOT_RUN`. Dados operacionais originais não versionados.


### Ciclo 1 - recebimentos por data (23/10/2026)

[Doc 74 - Relatorio de recebimentos por data](./74-ciclo1-recebidos-por-data.md): PDF privado do layout `DLP06R01`, com baixas agrupadas por data, compensacoes, subtotal e total geral. Nao equiparar baixa a entrada bancaria, nem posicao em aberto a fluxo liquidado. Correspondencia FINR190, verificacao do log de inconsistencias e paridade R01/R02 seguem pendentes; dados de origem nao versionados.


### Ciclo 1 - relacao tabular de recebimentos (23/10/2026)

[Doc 75 - Recebidos XLSB: inventario de eventos de baixa](./75-ciclo1-recebidos-relacao-baixas.md): inventario sanitizado de uma aba com 22 campos, codigos de motivo, diferencas entre valor original e total baixado, comparacao conceitual com PDF (doc 74), contas a receber (doc 70) e TARGET R01/R02 (doc 48). Produtor FINR190, regra de compensacao, identificador de evento, log de inconsistencias e paridade SQL/relatorio permanecem `TO_INVENTORY/TEST_NOT_RUN`. Fonte e valores privados nao versionados. Documento 71 permanece pendente de verificacao.


### Ciclo 1 — Revisao consolidada (23/10/2026)

[Doc 71 — Pagamentos por data](./71-ciclo1-pagos-por-data.md): inventario conceitual do PDF DLP06R01, distinguindo fluxo de baixas, compensacoes, posicao aberta e movimentacao bancaria. Fonte privada nao versionada; FINR190 candidato e paridade TEST_NOT_RUN.

[Doc 76 — Revisao documental do Ciclo 1](./76-ciclo1-fechamento-documental.md): cobertura de 19 planilhas/PDFs e video, lacunas dos inventarios historicos CC matriz/Analise, parametros divergentes do inventario e paridade financeira pendente. ACCEPT_WITH_RESIDUAL para base documental, encerramento formal PENDING, Ciclo 2 NO_GO. Corrige a nota anterior de que doc 71 ainda nao havia sido publicado; paths de 53/58 historicos ainda TO_INVENTORY.


### Ciclo 1 — Reconciliação de identificadores históricos (23/10/2026)

[Doc 77 — CC matriz e Análise: reconciliação de aliases do handoff](./77-ciclo1-reconciliacao-cc-matriz-analise.md): os números históricos 53 (CC matriz) e 58 (Análise) não são caminhos canônicos comprovados. O doc 53 vigente é o roadmap de Table UX. O doc 77 registra separadamente finalidade, estrutura observada, owner e pendências das duas fontes, sem renomear ou sobrescrever documentos existentes. Paridade e regras TOTVS seguem TO_INVENTORY/TEST_NOT_RUN; Ciclo 1 PENDING, Ciclo 2 NO_GO.


### Ciclo 1 — Cruzamento narração e relatórios (23/10/2026)

[Doc 78 — Crosswalk V01–V23 entre relato guiado e artefatos](./78-ciclo1-crosswalk-narracao-artefatos.md): associa docs 56/57 aos inventários 59–77, explicita divergências, limitações e nove verificações propostas para o Ciclo 2 com owners candidatos. Narrativa do PO integralmente registrada, áudio/timecodes independentes INCONCLUSIVE; paridade TOTVS TEST_NOT_RUN. Revisão ACCEPT_WITH_RESIDUAL, fechamento formal do Ciclo 1 PENDING e Ciclo 2 NO_GO. Sem alteração de contratos ou runtime.


### Ciclo 1 — aceite formal do PO (23/10/2026)

[Doc 79 — Aceite formal do Ciclo 1](./79-ciclo1-aceite-formal-po.md): após revisão e cruzamento narrativo-documental do doc 78, o PO declarou expressamente «eu aceito». `CICLO_1_DOCUMENTAL=PO_ACCEPTED_WITH_RESIDUAL`; o inventário conceitual fica formalmente aceito, com paridade TOTVS/SQL `TEST_NOT_RUN`, áudio/timecodes independentes `INCONCLUSIVE` e demais gaps rastreados. **Este aceite não autoriza o Ciclo 2:** investigação técnica aguarda GO específico; implementação e contratos novos não autorizados por esta decisão.


### Ciclo 2 — Registro vivo para investigação Devin (23/10/2026)

[Doc 80 — Registro vivo, fichas e roadmap de levantamento técnico](./80-ciclo2-registro-vivo-investigacao-devin.md): ponto de entrada preenchível por lotes D0–D5, matriz dos nove workstreams, campos obrigatórios de evidência, consultas read-only, owners, paridade e stop conditions. O [doc 47](./47-t01-report-column-audit-tracker-v1.md) permanece a authority de R01–R15, G1–G6 e percentuais; o doc 80 é registro de execução, não segundo tracker de gates. **CYCLE_2_GO=NO**, DAVI/SQL/system ainda não autorizados por este documento, paridade `TEST_NOT_RUN`, runtime sem autorização adicional. Após decisão expressa do PO sobre escopo/capabilities, Devin poderá preencher apenas o lote autorizado, com commits e revisão GPT.


### Ciclo 2 — Crosswalk integral de evidências (23/10/2026)

[Doc 83 - Crosswalk R01-R15](./83-ciclo2-crosswalk-evidencias-r01-r15.md): processamento da pasta de evidências do PO (20 arquivos) e do video de 54:44. Identifica DLP06R01.prt como layout compartilhado das baixas (pagar: produtor FINR190 provado pelo fonte; receber: custom `DLP06R01` sem fonte no acervo), vincula rotinas oficiais a R01-R15 (MATR460/P7, MATR320, MATR910, MATR989, DLP204, EDAPP, FINR190), registra execucao observada do fechamento de custo e mapeia residuais por owner.

[Doc 84 - Paridade monetária R01-R15](./84-ciclo2-paridade-monetaria-relatorios-oficiais.md): reconciliação linha-a-linha dos relatórios de baixas × SE5/SE1/SE2 (SELECT-only, set/2026). R01: 948/948 chaves, TB=`E5_VALOR` e VO=`E2_VALOR`(+regras aglutinado) exatos, resumos/componentes/filorig exatos → G5 PASS. R02: 649 SE5×SE1 + 8 `PA`/`FINA750` sem título = 657, TB=`E5_VALOR`, VO=`E1_VALOR` 649 + provisão 'P' espelhada 8/8 — Δ R$0,00 (errata doc 80 §30) → G5 PASS (G4 PENDING — fonte ausente). R03/R05: paridade parcial documentada. Doc 47 (§11.2): coleta 39/60 = 65,0%, auditoria 41/90 = 45,6%.

[Doc 85 - Catálogo de regras de negócio R01-R15](./85-ciclo2-catalogo-regras-negocio-r01-r15.md): consolidação versionada de toda regra necessária para reproduzir os resultados oficiais — WHERE fiel do FINR190, chave de estorno de 12 campos, regras de VO/TB (título/INV/aglutinado/provisão 'P'), resumos, XLSB×PDF×log, parâmetros observados e classificação PROVEN/AS-IS/TO_INVENTORY/TARGET/PENDING/STALE_EVIDENCE por regra (BR-Rxx-NNN). Inclui matriz de handoff (regra → fonte canônica → campos → transformação → contrato candidato → owner → testes → evidência) e matriz de testes derivada. Divisão de camadas: regras físicas na api-delpi, BFF agrega, MFE renderiza — sem implementação nesta rodada.


### Ciclo 2 — Consolidação R03/R05 e sanitização retroativa (23/10/2026)

[Doc 80 §33](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-STOCK-RULES-CONSOLIDATION-002): reconciliação do MATR320 expandida a **10 tipos × 13 colunas — 120/120 colunas de fluxo exatas** no estado de emissão; residual MovInt R$0,48 eliminado (artefato de sobre-reversão `TTAT_COLD` — corte correto por timestamp de emissão); divergência MP +8.631,731 **decomposta ao centavo por produto** (verificação rodada 16: 6 produtos revalorização CM + micro-ajustes líquido 0,000; Δ 0,000 — doc 80 §34). Binding de totalização P7 **provado**: `EM ESTOQUE = saldo ex-MV_LOCPROC(99) no as_of da emissão` (3.884.464,444 − 293.273,084 = 3.591.191,36; Δ 0,004) e `EM PROCESSO = MATR989`. **R05 promovido a G4+G5 PASS** (doc 47 §5/§11) — G6 PENDING (aceite funcional); R03 G4/G5 mantidos PENDING (parametrização por emissão e produtor `matr460.prx` pendentes — E2). Regras e testes preservados no [doc 85](./85-ciclo2-catalogo-regras-negocio-r01-r15.md) (BR-R03-004/005/006, BR-R05-007/011/012, T-R03-03/04, T-R05-08/09). Coleta 40/60 = 66,7%, auditoria 43/90 = 47,8%.

[Doc 80 §32](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-HISTORICAL-SANITIZATION-001, commit `edc19a6dda`): auditoria retroativa de confidencialidade — identificadores operacionais substituídos por aliases estáveis em 25 documentos; histórico Git preservado por decisão do PO (OPÇÃO A), residual de exposição em commits antigos classificado `DECISION_REQUIRED` para owner de segurança.

### Ciclo 2 — Decomposição da emissão resumida P7 (23/10/2026)

[Doc 80 §35](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-P7-PARAMETERS-PARITY-001): catálogo integral do grupo SX1 **`MTR460`** (25 perguntas — existe `Saldo em Poder 3º?` Sim/Não/De Terceiros/Em Terceiros; **não** existe parâmetro de tipo de produto). A emissão resumida (`Resumo Estoque.pdf`, folha 74) é **distinta** do completo (folha 101), com **mesma data-base 30/09 e mesmo estado de custo** (PA/PI bit a bit) — fatos: escopo MP/PA/PI + divergência exclusiva em MP. Melhor modelo `QTNP@emissão>0`: estoque 587.621,85 vs 587.698,28 implícito (**Δ 76,43**, 99,987 %) e processo 79.194,35 vs 77.251,73 (**Δ 1.942,62**) — sem paridade centavo. Hipóteses descartadas com evidência: filtro de armazém, `as_of` temporal, faixa/prefixo, sem-movimento, poder3 por quantidade/SB6, emissão intermediária. **R03 G4/G5 mantidos PENDING** (`NO_GATE_CHANGE`); regras `BR-R03-007/008` e testes `T-R03-05/06` no [doc 85](./85-ciclo2-catalogo-regras-negocio-r01-r15.md).

### Ciclo 2 — Correção de classificação R03 e handoff E2 (23/10/2026)

[Doc 80 §36](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-P7-E2-HANDOFF-001, DOCUMENTATION_ONLY): errata de classificação — `BR-R03-007` separada em **fatos `PROVEN`** (resumo só MP/PA/PI; divergência exclusiva em MP; parâmetro `MTR460` pergunta 02 existe) × **`PENDING`** (opção selecionada, causalidade, população exata, semântica do MATR460). O modelo `QTNP@emissão` permanece **hipótese empiricamente sustentada — não regra oficial**. Doc 82 E2 reescrito como solicitação conclusiva de **três evidências** ao owner TI/ERP: E2.1 parâmetros efetivos da emissão resumida; E2.2 relatório integral da folha 74 (custódia fora do GitHub); E2.3 produtor implantado/RPO — com critérios `SOURCE_AVAILABLE`/`CODE_DEPLOYED`/`EXECUTION_OBSERVED`/`FUNCTIONAL_ACCEPTANCE`. Gates inalterados (R03 G4/G5 PENDING; R05 G4/G5 PASS; E6=C; 40/60 · 43/90).

[Doc 80 §37](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-KARDEX-CPV-INVENT-PARITY-001): **reconstrução física completa do kardex MATR910** (filial 02, 09/2026). Fonte `matr910_dlp.prx` localizada no acervo (`SOURCE_AVAILABLE`; `CODE_DEPLOYED` → E7). Modelo `PROVEN`: UNION **SD1 (`D1_DTDIGIT`) + SD2 (`D2_EMISSAO`) + SD3 (`D3_EMISSAO`)** por produto, `F4_ESTOQUE='S'`, `D3_ESTORNO<>'S'`, `D*_ORIGLAN<>'LF'`, loc 01 — paridade linha-a-linha **9.357/9.357** (R06) e **45/45** INVENT (R07, loc 01+99). Ordem data+`D3_NUMSEQ` (1.971/1.971); REF decodificado (F-/P-/OP/CC); custos `as_of` emissão (**100%** — 7.376 `CUR` + 1.981 `TTAT_OLD`; errata r20 doc 80 §38: as "11 linhas" eram devoluções `TIPONF='D'` com sinal − provadas no fonte `zMTR910Dev`/`MV_LISTDEV`); saldo inicial `B9`@0831 e cadeia contínua **1.544/1.544**; saldo final vs SB9 regravada = drift temporal (`STALE_EVIDENCE`, Δqtd=0). Saídas agregadas **≠ CPV** (semântica composta, `DECISION_REQUIRED` para a medida). **Gates promovidos: R06 G4+G5 PASS, R07 G4+G5 PASS**; G6 PENDING; R01–R05 inalterados. Regras `BR-R06-001..010`/`BR-R07-001..003` e testes `T-R06-01..10`/`T-R07-01..04` no [doc 85](./85-ciclo2-catalogo-regras-negocio-r01-r15.md); matriz no [doc 84 §5.1](./84-ciclo2-paridade-monetaria-relatorios-oficiais.md). **Coleta 42/60 = 70,0% · auditoria 47/90 = 52,2%.**

[Doc 80 §38](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-KARDEX-R06-G5-REWORK-001): esclarecimento das "11 linhas de custo" — não eram divergência, mas `NO_KEY` do roteamento estrito da reconciliação inicial. Todas são **devoluções `TIPONF='D'`**: 4 SD2 (devolução de compra → coluna entradas ×−1) e 7 SD1 (devolução de venda → coluna saídas ×−1), custo `CUR` exato, mecanismo `zMTR910Dev`/`MV_LISTDEV` provado no fonte `matr910_dlp.prx`. **Paridade de custo efetiva = 9.357/9.357 (100%)**. R06 G5 PASS mantido (evidência reforçada); R07 inalterado; métricas inalteradas.

[Doc 80 §39](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-CPV-EXISTING-RULE-VERIFY-001, rodada 21 — READ/VERIFY only): **o CPV já existe implementado e canônico** — `GET /supplies/cpv` na api-delpi (`get_supplies_cpv`): `CpvQueryRepository` → `SUM(SD2.D2_CUSTO1)` com `D2_CF ∈ (5101,5124,6101,6124)`, `D2_EMISSAO` e filial opcional; `GetCPVUseCase` compõe ROL (SD2 vendas elegíveis − devoluções SD1) → `cpv_percentage`. Consumidores: `dashboard-supplies/CpvPage.tsx`, supplies-api KPI-CPV (overview + strategic indicators `supplies-cpv`), chat/DAVI `SUPPLIES_CPV`. Crosswalk R06: CPV = subconjunto das saídas SD2 do kardex (CFOPs de venda) — as saídas agregadas do MATR910 seguem ≠ CPV (incluem SD3 e CFOPs fora do conjunto). **BR-R06-010 → `PROVEN` (implementação/semântica verificadas) + `REUSE_PARTIAL`**: lacuna material = `D2_CUSTO1` corrente (não `as_of` — mutável por MATA330), CFOPs fixos na rota, sem recorte por produto/tipo; custo `as_of`/snapshot para fechamento = `DECISION_REQUIRED` do owner. Gates/métricas inalterados (42/60 · 47/90); zero código/contrato alterado.

[Doc 80 §40](./80-ciclo2-registro-vivo-investigacao-devin.md) — **Decisão PO: CPV mensal vivo (23/10/2026).** Correções retroativas são registradas na competência de origem e, após recálculo Protheus autorizado, a nova consulta desse mês mostra o valor corrente atualizado. A regra canônica `GET /supplies/cpv` usa `D2_EMISSAO` e `D2_CUSTO1` corrente; não exigir snapshot para leitura viva. Evidências previamente homologadas podem precisar de rastreabilidade separada, sem alegar implementação. E6=C é específico de MOD. **Sem mudança de gates ou runtime.** Próximo: docs 47/80 e gate de reuso §0.

[Doc 80 §41](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-R08-MATR989-MATERIAL-IN-PROCESS-PARITY-001, rodada 22): **reconstrução física completa do MATR989** (`Material em processo.xlsb`, aba `01-01 - Saldo em Processo (Ana`, Dt.Ref 01/10/2026 16:15; `matr989.prx` ausente — `SOURCE_MISSING`, E8). Dois blocos `PROVEN`: **(1)** 1.501 linhas com OP = 1.501 linhas `SD3010` `D3_CF IN (RE0,RE1,RE2,RE9)` — grão linha de movimento, `D3_QUANT`/`D3_CUSTO1`, corte `D3_EMISSAO`≤30/09, OP **aberta na emissão** (sem `PR0` e sem `C2_DATRF`; 650/650 pares exatos; 33 OPs que produziram em 01/10 e 3 encerradas-sem-produção excluídas); **(2)** 573 produtos sem OP = `SB9010`@20260930 loc99 (569 exatos + 4 Δ temporais de revalorização). **Total R$355.240,51 = EM PROCESSO do P7 exato** — EM PROCESSO = SB9-loc99 (293.273,09) + material alocado a OP aberta (61.967,42), não o armazém 99 sozinho; `RE1` loc01 (254,44) = fatia PI prevista (§33.D). Reuso: `stock_value_historical_sql` canônico p/ SB9+SD3 `as_of`; `em_processo_proxy_value` (SB2 loc 50/98/99) = parcial; serviço de saldo RE−DE por OP inexistente (`TARGET`, BR-R08-009). **Gates promovidos: R08 G4+G5 PASS**; G6 PENDING; R03 não promovido por associação (produtor/params E2 pendentes). Regras `BR-R08-001..009` e testes `T-R08-01..06` no [doc 85](./85-ciclo2-catalogo-regras-negocio-r01-r15.md); matriz no [doc 84 §5.2](./84-ciclo2-paridade-monetaria-relatorios-oficiais.md). Coleta 42/60 = 70,0% · auditoria 47/90 = 52,2% — zero runtime.

[Doc 80 §42](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-R08-MATR989-PARITY-REWORK-001, rodada 23 — errata de rigor sobre o §41): **(a)** o centavo de diferença na decomposição publicada era artefato de arredondamento — em precisão original (3 dec) os componentes somam **355.240,512** → exibição 355.240,51; **(b)** as 4 divergências SB9 estão decompostas por produto (aliases `<PRODUTO-WIP-A..D>`; ΣΔ +449,294 = SB9 corrente 293.722,382 − impresso 293.273,088) e classificadas `TEMPORAL` com evidência física: as **753 linhas** SB9 f01@0930 loc99 foram regravadas em **21/10 19:13** (`I_N_S_D_T_`) — 20 dias após a emissão, logo o bloco sem-OP é a posição do armazém 99 **no `as_of` da emissão**; TTAT de SB9/SB2 vazio para os RECNOs (sem auditoria por campo — classe apoiada no timestamp universal + drift de CM); **(c)** produtor reclassificado `PRODUCER_INFERRED_BY_ARTIFACT` (relatório emitido = `EXECUTION_OBSERVED`, não `CODE_DEPLOYED`); seleção por OP aberta provada em granularidade de dia — intradia pendente (E8); neteo `DE*` não generalizado. **(d)** códigos reais dos 4 produtos removidos dos docs; exposição anterior em `f5c50f7c04` registrada para o owner de segurança (histórico não reescrito — decisão PO §32). **Gates sustentados: R08 G4+G5 PASS, G6 PENDING**; métricas `43/60 = 71,7%` coleta · `49/90 = 54,4%` auditoria · `0/15`. Próxima ação: E8 (fonte/RPO/params MATR989 — TI/ERP) e E2 (P7) seguem com owners.

[Doc 80 §43](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-R09-FATURAMENTO-MOD-DLP204-PARITY-001, rodada 24): **modelo físico do DLP204 reconstruído com fonte** — `Fat x MOD.xlsb` (abas `1-Fl01`/`2-Fl02`, 4.476 linhas, set/2026). `DLP204.prw` **no acervo** (`SOURCE_AVAILABLE`; `EXECUTION_OBSERVED`; `CODE_DEPLOYED` RPO → E9). Provas: PA-âncora = `SB1`∩`SD2` do período com TES `F4_DUPLIC='S'` (regra canônica de vendas); `Qtd Fat.` = faturamento do âncora propagado aos descendentes (**4.476/4.476**); `Seq Comp` = nível SG1 (02/04/06); MOD = recurso do **roteiro congelado da OP** (`SHY010`, chave `C2_NUM+C2_ITEM+C2_SEQUEN`; fallback `SG2`) via `SH1010.H1_CCUSTO` → `MOD<cc>`; `Quantidade` = `HY_TEMPAD` (**4.449/4.476 = 99,4%**); fórmulas `Horas=QtdFat×Quantidade`, `CustoTotal=Horas×rate` (identidade integral); `Custo Unitario` = `SBZ010.BZ_CUSTD` **as_of emissão** via TTAT (**4.469/4.469** com SBZ; 7 MODs sem cadastro ≠ zero). Motor `EXEC STP_DELPI_FORMA_PRECO_<emp>` **ausente dos bancos** (`SOURCE_MISSING`, legado 2019 → E9: SP/RPO, parâmetros efetivos, divisor `÷2` desdobramento, 27 tempos, 7 MODs sem SBZ). Reuso: `F4_DUPLIC='S'` `REUSE_CONFIRMED`; `vw_Apontamentos_Eficiencia` `REUSE_PARTIAL` (horas reais + rate corrente ≠ tempo padrão × faturado × rate as_of). **Gates: R09 G4 PASS · G5 `INCONCLUSIVE` · G6 PENDING**; métricas `44/60 = 73,3%` coleta · `50/90 = 55,6%` auditoria · `0/15`. Regras `BR-R09-001..013` + `T-R09-01..07` no [doc 85 §9](./85-ciclo2-catalogo-regras-negocio-r01-r15.md); matriz [doc 84 §5.3](./84-ciclo2-paridade-monetaria-relatorios-oficiais.md). Zero runtime.

[Doc 80 §44](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-R10-CENTRO-CUSTO-SD1-PARITY-001, rodada 25): **seleção EDAPP do `CC matriz.xlsb` reconstruída integralmente e corroborada pelo owner** — 353 linhas = itens SD1 f01 `D1_DTDIGIT`∈set/2026 (eixo digitação provado: 80 linhas com emissão fora de setembro). Decomposição exata do universo (686): −303 linhas de 13 TES excluídos (`001,003,016,020,030,040,080,083,085,120,159,204,318` — COMPRAS-MP/CONTA-ORDEM/ENERGIA/COMUNIC/TRANSP/IND-VASILHAME/DEVOL-VENDAS/REMESSA/TRANSF/IMPORT), −24 `D1_TP='MP'` residuais, −6 benefícios saúde/odonto sem CC (`<PRODUTO-BENEFICIO-*>`) = **353/353 itens, Σ `D1_TOTAL` = R$ 169.704,12 exato**, 139 documentos, 46 CCs. Cada passo casa com o procedimento relatado no vídeo (doc 56 Registro 17: digitação no mês → excluir tipos de entrada → excluir MP → coparticipação benefícios fora → classificar manualmente). Coluna sem título `Direto`/`Indireto`/`Adm` = **classificação manual pós-exportação** por CC (não é campo SD1/CTT; subtotais Adm 99.297,81 · Ind 38.554,82 · Dir 31.851,49). Reuso: `vw_fin_despesas_centro_custo`/rotas `despesas-centro-custo` = **`REUSE_PARTIAL`** (eixo `D1_EMISSAO` + CC-obrigatório + sem exclusões: 448 linhas, 269/353 cobertura — não reproduz a seleção oficial). **Gates: R10 G1–G5 PASS · G6 PENDING**; métricas `44/60 = 73,3%` coleta · `51/90 = 56,7%` auditoria · `0/15`. Residuais documentais → **E10** (Controladoria): lista exata de tipos de entrada (narrada 12 vs observada 13 — `016`/`159` `F4_DUPLIC='N'`), filtro EDAPP preservado, regra benefícios colaborador×empresa, owner da taxonomia Direto/Ind/Adm. Regras `BR-R10-001..007` + `T-R10-00..04` no [doc 85 §10](./85-ciclo2-catalogo-regras-negocio-r01-r15.md); matriz [doc 84 §5.4](./84-ciclo2-paridade-monetaria-relatorios-oficiais.md). Zero runtime.

[Doc 80 §45](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-R11-NF-DESCONSIDERAR-SD2-PARITY-001, rodada 26): **seleção EDAPP do `NF a desconsiderar.xlsb` reconstruída por identidade de conjunto** — 11 linhas = **exatamente** os itens `SD2010` f01 `D2_EMISSAO`∈set/2026 com `D2_GRUPO='9035'`∩`D2_TES='594'` (equivalência bidirecional na competência; não é regra universal — all-time 9035 aparece com outros TES). Binding 11/11 por chave `(D2_DOC,D2_ITEM,D2_COD,D2_TOTAL)`; Σ `D2_TOTAL` = **R$ 97.462,71 exato**. "CPV zero" explicado estruturalmente: `D2_CUSTO1=0` **desde a criação** (TTAT `SD2010_TTAT_LOG` — insert `MATA460A` na emissão, `COLD`=`CNEW`=0.000, sem alterações) porque TES 594 tem `SF4.F4_ESTOQUE='N'`; semântica = **faturamento de industrialização para terceiros** (8/11 NFs casam item TES 510 custo>0/CFOP 5124 + item TES 594 custo 0/CFOP 5101). `GET /supplies/cpv` = `REUSE_PARTIAL` (as linhas CFOP 5101 contribuem R$0 ao numerador — lista de conferência manual, não regra da API; fórmula CPV intocada). Errata: `Tipo Saida` do export = `D2_TES` (não `D2_TIPO`='N'). **Gates: R11 G1–G5 PASS · G6 PENDING**; métricas `44/60 = 73,3%` coleta · `52/90 = 57,8%` auditoria · `0/15`. Residual → **E11** (Controladoria): qual apuração recebe o desconsiderar (CPV×ROL×DRE), regra×exceção por documento, eixo do filtro EDAPP. Regras `BR-R11-001..006` + `T-R11-01..04` no [doc 85 §10](./85-ciclo2-catalogo-regras-negocio-r01-r15.md); matriz [doc 84 §5.5](./84-ciclo2-paridade-monetaria-relatorios-oficiais.md). Zero runtime.

[Doc 80 §46](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-R12-COST-CLOSING-PROCESS-VERIFY-001, rodada 27): **cadeia de rotinas do fechamento de custos bound fisicamente** — vídeo MP4 reinspecionado diretamente (frames nos timestamps). **Custo de Reposição = `MATA320`**: grupo SX1 `MTA320` reproduz 1:1 os 16 parâmetros da tela; `SB1010_TTAT_LOG` prova a escrita em `SB1.B1_CUSTD` — `MATA320`/JOICI: 13.201 writes 30/09 14:36–14:56 + 1.532 em 15:09–15:14 (duas execuções MC-MP e PA/PI) + 15.972 em 01/10. **Refaz Saldos = `MATA300`**: grupo SX1 `MTA300` (8 perguntas) 1:1 — `Zera saldo/CM de produtos MOD?`=Recalcular; log de threads `c300P* - Ok` observado; efeito em SB2 `PENDING_EVIDENCE` (campos não auditados em TTAT). **Acompanha Custos** = wizard 4 etapas sobre motor MATA330 custom: lista `Fechamentos` com status (Concluído/Cancelado/Análise e revisão) + `Reabertura de estoque`; etapas 1–3 `EXECUTION_OBSERVED` — **etapa 4 `Fechamento` não exibida**. `Analise.xlsx` = export da etapa 3: **CM final ≡ `B9_CM1`@30/09 em 1.966/1.994 (98,6%)** — 22 `MOD*` sem SB9 (estrutural) + 6 deltas drift demo(30/09)→gravação-f01(21/10); status=sinal(variação) 1.994/1.994. `MV_ULMES`=`20260930` f01+f02; SB9@30/09 em rajadas 02/10 (f02) e 21/10 (f01) — writer `PENDING` (E5). **Erratas**: `Tempo Setup?`=`Som Tempo Propo`; `Calcular Custos Por?`=`Ult Cust Compra` (1ª exec, MC→MP) e `Estrutura` (2ª, PA→PI); "Refaz=DEL100" corrigido — DEL100 é auditoria SB9 distinta; `MA330OK`→`STP_DELPI_*`/`STP_PROTHEUS_*` ausentes (E4). Reuso: `B1_CUSTD`→`standard_cost` `REUSE_CONFIRMED`; `stock_value_official_closure_sql` (SB9) `REUSE_CONFIRMED`; `GET /supplies/cpv` `REUSE_PARTIAL`; orquestração de fechamento `TARGET`. **Gates: R12 G1–G4 PASS · G5 `INCONCLUSIVE` · G6 PENDING**; métricas `45/60 = 75,0%` coleta · `53/90 = 58,9%` auditoria · `0/15`. Residuais → **E12** (sequência oficial/checkpoints/rotina-DIT/efeitos-MATA300 — Controladoria+TI/ERP) + E4/E5 mantidos. Regras `BR-R12-001..006` + `T-R12-01..04` no [doc 85 §11](./85-ciclo2-catalogo-regras-negocio-r01-r15.md); evidência monetária [doc 84 §5.6](./84-ciclo2-paridade-monetaria-relatorios-oficiais.md); adendo [doc 56](./56-proc0072-observacoes-guiadas-fechamento-custos.md); crosswalks [doc 57](./57-proc0072-matriz-mestra-revalidacao-video-e-roadmap-inventarios.md)/[doc 78](./78-ciclo1-crosswalk-narracao-artefatos.md); handoff [doc 82 E12](./82-ciclo2-handoff-pacote-evidencias-owners.md). Zero runtime.

[Doc 80 §47](./80-ciclo2-registro-vivo-investigacao-devin.md) (CF-C2-R15-CUTOFF-SB9-CLOSURE-VERIFY-001, rodada 28): **cadeia produtora do fechamento identificada** — `MATA330` (Recálculo do Custo Médio; JOICI+serviço) → `MATA280` (**Virada de Saldos**; SX1 `MTA280`: "Gera Saldo Inicial", "Atualiza Saldo Atual MOD"; executado como serviço) → rajada `SB9` + saldos iniciais de OP (`SC2.C2_VINI1`/`C2_VINIRP1`/`C2_APRINI1/2/3`). Descoberta estrutural: **`I_N_S_D_T_` grava UTC** (prova SD3 recno×`TTAT_DTIME`: Δ +3h exatos) — a "divergência temporal" da rodada 27 era fuso, não regravação tardia. Em horário local, **5/5 rajadas SB9 de 2026 caem dentro das janelas MATA280** (10/08 coincidente total 15:45–17:11; 18/09, 01/10, 02/10, 21/10 a ±4s). Vídeo reinspecionado: lista `Fechamentos` persiste ciclo de vida (f01-ago "Concluído 18/09 16:05" ≈ fim virada 16:03:52; cancelados não geram SB9; f02-ago parado em "Análise e revisão" até 01/10); botões `Reabertura de estoque`/`Refazer cálculo`; etapa 4 novamente não exibida. `MV_ULMES` por filial = 20260930 (avanço na virada; writer não auditável — SX6 sem TTAT). Timestamps distintos f01/f02 explicados: viradas em execuções separadas (f02-set 02/10; f01-set 21/10 após retificações — correções precedem o snapshot). **Gates: R15 G1–G4 PASS · G5 `INCONCLUSIVE` · G6 PENDING**; métricas `47/60 = 78,3%` coleta · `55/90 = 61,1%` auditoria · `0/15`. Residuais → **E5 estreitado** (confirmar função interna/RPO do MATA280 que insere SB9/`MV_ULMES` — SB9/SX6 sem TTAT) + E4 + **E12.6/E12.7** (semântica reabertura, critério de homologação). Regras `BR-R15-001..007` + `T-R15-01..07` no [doc 85 §14](./85-ciclo2-catalogo-regras-negocio-r01-r15.md); handoff [doc 82](./82-ciclo2-handoff-pacote-evidencias-owners.md); crosswalk [doc 83](./83-ciclo2-crosswalk-evidencias-r01-r15.md). Zero runtime.

[Doc 86](./86-ciclo2-relatorio-final-consolidado-e-handoff.md) (CF-C2-FINAL-CONSOLIDATION-AND-HANDOFF-001, rodada 29): **Ciclo 2 — investigação consolidada** (`CYCLE2_DOCUMENTATION_READY`). Matriz R01–R15 recontada na base — coleta `47/60 = 78,3%` · auditoria `55/90 = 61,1%` · `0/15` concluídos (G6 exige aceite humano). Paridade integral em R01/R02(artefato)/R05/R06/R07/R08/R10/R11; sequência operacional `MATA320→MATA300→MATA330→MATA280→SB9` corroborada temporalmente (R12/R15), sem atribuição interna do writer SB9/MV_ULMES comprovada (E5). Bloqueados por owner: R03 (fonte MATR460 — E2), R04/R13/R14 (sem artefato/fonte). Residuais consolidados E1–E12 com critério de aceite ([doc 82](./82-ciclo2-handoff-pacote-evidencias-owners.md)). Decisões preservadas: CPV vivo (doc 80 §40), E6=C `IMPLEMENTATION_AUTHORIZED=NO` (doc 81). Readiness: `READY_WITH_CONSTRAINTS` para R01/R02/R05–R12/R15; `BLOCKED_BY_OWNER` para R03/R04/R13/R14. **Sem autorização de implementação/runtime** — Nível 2 (design) requer decisões e escopo do PO; Nível 3 requer gate transversal + G6. Próximo passo: revisão e aceite do PO sobre o doc 86.


### Ciclo 3 — Abertura de design condicionado (23/10/2026)

O PO aceitou o encerramento documental do Ciclo 2 com residuais e direcionou iniciar o **design read-only** da Central de Fechamento, sem runtime. [Doc 86](./86-ciclo2-relatorio-final-consolidado-e-handoff.md) mantém as métricas 47/60, 55/90, 0/15 e esclarece que **11/15** itens estão `READY_WITH_CONSTRAINTS` (não 10), enquanto R03/R04/R13/R14 seguem `BLOCKED_BY_OWNER`. A atribuição interna do writer SB9 ao MATA280 segue pendente E5, apesar do forte binding temporal.

[Doc 87 — Abertura Ciclo 3 / intake read-only](./87-ciclo3-abertura-design-central-fechamento-read-only.md): inventário prévio de contratos, boundaries e componentes `@delpi/plugin-ui`; decisões de escopo/estados/reabertura/contratos/homologação; RQ/AC, pacote de decisão e plano page-by-page. **`IMPLEMENTATION_AUTHORIZED=NO` · G6×15 PENDING.**

[Doc 88 — Inventário C3-R01 + pacote de decisões](./88-ciclo3-r01-inventario-contratos-e-pacote-decisoes.md) (CF-C3-01-READONLY-CLOSING-INVENTORY-AND-DECISION-PACK-001, rodada 30): **descoberta material — a fatia read-only já existe no HEAD**: BFF `controllership-finance-api` com `/viewer-context`, `/closing/financial-settlements(+summary)` e `/closing/stock-inventory` (Bearer humano + effective permissions via Core + S2S próprio ADR-010 + passthrough tipado `scope_unavailable`); api-delpi com `/financeiro/stock-inventory` (SB9/SB1 por `B9_DATA`, `branchesAvailable/Missing`, `source_missing` nunca disfarça zero) e `/financeiro/settlements/*` (SE5); MFE com Home + páginas P7 e Baixas. **Lacunas de contrato:** `MV_ULMES`/competências (`TARGET` — candidato `closing-context` na api-delpi), trilha de estados do wizard (`PENDING_EVIDENCE` — E12.5) e homologação (humana, nunca sistêmica — C3-D05=A). Pacote `C3-D01..D06` com recomendações: A(escopo comprovado), A(estados separados), B(reabertura fora da V1), A/B(contrato no owner api-delpi), A(aceite explícito), A(excluir superfícies sem fonte). RQ/AC candidatos RQ-C3-01..09; plano page-by-page P0–P5. **Nenhuma implementação autorizada**; runtime segue bloqueado até decisões + gate transversal.


[Doc 89 — Decisões aprovadas C3-D01..D06 e gate documental R02](./89-ciclo3-decisoes-aprovadas-e-gate-documental-r02.md) (24/10/2026): PO aprovou **A/A/B/B/A/A** exclusivamente para escopo e design. V1 read-only usa seleção por período, filial e contratos vigentes de SB9/baixas; estados separados, reabertura fora, `closing-context`/`MV_ULMES` adiados, homologação humana e superfícies sem fonte excluídas. **`IMPLEMENTATION_AUTHORIZED=NO`**. Próxima rodada: `CF-C3-02-READONLY-DESIGN-CONTRACT-GATE-001` — inventário de HEAD, RQ/AC e design page-by-page sem runtime.


### Ciclo 3 — Crosswalk E2E PROC-0072 e correção de interpretação de escopo (24/10/2026)

[Doc 90 — Crosswalk completo PROC-0072/TÉO → RQ/AC → P1–P6 → capacidades, fontes, contratos e gaps](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md): confirma que a Central de Fechamento é **workflow de ponta a ponta**, envolvendo checklist/automação dos relatórios, PDFs e extratos com validação humana P2, conciliação/cutoff P3, classificação/pendências P4, pacote/versionamento/submissão portal-first/review P5 e configuração P6. A fatia read-only C3-D01..D06 é **somente o incremento inicial de design**, não substitui P1–P6. [Doc 89 §6](./89-ciclo3-decisoes-aprovadas-e-gate-documental-r02.md) esclarece o alcance sem reabrir as decisões aprovadas; [doc 37](./37-p5-submissao-e-revisao-no-portal.md) mantém envio para análise dentro da Minha DELPI (e-mail só notificação). Resíduos de contratos e RQ-P2 detalhados continuam TO_INVENTORY, G6×15 PENDING, **nenhum GO/runtime novo**.


### Ciclo 3 — Decisão de acesso restrito aos documentos históricos da Contabilidade (24/10/2026)

[Doc 91 — Solicitação de nova permission e gate contratual](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md): o PO escolheu expressamente **Opção B** — nova capability RBAC específica de consulta/download de pacotes do fechamento por competência para Contabilidade/DRE. DRE não faz aceite na primeira versão; Controladoria/Joici prepara/valida e disponibiliza, com eventos distintos; histórico por destinatário sob BFF fail-closed. **O manifesto atualmente mantém exatamente duas permissions e a Home requer .access**. Doc 91 registra exceção solicitada ao freeze, rota/permission candidatas e impactos Core/launcher/MFE/BFF/P2/P5, incluindo distinção de destinatário read-only versus reviewer P5 e C2. **Decisão de produto aprovada, contrato técnico e implementação pendentes do gate transversal; nenhuma nova permission ou página efetiva no runtime.**


### Ciclo 3 — Consolidação publicada e próximo gate P2 (24/10/2026)

**[Doc 92 — Estado consolidado C1→C2→C3 e handoff de prontidão P2](./92-ciclo3-consolidacao-e-handoff-continuacao-p2.md):** a consolidação E2E de PROC-0072 foi concluída no [doc 90](./90-ciclo3-crosswalk-end-to-end-proc0072-teo-rq-ac-portal.md), **com residuais de rastreabilidade 1:1 TÉO/RQ e contratos físicos P2/P5 ainda TO_INVENTORY**; não foi implementada a Central completa. Próximo gate técnico recomendado: `CF-C3-P2-DOCUMENTS-CHECKLIST-READINESS-001` — inventariar checklist por item, anexos, validators, versionamento, sources, reuso, segurança e RQ/AC de P2, sem runtime. **A permissão adicional e a página restrita da Contabilidade/DRE estão aprovadas como direção, mas a criação foi explicitamente ADIADA pelo PO** ([doc 91 §8](./91-ciclo3-contabilidade-acesso-documentos-historicos-gate.md)); manifesto/Core/MFE/BFF/rotas de histórico permanecem sem alterações relacionadas. **G6 C2 continua PENDING 15/15. IMPLEMENTATION_AUTHORIZED=NO para estes novos slices.**

### CLARA — Especialista MCP em Controladoria & Finanças

[Doc 94 — CLARA](./94-clara-especialista-mcp-controladoria-financas.md): identidade aprovada — **CLARA** (**C**ontroladoria, **L**eitura, **A**nálise, **R**esultados e **A**companhamento), especialista MCP do Portal na família TÉO/DAVI/VISTA. Princípio aprovado: vê e executa o que o usuário autenticado está autorizado a ver/executar, via contratos da `controllership-finance-api`, com effective permissions do Core e fail-closed — sem identidade privilegiada e sem permission própria (herda o contrato do Portal). Inventário: fundação `shared/delpi_mcp` (taxonomia `DISCOVERY/READ/ANALYSIS/PREPARE/ACT`); especialistas hospedados na API owner; BFF C&F hoje somente READ. **CLARA-D01=B aprovada** em 24/10/2026 (validar/rejeitar/concluir e outras ações permitidas no Portal por delegação, com aval explícito e auditoria); **CLARA-D02..D05 seguem pendentes** para hosting, token, PREPARE/ACT e primeira fatia. Doc 14 §IA reconciliado; roteiro e checkpoints **M00–M06 no doc 93**. **TARGET · `IMPLEMENTATION_AUTHORIZED=NO`.**

### CP00/CP01 verificados e brief P2 (24/10/2026)

[Doc 95](./95-ciclo3-cp00-cp01-rebaseline-e-brief-primeiro-slice-p2.md): checklist original lido em modo somente leitura — **53 itens em escopo** (30 Eletrônico + 23 Físico) rastreados por  com lacunas individualizadas; sem 1:1 com R01–R15 (37 sem R-ID; CK-E-27 faturamento da filial sem investigação). CP01: testes **271/271 PASS** (MFE 91+25, BFF 83, api-delpi 72) e smoke read-only de dados — as duas páginas operam, mas **não reproduzem** os oficiais (settlements lê FK2/FK1, Δ quantificado; stock é snapshot SB9, ). Brief  pronto para GO; bloqueante real:  persistência/owner (doc 45 D3=C). .

### Gate contratual P6-MIN + P2-READ (24/10/2026)

[Doc 96](./96-ciclo3-gate-contrato-e-persistencia-p6-min-p2-read.md): com `CP-D01=A` aprovada, o gate documenta o padrão real de persistência dos BFFs irmãos (schema por app no `postgres-plugins`, runner com checksum SHA-256, seeds por migration, testes PG reais sem mock de atomicidade), o modelo lógico (template/version/item + competence + snapshot congelado + audit append-only), contratos HTTP candidatos (admin P6-MIN + leitura/abertura P2), matriz de autorização e plano de testes. Decisões residuais: seed v1 DRAFT vs PUBLISHED; UI admin mínima no slice. `IMPLEMENTATION_AUTHORIZED=NO` — aguarda GO de runtime.


### Decisões de escopo P6-MIN + P2-READ aprovadas (24/10/2026)

O PO aprovou **seed inicial dos 53 itens em `DRAFT`**, com publicação governada posterior, e **API administrativa mínima sem tela P6**. [Doc 97 — registro vinculante e pedido de GO transversal](./97-ciclo3-p6-min-p2-read-decisoes-po-e-solicitacao-go-transversal.md). Contratos físicos e autorização de implementação continuam pendentes; próximo gate `CF-C3-P6-MIN-P2-READ-TRANSVERSAL-GO-REVIEW-001`. **`IMPLEMENTATION_AUTHORIZED=NO` para esse slice.**

### Revisão transversal GO — `GO_RECOMMENDED` (24/10/2026)

[Doc 98](./98-ciclo3-go-review-transversal-p6-min-p2-read.md): todos os gates materiais PASS (persistência padrão irmão, invariantes, contratos `CONTRACT_FREEZE=PASS`, AuthZ, UI/plugin-ui, plano de testes, escopo, decisões PO). Solicitação `CF-C3-P6-MIN-P2-READ-RUNTIME-GO-001` pronta para o PO. **`GO_RECOMMENDED` ≠ autorização** — `IMPLEMENTATION_AUTHORIZED=NO` até aprovação expressa. Deploy em gate separado.


### Primeiro GO de runtime concedido — 24/10/2026

O PO autorizou **somente o incremento `P6-MIN + P2-READ`**, com seed v1 de 53 itens `DRAFT`, API administrativa mínima sem página P6, competências/snapshot/P2 leitura, testes e Help. **Documento vinculante:** [99 — autorização de implementação e handoff Devin](./99-ciclo3-go-runtime-p6-min-p2-read-e-handoff-devin.md). `IMPLEMENTATION_AUTHORIZED=YES / SCOPE=P6-MIN+P2-READ_ONLY` e `DEPLOY_PRODUCTION_AUTHORIZED=NO`. Registros anteriores `IMPLEMENTATION_AUTHORIZED=NO` neste README são históricos para outros slices ou antes do GO; nenhum outro runtime foi autorizado e os checkpoints CP02/CP03 ainda precisam ser provados.

### Gate contratual P2-Upload executado — 24/10/2026

`CF-C3-P2-UPLOAD-CONTRACT-GATE-001` (documental) publicado em [103 — inventário, contratos TARGET e readiness de P2-Upload](./103-ciclo3-p2-upload-contract-gate.md) e fechado em `CF-C3-P2-UPLOAD-DECISIONS-CONTRACT-CLOSURE-001`: padrão canônico de storage inventariado (metadado no Postgres do contexto + binário em volume `${DELPI_DATA_HOST_DIR}`), modelo `closing_document`/`document_version`/`document_file`, operações U1–U8 TARGET, decisões **D-U1..U6=A PO_APPROVED** ([doc 97 §7](./97-ciclo3-p6-min-p2-read-decisoes-po-e-solicitacao-go-transversal.md); [doc 17](./17-backlog-de-confirmacoes-e-inventarios.md)), lacunas C1–C4 revisadas (idempotência: parte provada pelo padrão supplies-api, transporte/escopo/TTL = **D-U7 pendente** no doc 17) e AC-P2-UP-01..24 no [doc 23](./23-ledger-rq-ac-testes.md). **Upload/runtime NÃO autorizado** — aguarda revisão do GPT Arquiteto e GO próprio do PO. Antes deste gate, o hardening pós-revisão R1/R2/R4 foi concluído (commits `1ad43e04`, `a9e43b33`; adendos nos docs 100/102).


### P2-Upload SLICE-1+SLICE-2 implementados — aguardando revisão arquitetural

GOs `CF-C3-P2-UPLOAD-IMPL-GO-001` e `CF-C3-P2-UPLOAD-SLICE2-IMPL-GO-001` (PO_AUTHORIZED, `PRODUCTION_DEPLOY_AUTHORIZED=NO`) executados: **ciclo documental completo U1–U8** de evidências — upload, listagem, consulta, download auditado, **substituição com OCC** (v anterior `SUPERSEDED`, perdedor `stale_revision` 409), **histórico de versões**, **cancelamento lógico** (`CANCELLED != DELETED`, histórico/arquivos preservados) e **eventos de auditoria** — sobre migration `V003` sem migrations novas (`document_file`/`closing_document`/`document_version` já proviam `state`/`current_version_no`/`revision`/`uploaded_by`), **D-U7=A** no [doc 97 §8](./97-ciclo3-p6-min-p2-read-decisoes-po-e-solicitacao-go-transversal.md), storage durável `${DELPI_DATA_HOST_DIR}/cf-closing-documents` (`.part` → sha256 → rename atômico → transação → compensação), `FOR UPDATE`+`revision` (corrida 4 threads → 1 vencedor), MFE com substituir/versões/cancelar/auditoria e Help sincronizado. Evidência: 308 testes BFF+PostgreSQL real, 115 vitest + 25 estruturais — [doc 100 Adendos SLICE-1/SLICE-2](./100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md). **Validação humana e P5 permanecem TARGET; deploy de produção NÃO realizado.** Relato do executor, não aceite arquitetural.


## Plano mestre consolidado de execução — 24/10/2026

O [Documento 104 — plano mestre E2E de implementação, aceite e deploy por Operador SSH](./104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md) consolida CP02–CP12 em pacotes A–D e três paradas formais (G1 decisões materiais, G2 aceite integrado, G3 release/rollback). Preserva o ledger 23 e este roadmap como authorities de RQ/AC e dependências; não declara runtime nem deploy já executados. Deploy de produção depende de operador SSH autorizado, preflight, backup, rollback e smoke real.


## Execução complementar: concluir pendências antes do refinamento — 25/10/2026

O PO autorizou a execução contínua das lacunas remanescentes da Central P1–P6, mantendo decisões materiais em G1 e G2/G3 de homologação e release. **Documento vigente:** [105 — GO de conclusão integral das pendências antes do refinamento](./105-go-conclusao-integral-pendencias-implementacao-antes-refinamento.md). O [104](./104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md) continua sendo o roteiro E2E e de deploy; o [23](./23-ledger-rq-ac-testes.md), o [37](./37-p5-submissao-e-revisao-no-portal.md) e o [100](./100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md) mantêm contratos/evidências. Nenhum novo deploy foi realizado por esta atualização documental.


## GO de escopo atualizado — CLARA multi-ação, Keycloak e ChatGPT (25/10/2026)

**Documento vigente mais recente:** [106 — CLARA batch inteligente e release SSH/ChatGPT](./106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md). Decisão expressa do PO: múltiplas operações do mesmo pedido com mínima interação, intenção atestada ou aprovação consolidada do lote; controles por ação. Priorizar PROC-0072 + CLARA com knowledge base própria; Sala de interação e expansão de Minhas tarefas adiadas; código preexistente preservado. Não implica G2/G3 aprovado, alteração Keycloak realizada ou deploy executado. A ficha de configuração MCP/ChatGPT deve conter somente metadados públicos comprovados.


## Urgência PO — testar CLARA no ChatGPT antes do aceite final (25/10/2026)

**Diretriz posterior:** [Documento 107 — validação antecipada CLARA no ChatGPT, conclusão do release](./107-clara-validacao-antecipada-chatgpt-release-hoje.md). Após rework de consentimento, **piloto MCP em ambiente não produtivo existente e autorizado → cadastro/teste ChatGPT → fechar G1 owners e homologação G2 → autorização G3 → produção e smoke → cadastro/teste final**. Se não houver ambiente não produtivo apto, executar G1/G2/G3 primeiro, jamais usar produção como piloto sem gates. Meta PO para 25/10/2026; objetivo, não evidência de conclusão. Atualizar Github a cada decisão material/entrega no mesmo commit e não solicitar novo prompt por pequena etapa.


## Homologação guiada G2/G3 — 26/10/2026

A sessão de validação funcional assistida pelo PO, a matriz de testes visual/runtime do Portal P1–P6, os findings, os aceites humanos G2 e as verificações de Operador SSH G3 têm agora ledger próprio: **[Documento 108 — Homologação guiada G2/G3](./108-homologacao-guiada-g2-g3-2026-10-26.md)**. Estado inicial: somente tela Início com screenshot visual; navegação, operações, OAuth/CLARA e smoke continuam TEST_NOT_RUN; sem sign-off G2/G3. Atualizar o Doc 108 por evidência e decision após cada passo, não atribuir PASS por atalhos ou deploy.


## G2 aprovado pelo PO com ressalvas e handoff G3 — 26/10/2026

**G2 do PO foi formalizado como `ACCEPT_WITH_RESIDUAL`** para o escopo local da Central de Fechamento P1–P6 e CLARA, com P7, relatórios oficiais, T03/T05/R04+, seeds e fontes G1 pendentes, e regra V1 de clarificações abertas com C2 bloqueado. Fonte: [Doc 108](./108-homologacao-guiada-g2-g3-2026-10-26.md), decisão `CF-PROC0072-G2-ACCEPT-WITH-RESIDUAL-20261026`; rastro PO [Doc 109](./109-go-po-ultima-rodada-e2e-usuario-g2-g3-2026-10-26.md). **[Doc 110 — Handoff Operador SSH/IAM → Keycloak → ChatGPT](./110-g3-handoff-operator-iam-clara-chatgpt-2026-10-26.md)** é a próxima authority operacional. G3 do Operador, mudanças IAM e smoke autenticado produtivo ainda não concluídos; não inferir deploy/autorização do aceite local.
