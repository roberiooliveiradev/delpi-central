# 14 — Segurança, RBAC, Auditoria e IA

## Autorização

JWT identifica e contextualiza, mas não é a fonte final de permissions.

```text
capability
AND resource_scope / ownership
AND business_rule
```

A autorização final deve ocorrer server-side e fail-closed.

## ACCESS

Dentro do acesso e ownership autorizados:
- operar competência;
- consultar e tratar checklist;
- anexar evidências;
- marcar N/A quando permitido;
- consultar histórico;
- operar pendências;
- criar item excepcional da competência;
- executar ações operacionais previstas.

## MANAGE

Autoriza administração/configuração:
- templates;
- catálogos;
- validators;
- vigências;
- promoção de item excepcional;
- correções estruturais;
- publicação.

`MANAGE` não implica automaticamente `ACCESS` operacional. Se o mesmo usuário precisar usar as superfícies operacionais, deve possuir `controllership-finance.access` conforme effective permissions do Core.

Não criar permission por botão, tela, endpoint, CRUD, filial ou unidade.

Para este Portal, filial/unidade é dimensão de dados quando aplicável, não permission code dedicado.


## Página do usuário

Contrato detalhado: [31-pagina-do-usuario.md](./31-pagina-do-usuario.md).

Decisões congeladas:

```text
D1 = viewer com controllership-finance.access
     pode consultar perfil corporativo básico de outro usuário
     com acesso ao mesmo Portal.

D2 = permission labels + technical codes
     aparecem somente no próprio perfil.
```

AuthZ server-side:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND target_user_has_app_access(controllership-finance)
```

Regras:

- `MANAGE` sozinho não implica `ACCESS` ao perfil;
- target sem acesso ao Portal → 404;
- outro usuário nunca expõe roles, groups, permission codes, superadmin ou capabilities administrativas;
- self pode exibir somente os permission codes deste Portal;
- Core continua owner de identidade/person profile/foto/effective permissions;
- o Portal não cria permission nova, tabela de perfil ou storage de foto;
- resolução de permission indisponível → fail-closed.

## Minhas tarefas

Contrato detalhado: [27-minhas-tarefas.md](./27-minhas-tarefas.md).

AuthZ:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND projection.assignee_user_id = authenticated_user
AND owner_resource_access
```

Regras:
- a worklist é self-only;
- frontend não escolhe outro `userId`;
- `MANAGE` não cria visão de equipe;
- TaskProjection não concede acesso ao recurso;
- owner reautoriza no deep link;
- blocker, warning ou mention sem responsabilidade individual não geram task;
- nenhum permission code novo é criado para source/task/action;
- source failure não pode ser convertido em empty;
- due/overdue só existem quando o owner possuir regra formal.

## Administração

Contrato detalhado: [28-administracao.md](./28-administracao.md).

AuthZ:

```text
authenticated
AND effective_permission(controllership-finance.manage)
```

Regras:
- `MANAGE` é a única permission administrativa do Portal;
- `ACCESS` sozinho não altera mestre;
- `MANAGE` não implica `ACCESS` operacional;
- nenhum permission code adicional por catálogo, template, CRUD, unidade ou ação;
- responsible/validator/recipient referenciam identidade do Core, mas Administração não cria usuário, role nem permission;
- writes usam optimistic concurrency e falham em stale version;
- publicação/inativação/audit ocorrem server-side e fail-closed;
- published version e histórico não podem ser sobrescritos silenciosamente;
- hard delete de referência histórica não faz parte da V1.

## Ajuda

Contrato detalhado: [29-ajuda.md](./29-ajuda.md).

Regras:
- rota `/help` exige `controllership-finance.access`;
- conteúdo runtime respeita feature availability e effective permissions;
- seção/links de Administração exigem `controllership-finance.manage`;
- hash de seção não bypassa AuthZ nem revela conteúdo MANAGE;
- tool links usam destinos internos tipados; não aceitar URL arbitrária em conteúdo;
- Ajuda V1 não cria endpoint, DB, CMS ou editor administrativo;
- ausência de capability futura significa ausência da instrução runtime, não conteúdo disabled que revela comportamento ainda não liberado.

## Validator

Validator é papel/responsabilidade operacional, não sinônimo de MANAGE.

```text
MANAGE_APPROVAL != EVIDENCE_VALIDATION
```

## Reviewer externo / P5

