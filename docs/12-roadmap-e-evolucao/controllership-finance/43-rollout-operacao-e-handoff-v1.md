# 43 — Plano de Rollout, Operação, Observabilidade e Handoff V1

> **REBASELINE 24/10/2026:** As ondas W0–W5 aqui são planejamento histórico de rollout de todo o Portal. A **ordem incremental atual da Central de Fechamento**, com checkpoints de negócio e segurança, consta do [Documento 93 — Roadmap executivo E2E com checkpoints reais](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md). A permission e página histórica da Contabilidade/DRE estão adiadas pelo PO (doc 91). Nenhum release ou migração foi autorizado por esse rebaseline.
**Estado:** TARGET / PLANNED / NOT_DEPLOYED. Somente planejamento operacional do Portal Controladoria & Finanças; **não** concede autorização de implementação, deploy, acesso a ambiente, migração ou go-live.

Fontes: [39 — Roadmap](./39-roadmap-mestre-implementacao-v1.md), [40 — slices](./40-matriz-dependencias-e-slices-v1.md), [41 — gates](./41-estrategia-validacao-e-gates-implementacao-v1.md), [14 — segurança](./14-seguranca-rbac-auditoria-e-ia.md), [21 — boundaries](./21-boundaries-produtos-e-owners.md), [29 — Ajuda](./29-ajuda.md), [35 — contratos/testes](./35-contratos-regras-scripts-test-matrix-gate-v2.md). Revalidar padrões vivos de gateway, plataforma, observabilidade e operação no HEAD antes de decidir mecanismo de deploy.

## 1. Duas decisões independentes: implementar e publicar

1. **Gate de implementação:** A12/A14/A15/A16 e quatro freezes PASS com evidência; aprovação explícita posterior do PO, `IMPLEMENTATION_AUTHORIZED=YES`; releases permanecem bloqueadas.
2. **Gate de publicação:** implementação testada, owners/consumers integrados, segurança, dados, operação e experiência com evidence; aprovação operacional de release, **separada** da implementação. Nenhum merge/HTTP 200/documento deve alterar este gate.
3. Não inventar nome de ambiente, cluster, job, segredo, SLO ou janela de mudança. Inventariar deployments/API/MFE existentes, pipeline e owner conforme `platform-delivery-runtime-operations.mdc` e políticas de segurança.

## 2. Ondas futuras e critérios de entrada

| Onda | Superfícies | Pré-condição | Condição observável para ativar |
|---|---|---|---|
| W0 — Preparação | Inventário técnico, Core contracts, plugin-ui, BFF/MFE patterns | G-DOC + G-FREEZE + G-AUTH | contrato e monitorabilidade aceitos; não é release de feature |
| W1 — Common first | Página do usuário, Início, Visão geral, tarefas, Sala, Administração, Ajuda | IMP-01..07 validados individualmente | Somente rotas reais/autorizadas; Help e authz same slice; nenhum menu futuro |
| W2 — Central operacional | P1/P2/P3/P4 | IMP-08..11, sources T01/T03 e E/T aceitos | blockers honestos, validação auditável, estoque canônico; sem fake completion |
| W3 — Revisão e encerramento | P5 (PackageVersion, submit in-app, accept por área, coordenação, C2) | Core T05 atributos corporativos, P6 area snapshot, states/OCC/projections e testes aprovados | outcome C2/terminal comprovado sem bypass; notificações não alteram estado |
| W4 — Catálogos e configuração completa | P6 UI e contratos transversais | DEC-04 MANAGE + administrative scope, versão/prospectividade | novos snapshots prospectivos, version/audit, sem retroatividade |
| W5 — Release integrada | P1–P6, navegação, UX, Help, operações e fontes | regressão E2E + smoke materiais + rollback + aprovação de mudança | release decision formal, checklist operacional e evidence |

A onda W2/W3 depende do estado da API e do deployment real: é proibido ativar uma operação que dependa de producers ausentes. A infraestrutura/contrato P6 pode anteceder sua UI completa **somente** por dependência comprovada e micro-slice aprovado, conforme doc 40.

