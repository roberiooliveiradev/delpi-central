# 39 — Roadmap Mestre de Implementação V1 — Portal Controladoria & Finanças

> **Última revalidação:** [44 — Revalidação A16](./44-a16-revalidacao-final-transversal-2026-10-16.md). A16 continua INCONCLUSIVE; o roadmap permanece PLANNED e não autoriza runtime.

> **Estado:** TARGET / PLANNED / DOCUMENTATION_ONLY — 16/10/2026. Plano executivo para futura execução incremental, não é ordem para desenvolver nem prova de runtime.
>
> **Gate vigente:** `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `IMPLEMENTATION_AUTHORIZED = NO`; `A12/A14/A15 = INCONCLUSIVE` conforme [38 — rebaseline e evidências](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md). Qualquer referência anterior a PASS permanece histórica até revalidação formal.

## 1. Objetivo e fontes de verdade

Converter a especificação da primeira funcionalidade, **Central de Fechamento**, do processo **PROC-0072 — Gestão do Fechamento Mensal da Controladoria**, em sequência de entregas pequenas, verificáveis, com owners, dependências, contratos, aceites e evidência por slice. Não transformar PLANNED em PROVEN.

A ordem de authority segue: [instruções oficiais do GPT Arquiteto](../../11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md) → regras .cursor aplicáveis → ADRs/contratos canônicos → HEAD (schemas/manifests/migrations/código) → testes → docs técnicas vigentes → este roadmap → histórico. O TÉO/Transformômetro é authority de AS-IS e proveniência; GitHub é authority do TARGET, contratos, testes e SHA. Na divergência, **não criar uma terceira regra neste plano**: retornar à authority superior e classificar `EXECUTION_DRIFT` quando a premissa necessária cair.

Este documento é o **índice executivo da ordem futura**, não substitui:
- [18 — readiness e handoff](./18-readiness-e-handoff-de-implementacao.md), [22 — handoff P1–P6](./22-handoff-implementacao-p1-p6.md), [23 — ledger RQ/AC/testes](./23-ledger-rq-ac-testes.md);
- [30 — reuso plugin-ui](./30-plugin-ui-reuse-map.md), [31 — Página do usuário](./31-pagina-do-usuario.md), [32 — Início](./32-inicio-home.md), [24 — navegação](./24-inicio-e-navegacao-principal.md);
- [04 — regras de negócio](./04-regras-de-negocio-consolidadas.md), [14 — segurança](./14-seguranca-rbac-auditoria-e-ia.md), [21 — boundaries](./21-boundaries-produtos-e-owners.md), [29 — Ajuda](./29-ajuda.md);
- [37 — submissão/revisão P5](./37-p5-submissao-e-revisao-no-portal.md), decisões C2, P5-A..J e DEC-01..04;
- [33 — plano mestre de fechamento documental](./33-plano-mestre-fechamento-documental.md), [34 — A14](./34-revisao-transversal-gate-v2.md) e [35 — A15](./35-contratos-regras-scripts-test-matrix-gate-v2.md).

Documentos operacionais associados: [40 — slices/dependências](./40-matriz-dependencias-e-slices-v1.md), [41 — validação e gates](./41-estrategia-validacao-e-gates-implementacao-v1.md), [42 — briefs e execução Cursor](./42-playbook-brief-cursor-execution-report-v1.md) e [43 — rollout/observabilidade](./43-rollout-operacao-e-handoff-v1.md).

## 2. Escopo V1 e identidades congeladas

| Contrato | Valor TARGET |
|---|---|
| Produto / plugin id | `controllership-finance` |
| MFE | `plugins/controllership-finance` |
| Rota base do MFE | `/apps/controllership-finance` |
| BFF | `controllership-finance-api` |
| Rota base da BFF | `/apps/controllership-finance-api` |
| CSS root | `.portal-controllership-finance` |
| Permission codes, e somente estes | `controllership-finance.access` e `controllership-finance.manage` |
| Primeira capability | Central de Fechamento / PROC-0072 |

**Fronteira:** MFE → BFF do Portal → adapters/contratos dos owners, nunca browser → `api-delpi` diretamente. Core é owner de identidade, effective permissions, usuários e notificações; `api-delpi` de regras SQL/TOTVS/Protheus canônicas; `strategic-indicators-api` de metas/indicadores; BFF de estado operacional P5 e regras que pertencem a este produto. Sem import de domain/application vizinho nem usar banco do vizinho como API. Seguir Clean Architecture com domain isolado de HTTP, DB, framework e SDK.

**Fora do escopo por decisão vigente:** permission por página/botão/reviewer/área/filial; edição de identidade local; envio de anexo do pacote por e-mail; link público de revisão; reversão/retificação de aceite P5 por UI ou endpoint V1; escrita de sacramentação ERP pela P3; criação automática de tarefa pela Sala; TaskEntity paralela para projections. Não antecipar outros processos/portais nem criar serviços de infraestrutura apenas por preferência.

## 3. Portas de autorização: não confundir plano com execução

| Gate | Condição mensurável | Estado inicial |
|---|---|---|
| G-DOC / A16 | A12/A14/A15 revalidados, residual search, owners, Help, RQ/AC e freeze documentados | PENDING / INCONCLUSIVE |
| G-FREEZE | `PORTAL_DESIGN_FREEZE`, `PRODUCT_CONTRACT_FREEZE`, `SECURITY_MODEL_FREEZE` e `TEST_STRATEGY_FREEZE` explícitos e sustentados | PENDING |
| G-AUTH | Aprovação posterior explícita do PO para implementação e `IMPLEMENTATION_AUTHORIZED=YES` registrado | NO |
| G-SLICE | HEAD + `git status`, .cursor, owners, contratos, RQs/AC, positive/sibling/negative, escopo e stop conditions do slice | NOT_STARTED |
| G-DELIVERY | PR/commit, testes realmente executados, security/UX/Help, postcondition e residual search | NOT_RUN |
| G-RELEASE | Readiness de operação, deploy/rollback/smoke em ambiente aplicável, gate de publicação separado | NOT_AUTHORIZED |

**Nenhum diff runtime será iniciado por este roadmap.** Criar e versionar os planos não modifica G-DOC, G-FREEZE, G-AUTH ou G-RELEASE. Quando GitHub connector não disponibilizar working tree, `git status = INCONCLUSIVE` até executor com checkout registrar evidência.

## 4. Estratégia de entrega: página por página com dependências explícitas

A ordem proposta implementa primeiro a experiência comum, depois as páginas do processo. A **topbar em runtime** preserva sua ordem funcional própria (Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda); não confundir ordem do menu com ordem de PRs. Página do usuário é deep route, não novo item de topbar.

~~~text
R0 — Inventário técnico/documental e revalidação A12/A14/A15/A16
       → quatro FREEZES com evidência → PO AUTHORIZE
       |    (sem GO, STOP; sem scaffold/runtime)
       v
R1 — Página do usuário → Início → Visão geral → Minhas tarefas
                        → Sala de interação → Administração → Ajuda
       |
R2 — P1 Cockpit → P2 Checklist → P3 Estoque → P4 Pendências
       |
R3 — P5 Pacote/Finalização/Submissão/Revisão
       |
R4 — P6 Administração/Configuração (UI completa) + integração final
       |
R5 — hardening, regressão, readiness operacional e release governado
~~~

**Ordem de páginas é proposta de execução, não bypass de dependências.** Quando um contrato/subconjunto de P6 for necessário para P2 ou P5 (templates, áreas de revisão obrigatórias, versões/snapshots), seu **inventário e contrato** precedem o consumer. A implementação mínima do owner somente poderá ocorrer no slice aprovado e com RQ/AC, sem entregar toda a UI P6 antecipadamente. Caso a dependência mude a ordem material ou o ownership, revisar o plano/gate e registrar a razão antes de codificar. O antigo texto do doc 18 que inicia em “fundação técnica → P1” é **sequência histórica de investigação operacional** e não substitui a fila A01–A13 documentada no 33.

## 5. Fases com outcomes verificáveis

### R0 — Pré-flight e fechamento transversal (documentação; sem runtime)

**Objetivo:** completar A12/A14/A15/A16, conferir padrões atuais de API/Portais antes de scaffold, resolver ou classificar explicitamente T01–T05 e E01–E06 por necessidade, mapear integração Core T05 grupos/funções elegíveis e vínculo do coordenador P5, vigência e snapshot P6, fontes de P3 T03, DTOs/eventos/concorrência. **Não pressupor** que busca de diretório por permission já fornece grupo/função.

**Saída:** ata de gate documentada com evidência e SHA; owners/contracts/bindings; matriz de testes atualizada; GO/NO-GO explícito. **Sem gate PASS e autorização explícita → não executar R1.**

### R1 — Páginas comuns e fundação mínima dependente de uso

A01 **Página do usuário** primeiro (docs 31 e 30): identidade/foto/Core, leitura autorizada do próprio perfil e de outro usuário do mesmo Portal conforme D1/D2, edição apenas no Meu Perfil da plataforma; proteção contra vazamento de RBAC. Inventariar Core S2S e `@delpi/plugin-ui` antes de scaffold; BFF autoriza fail-closed.

Depois A02 **Início** (doc 32), A03 **Visão geral** (doc 25), A04 **Minhas tarefas** (doc 27), A05 **Sala de interação** (doc 26), A06 **Administração** (doc 28) e A07 **Ajuda** (doc 29). Seguir [40](./40-matriz-dependencias-e-slices-v1.md) para dependências H01/O04/O05/TSK/R/ADM/HELP e [41](./41-estrategia-validacao-e-gates-implementacao-v1.md) para qualidade. A Ajuda deve ser sincronizada **na mesma PR** de cada mudança user-facing; A07 consolida a superfície comum, não posterga o requisito.

**Saída por slice:** página/deep link funcional, proteção BFF, estados LOADING/EMPTY/PARTIAL/UNAVAILABLE/ERROR/FORBIDDEN/NOT_FOUND quando aplicáveis, desktop/mobile, claro/escuro, teclado/foco, Help, testes e evidência fresca. O Portal não deve expor navegação para telas futuras.

### R2 — Central de Fechamento, P1–P4

- A08/P1 **Cockpit:** agrega estado e bloqueios de owners P2–P5, sem assumir suas regras. T01/T05 como stop de integração.
- A09/P2 **Checklist/Documentos:** snapshot, requirements, evidências, validação, versionamento e atores autorizados; E05/E06 e T05; não confundir upload com validação.
- A10/P3 **Estoque/Cutoff/Conciliação:** status/freshness, revalidação e paridade monetária exata (R$ 0,00), `STOCK_CLOSED` terminal Portal V1; T03 é STOP para confirmar o owner ERP e sua semântica — nenhuma escrita canônica direta.
- A11/P4 **Classificações/Pendências:** apresentação e operação nas regras do owner; não replicar domínio alheio, confirmar T01/T05.

**Saída:** comportamento positivo, sibling e negativo por eixo, fonte indisponível nunca vira “zero/sucesso”, auditable state e owner preservado.

### R3 — Central de Fechamento, P5 (A12)

Finalização congela uma `PackageVersion` imutável; submissão e revisão ocorrem dentro da Minha DELPI, com Core Notifications como aviso e sem rollback por falha de e-mail. Quórum C2: **todos os pacotes aplicáveis submetidos, um aceite válido para cada área obrigatória da versão vigente e nenhuma clarification aberta**, sem desfecho terminal rejeitado. Áreas obrigatórias versionadas P6 e congeladas no snapshot da submissão. Nova PackageVersion reinicia os aceites; reatribuição não reescreve autoria nem remove aceite válido; nenhuma reversão de aceite por API/UI V1. `CHANGES_REQUESTED` é distinto de `REVIEW_REJECTED`. Rejeição da área não encerra competência automaticamente: somente o coordenador formal com ACCESS, vínculo, scope e reason confirma terminalmente; sem confirmação, permanece pendente. Rejeição terminal torna TaskProjections não acionáveis, preservando o histórico.

**STOP material:** sem inventário Core T05 de atributo/função/grupo, vínculo operacional, contrato P6 de áreas/snapshot, estado/DTO/evento, controle concorrente e testes, **não implementar submissão ou aceite**. Documento 37 é a authority temática.

### R4 — P6 interface completa, integração e cross-page

A13/P6 completa templates, catálogos, áreas obrigatórias por tipo de pacote e versões prospectivas, publicadas com `controllership-finance.manage` efetivo **e** escopo administrativo, justificativa e auditoria. Snapshots abertos não mudam. Integração P1–P6 revalida links, tasks, notificações, estados e Help, sem promover “tela pronta” a outcome de competência. Ajustar ordem se a implementação de contrato owner P6 antecedeu a UI por dependência demonstrada.

### R5 — Qualidade integrada e readiness de publicação

Executar regressão por contexto, AuthZ negativas e por recursos irmãos, contracts, concorrência/idempotência, acessibilidade, builds/MFE federation e todos os smokes materiais; observabilidade, release/rollback e aceite operacional nos termos do [43](./43-rollout-operacao-e-handoff-v1.md). Não inferir smoke nem conclusão mensal por HTTP 200.

## 6. Principais riscos e bloqueios atuais

| Risco/dependência | Responsável pelo contrato | Efeito/stop |
|---|---|---|
| Core T05 — grupo/função, elegibilidade por área, effective permissions e coordenador | Core para identidade/atributos; P5 para atribuição e scope | Sem prova de vínculo, não liberar ações P5; falhar fechado |
| P3 T03 — estado ERP/TOTVS/cutoff | api-delpi / authority canônica ERP a inventariar | Sem prova da fonte, não criar `STOCK_CLOSED` por interpretação local |
| P6 configuração e snapshot por tipo de pacote | P6 owner; P5 consumidor | Não concluir/aceitar P5 com catálogo desconhecido ou mutável retroativamente |
| Contratos físicos/eventos/OCC por slice | BFF/owner respectivo após inventário | Sem contrato, bloquear write ou estado concorrente |
| H01 / O04/O05 / R01–R05 / TSK01–TSK05 / ADM01–ADM07 | respectivos owners atuais, a confirmar no HEAD | Degradação honesta e stop seletivo; não criar banco/serviço por antecipação |
| Help e UX | MFE com `@delpi/plugin-ui` | Sem Help sincronizada/teclado/tema/foco, entrega incompleta |

Conforme [40](./40-matriz-dependencias-e-slices-v1.md), cada linha exige **evidência do producer e consumer**, não simples busca textual. Caso uma descoberta altere owner, framework, permission, contrato, persistência, integration ou deprecation, devolver `DECISION_REQUIRED` para a escolha real, com opções e impactos; `EXECUTION_DRIFT` se a premissa previamente aprovada foi invalidada.

## 7. Governança de execução e versionamento

Fluxo obrigatório: **USER GOAL → GPT BRIEF → CURSOR INVENTORY/EXECUTION → EXECUTION REPORT → GPT REVIEW → REWORK quando necessário → VERIFY OUTCOME → DOCS/EVIDENCE → COMMIT/SHA → NEXT SLICE**.

Uma PR deve corresponder ao menor slice de comportamento/owner coerente; não juntar páginas por conveniência, não reduzir testes para fazer CI passar, não avançar quando `FAIL` ou `INCONCLUSIVE` se referir a precondição material. Registrar HEAD base/final, git status, files, RQ/AC, positiva/sibling/negativa, Help, safety, CI, smoke, residual search, SHA e decisão `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

**Sem cronograma, capacidade ou datas inventadas:** estimativas, priorização comercial e corte de release requerem planejamento posterior com equipe/owner, e não alteram o contrato funcional aprovado. A ordem acima é a baseline de trabalho sujeita a dependências comprovadas, não compromisso de prazo.

## 8. Critério de saída do pacote documental deste roadmap

Documentos 39–43 publicados, links no README, cobertura integral das superfícies A01–A13 e dos gates A14–A16, matriz RQ/AC e dependências, playbook Cursor e plano operacional rastreáveis. **Esta saída significa apenas ROADMAP_DOCUMENTED = PASS**, nunca `DOCUMENTATION_CLOSURE_COMPLETE=PASS`, `IMPLEMENTATION_AUTHORIZED=YES`, teste executado, deploy ou aceite de negócio.

**Próximo passo real antes de runtime:** execução do inventário residual de A12/A14/A15, gate A16 com evidência sobre HEAD e autorização explícita posterior.