Reviewer externo da Controladoria é usuário autenticado da Minha DELPI, não acesso público.

AuthZ:

```text
authenticated
AND effective_permission(controllership-finance.access)
AND Core_corporate_group_or_function_eligibility_for_required_area
AND reviewer_assignment/resource_scope
AND current_PackageVersion_and_area_snapshot
AND package_business_rule
```

Regras:
- não existe `controllership-finance.review`;
- reviewer não recebe MANAGE por ser reviewer;
- assignment não concede app access global;
- deep link de notification é reautorizado no BFF;
- package não é anexado ao e-mail;
- e-mail/notificação não constitui prova de autorização nem de review;
- package fora do scope é rejeitado server-side;
- reviewer não edita PackageVersion finalizada/submetida.

## Auditoria

Eventos materiais devem registrar, conforme aplicável:
- actor;
- timestamp;
- competência;
- empresa/unidade;
- entidade;
- before/after;
- reason/comment;
- correlation.

Cobrir:
- snapshot;
- item excepcional;
- anexos/versões;
- N/A;
- validação/rejeição;
- substituição;
- reversão;
- correção estrutural;
- cutoff/revalidação;
- fechamento;
- pacote/envio;
- esclarecimentos;
- mudanças mestre.

## Negative cases

- ACCESS alterando mestre;
- acesso direto a recurso fora de ownership/autorização;
- UI escondendo botão, mas backend aceitando;
- IA acessando dados fora do acesso/ownership autorizado;
- MANAGE apagando histórico;
- troca de validator para contornar rejeição;
- delete de evidência rejeitada;
- submissão de package para reviewer sem ACCESS/scope/business rule;
- usuário sem ACCESS consultando perfil do Portal;
- perfil de outro usuário vazando permissions/capabilities;
- usuário consultando task de outro usuário;
- MANAGE usado como bypass para team worklist;
- projection de recurso ao qual o usuário perdeu acesso;
- ACCESS alterando template/catálogo;
- stale admin write sobrescrevendo revisão nova;
- Administração criando usuário/role/permission no lugar do Core;
- hard delete de item/versionamento histórico;
- Help exibindo instrução administrativa para ACCESS-only;
- deep link de Help revelando seção não autorizada;
- tool link do manual navegando para URL arbitrária.

## IA

Pode:
- explicar;
- resumir;
- sugerir;
- investigar;
- apontar evidência;
- comparar padrões.

Não pode:
- autorizar;
- validar;
- rejeitar;
- sacramentar;
- concluir;
- enviar;
- alterar configuração;
- contornar business rules.

## Dados sensíveis

Não expor secrets/tokens em frontend state, prompts comuns ou logs.


## Decisões supervenientes do Product Owner — P5-A a P5-E (15/10/2026)

**TARGET / PO_APPROVED / DOCUMENTATION_ONLY — no runtime changes.** Este registro complementa C2 e prevalece sobre a interpretação anterior de D-P5-01 (unanimidade por identidade): o quórum é por **área/especialidade obrigatória**, não por cada usuário elegível. A multiplicidade de pessoas elegíveis na mesma área não cria múltiplos votos obrigatórios.

| Decisão | Regra aprovada | Relação com decisão anterior |
|---|---|---|
| P5-A | Um aceite por área obrigatória, executável por qualquer usuário elegível daquela área | D-P5-01 reinterpretada: unanimidade de áreas obrigatórias, não de pessoas |
| P5-B | Somente autor de um aceite pode alterá-lo; outra pessoa atua somente com reatribuição formal | Complementa D-P5-03; sem reversão livre na UI V1, preservar trilha imutável |
| P5-C | ACCESS efetivo + grupo/função corporativa + escopo do recurso + regra de negócio | Complementa D-P5-04; Core é owner da identidade/effective permissions; P5 controla workflow e scope |
| P5-D | Rejeição terminal encerra a competência em estado REJECTED, distinto de MONTHLY_CLOSING_COMPLETED; não exige ressubmissão | Concretiza D-P5-05, mantendo CHANGES_REQUESTED distinto de rejeição terminal |
| P5-E | Nova PackageVersion exige novo aceite de todas as áreas obrigatórias, sem herdar aceites da versão anterior | Complementa D-P5-02 e preserva versionamento imutável |