## 3. Estratégia de ativação e visibilidade

- Feature runtime e menus devem ser ativados apenas quando capability real, autorização e Help estiverem funcionando. Não expor placeholders/“Em breve” que chamem APIs inexistentes ou conteúdo de administração a usuários sem MANAGE.
- **Topbar canônica:** Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda. Página do usuário é deep route. P1–P6 são navegação subordinada à Central de Fechamento.
- URL/deep link/F5 devem preservar contexto e reautorizar no backend: competência, destinatário, item, área e período. Não confiar em permissão, função ou unidade enviada pelo cliente.
- Se flags, kill switch ou canary forem padrão da plataforma, **inventariar mecanismo real** antes de propor campos/serviços novos. Planejamento aqui não introduz solução exclusiva.
- Help deve ser publicada junto de cada funcionalidade user-facing. A visão geral do manual só lista o que já existe em runtime, em PT-BR, com links autorizados.

## 4. Preparação operacional e responsabilidades

| Responsabilidade lógica | Owner a confirmar no HEAD | Evidência antes do release |
|---|---|---|
| MFE e integração com shell/menu | Owner do Portal + padrões da plataforma | manifest/route, Module Federation/build, plugin-ui, isolation CSS, deep links |
| BFF do Portal | Owner do Portal, após inventário do padrão API | OpenAPI/DTO/errors, health/readiness, resource AuthZ, observability, load adequado |
| Identidade, effective access e directory | Core e time de identidade | S2S autorizado, denial/503 fail-closed, binding corporativo T05 para P5, sem defaults |
| SQL/TOTVS/cutoff | api-delpi e owner ERP | dados, periodo/freshness, status canônico e paridade; nenhum write local |
| Strategic indicators | strategic-indicators-api | owner/source/formula/version e tratamento de UNAVAILABLE |
| Mensagens/notificações | Core para notification, context owner para Sala | teste de destinatário/ACL, retry, dedup, nenhuma reversão de estado |
| Dados stateful P2/P5/P6 | Owner do produto, sem DB vizinho | schema/migration, backup/restore quando material, audit, OCC/idempotência e histórico imutável |
| Publicação/rollback | Owner da plataforma/operação a identificar | checklist de deploy, mudança, smoke, fallback e pós-condição |
| Ajuda/treinamento | Owner MFE/Produto | conteúdo versionado, deep links e suporte com terminologia atual |

**Papéis acima são responsabilidades técnicas, não nomeação de pessoas ou concessão de permission.** Se a autoridade de release ou deployment for escolha nova, pedir decisão formal quando material; não criar aprovação tácita em MANAGE.

## 5. Observabilidade mínima — contrato de evidência, não stack nova

Cada operação material deve permitir diagnosticar:

- Request/context correlation ID, operação, produto, competence/resource tokenizado quando necessário, source owner, version e outcome, sem JWT, segredo ou PII sensível em logs comuns.
- Para AuthZ: resultado allow/deny, effective permission e motivo de decisão **sem expor atributos pessoais desnecessários**; indisponibilidade de Core, tempo de resposta e falha fechada.
- Para P2/P5/P6: actor, timestamp, reason, previous/new state e versão; eventos auditáveis e idempotência sem alterar o histórico.
- Para integrações: disponibilidade/freshness de api-delpi, Core, indicadores, notificações, realtime; error kinds 403/404/409/503 e latência, sem confundir HTTP 200 com outcome.
- Para UX: erro/partial/source unavailable com mensagem honesta; **não** enviar dados financeiros ou identificadores sensíveis para analytics não autorizado.

**Proibido:** inventar stack de métricas/logs, coletar tokens, registrar body completo de pacote/revisão, salvar secrets no frontend, ocultar falha de source com zero ou default. SLO/alertas com limites quantitativos são `TO_INVENTORY` até padrão operacional owner.