**C2 atualizado semanticamente:** conclusão mensal requer todos os pacotes aplicáveis submetidos, aceites válidos da **versão vigente** para cada área obrigatória e nenhuma clarification aberta. Qualquer rejeição terminal impede MONTHLY_CLOSING_COMPLETED e resulta no desfecho de competência rejeitada, com auditoria. Não inferir que uma permission genérica concede approval irrestrito.

**AuthZ invariant:** JWT identifica; Core resolve `controllership-finance.access` efetivo; BFF valida função/grupo corporativo elegível, área obrigatória, resource scope/ownership e business rule, fail-closed. A origem/contrato preciso do grupo/função Core permanece **TO_INVENTORY (T05)**; não criar permission code para reviewer, área, botão, filial ou unidade. `controllership-finance.manage` não substitui ACCESS.

**Auditoria mínima:** ator Core, ação, instante, competência, recipient package, PackageVersion, área/atribuição usada, decisão e justificativa quando aplicável, mudança de responsável e referência ao evento anterior. Registro original não é apagado ou reatribuído retroativamente; mudança é novo evento auditável.

**SUPERSEDED / PO_APPROVED (16/10/2026):** reatribuição mantém aceite/autoria (P5-F); nenhuma reversão na UI ou endpoint V1 (P5-G/DEC-03); P6 congela áreas obrigatórias em snapshot (P5-H/DEC-04); revisão por área + confirmação de competência pelo coordenador formal com ACCESS/vínculo/scope (P5-I/DEC-01/02); rejeição terminal torna TaskProjections inativas sem apagar histórico (P5-J). Residual exclusivamente técnico a inventariar: Core T05 corp group/function S2S, DTOs/eventos, state IDs, P6 storage/OCC e consumers. Não reabrir decisões PO sem evidência material nova.