## 6. Plano de recuperação / rollback por impacto

| Situação | Comportamento seguro e reconciliação |
|---|---|
| Deploy MFE ruim / incompatibilidade de MF | Desativar rota/feature pelo mecanismo de plataforma provado, restaurar release compatível sem alterar dados; validar menu/Help após retorno |
| BFF ou Core indisponível | Bloquear writes e decisões sensíveis (fail-closed), retornar estados de error/unavailable/partial apropriados; não reutilizar permissions stale de cliente |
| Falha de source ERP/indicador | Não computar zero, READY ou `STOCK_CLOSED` localmente; preservar último valor apenas com freshness/contrato explícitos; documentar recuperação |
| Notificação/e-mail falhou após submissão | Retentar por mecanismo owner quando permitido; **não** fazer rollback da submissão P5 já persistida |
| Conflito de versionamento/concorrência | Rejeitar stale write sem perda; recuperar/readback e pedir nova intenção; sem last-write-wins silencioso |
| Erro em config P6 | Publicar versão corretiva **prospectiva** após autorização e testes; snapshots históricos permanecem iguais |
| Erro em aceitação P5 | DEC-03: **nenhuma reversão por UI ou endpoint V1**; registrar incidente fora do fluxo; não alterar DB/audit manualmente |
| Competência terminal rejeitada | Manter histórico; TaskProjections não acionáveis; não reabrir pela UI V1 por atalhos |
| Migration stateful | Planejar backup/readback/rollback com owner e constraints antes do primeiro write; nunca editar migration aplicada nem resetar produção |

O rollback de código **não equivale** a reverter decisões de negócio. Retenção, cleanup, reversão de dados e compatibilidade são contratos a decidir/verificar no slice material, não por inferência deste plano.

## 7. Smoke de release e aceite operacional

### Checklist de GO/NO-GO (somente após desenvolvimento e autorização)

- [ ] SHA de release e build/deploy idênticos aos artefatos testados; pipeline e regras de branch válidos.
- [ ] Core JWT/effective permissions: caso ACCESS, MANAGE, nenhum, usuário fora de scope e Core 503 exercitados.
- [ ] BFF resolve resource scope, ownership, business rule; sem chamada browser→api-delpi.
- [ ] Páginas ativas têm estados completos, URLs/F5, teclado/foco, claro/escuro, mobile, Help PT-BR, sem navegação futura.
- [ ] T03 prova source ERP; O05 prova fórmulas/indicadores; source unavailable não vira falso sucesso.
- [ ] P5 testa C2 sobre duas áreas, versões e recipients; rejection pending/terminal, notifications failure e audit; P6 snapshots prospectivos.
- [ ] Testes reais positive/sibling/negative e contrato passaram no ambiente da mudança.
- [ ] Não há drift de migration, schema, contract, manifest, owner e CI.
- [ ] Observabilidade, response owner e rollback verificados com logs/smoke, sem secrets.
- [ ] Treinamento/manual/documentação operacional versionados no mesmo SHA quando material.
- [ ] Owner operacional e PO autorizam publicação segundo processo da plataforma, registrada com SHA.

Para cada item: evidência/URL, ambiente, hora, owner, status. Se não executado: `TEST_NOT_RUN`; evidência incompatível com release SHA: `STALE_EVIDENCE`; dúvida material: `INCONCLUSIVE`. **Não marcar PASS porque CI static foi verde.**

## 8. Handoff pós-publicação

Registrar release SHA, tickets/incidentes, owners de suporte por contexto, evidência de ingestão/observabilidade, smoke final, instruções de rollback e Help linkável. Mudanças em Core/TOTVS/indicadores que afetam semântica exigem contract revalidation e novo gate. Não habilitar novos macroprocessos automaticamente.

**Estado deste plano:** `PLANNED`. `IMPLEMENTATION_AUTHORIZED=NO`, `DEPLOY_AUTHORIZED=NO`, `RUNTIME_TESTS=TEST_NOT_RUN`.