**Gate:** `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_RULES`; `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `IMPLEMENTATION_AUTHORIZED = NO`. Estes textos registram decisões de produto, não demonstram testes, código, contratos físicos, rebase nem execução de smoke.


## Decisões PO P5-F a P5-J — consolidação contratual vigente (16/10/2026)

**TARGET / PO_APPROVED / DOCUMENTED_NOT_IMPLEMENTED.** Este adendo é superveniente aos registros de perguntas abertas P5-F..J e prevalece quando notas históricas anteriores conflitarem. C2, D-P5-02..05 e P5-A..E permanecem válidas nos termos abaixo. A antiga unanimidade de *pessoas* em D-P5-01 foi substituída pela unanimidade das *áreas obrigatórias* em P5-A.

| ID | Resultado aprovado | Invariante |
|---|---|---|
| **P5-F = A** | Substituição de responsável mantém válido o aceite já realizado para a mesma área e PackageVersion; a autoria permanece a do executor original. Substituto assume somente ações futuras. | REASSIGNMENT != INVALIDATE_PRIOR_ACCEPTANCE |
| **P5-G = A** | Aceite P5 não é reversível/alterável pela UI V1. DEC-03 exclui qualquer processo de reversão/retificação do aceite P5 **dentro do Portal V1**, inclusive endpoint ou override; incidentes são tratados fora do fluxo. | NO_P5_ACCEPTANCE_REVERSAL_IN_V1 |
| **P5-H = A** | P6 configura por tipo de pacote as áreas/especialidades obrigatórias em versão governada; P5 congela a configuração aplicável na submissão. Core fornece identidade, effective permissions e atributos de grupo/função conforme contrato a inventariar. | REVIEW_AREA_SET_SNAPSHOTTED_ON_SUBMISSION |
| **P5-I = B** | Reviewer elegível registra rejeição do pacote em nome da área; uma **autoridade operacional formalmente definida**, distinta da simples permission MANAGE, confirma com justificativa e auditoria a rejeição terminal da competência. | AREA_PACKAGE_REJECTION != TERMINAL_COMPETENCE_REJECTION |
| **P5-J = A** | Após confirmação da rejeição terminal, a competência fica rejeitada e todas as projeções/tarefas de revisão ainda acionáveis deixam de sê-lo; histórico, decisões e autoria permanecem consultáveis conforme AuthZ. | REJECTED_COMPETENCE != MONTHLY_CLOSING_COMPLETED |

### Compatibilidade com regras anteriores

- **C2:** competência concluída somente se TODOS os pacotes aplicáveis foram submetidos, TODAS as áreas obrigatórias aceitaram a PackageVersion vigente e NÃO há esclarecimento aberto. Competência rejeitada nunca satisfaz `MONTHLY_CLOSING_COMPLETED`.
- **P5-A / D-P5-01:** quorum de um aceite por área obrigatória, executado por qualquer usuário elegível; não por indivíduo. Dois elegíveis na mesma área não criam dois aceites necessários.
- **P5-B / D-P5-03 / P5-G:** ninguém sobrescreve aceites; nem o autor pode revertê-los pela UI V1. A referência antiga a “autor pode alterar” é **superseded para aceite P5 na V1**. Reatribuição formal não autoriza mutação de decisões anteriores.
- **P5-C / D-P5-04:** ACCESS efetivo + grupo/função corporativa elegível + escopo do recurso + regra da ação; avaliação server-side fail-closed; reviewer assignment nunca se torna novo permission code.
- **D-P5-02 / P5-E:** esclarecer sem alterar conteúdo preserva versão; qualquer alteração de conteúdo cria nova PackageVersion e **exige novos aceites de todas as áreas obrigatórias**; histórico de versões anteriores preservado.
- **D-P5-05 / P5-D / P5-I:** `CHANGES_REQUESTED` não é `REVIEW_REJECTED`; rejeição da área/pacote não encerra competência automaticamente; só confirmação por autoridade operacional a leva ao estado terminal rejeitado.
- **P5-F / P5-H:** reatribuir elegível não altera aceite já registrado, nem o snapshot de áreas obrigatórias da submissão; edição futura do catálogo P6 não altera snapshots abertos.
- **P5-J:** `TaskProjection != TaskEntity`; P5 continua owner do lifecycle; revisão terminal rejeitada remove acionabilidade, sem hard delete nem apagamento de evidências.

### Trilha de auditoria obrigatória

Preservar identidade Core do ator, data/hora, ação, contexto competência/recipient package, versão, área obrigatória, elegibilidade/scope verificados, motivo/justificativa quando exigidos, estado anterior/posterior, autor original do aceite, referência a reatribuições, confirmação formal da rejeição e correlação da projeção/notificação. Histórico é append-only no nível semântico; **schema físico não definido**.

### Pendências reais — sem aprovação presumida

1. **PO_APPROVED DEC-01/02:** a pessoa formalmente designada para coordenar o fechamento da competência confirma rejeição terminal apenas com ACCESS efetivo, vínculo operacional, scope e business rule; se não confirmar, registra motivo e mantém decisão pendente, com possível devolução auditada para esclarecimento/correção. **TO_INVENTORY:** fonte operacional da designação/substituição e binding técnico, sem usar MANAGE como atalho.
2. **PO_APPROVED DEC-03:** retificação/reversão de aceite P5 não existe **nem por UI nem por endpoint na V1**. Incidentes são registrados fora do fluxo do Portal; não criar mecanismo excepcional, override ou alteração de banco para essa capability.
3. **TO_INVENTORY / STOP ON DRIFT:** fonte canônica dos grupos/funções corporativas e sua associação às áreas, contract Core (T05), elegibilidade de múltiplos usuários; não presumir que RBAC do Core tem os atributos necessários.
4. **PO_APPROVED P5-H/DEC-04; PHYSICAL_BINDING_TO_INVENTORY:** P6 versiona áreas obrigatórias por tipo de pacote e MANAGE+administrative scope publica prospectivamente com motivo e auditoria; P5 congela snapshot por submissão. Falta inventariar schema/DTO/OCC, source de função/grupo, vigência e tratamento de configuração ausente, sem criar tabelas/migrations antecipadas.
5. **CONTRACT_PENDING:** outcome de rejeição do pacote versus confirmação terminal da competência, estados técnicos definitivos, falha/conflito no commit, event projection/notifications/Help e matrizes de testes positive+sibling+negative.

**Gates:** `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_CONTRACT_AND_OWNER`; `IMPLEMENTATION_AUTHORIZED = NO`. Nenhum teste de runtime foi executado; `TEST_NOT_RUN`. Nenhum merge/rebase autorizado por este registro.

**Referência vigente:** decisões DEC-01..04/C2/P5 e seus AC estão consolidados nos contratos [37 — P5](./37-p5-submissao-e-revisao-no-portal.md), [23 — Ledger](./23-ledger-rq-ac-testes.md) e no gate documental [33](./33-plano-mestre-fechamento-documental.md). O histórico de decisão permanece no Git; contratos físicos e testes de runtime são inventariados por slice.
