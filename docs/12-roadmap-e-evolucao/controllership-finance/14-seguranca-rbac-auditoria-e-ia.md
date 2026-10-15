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
AND reviewer_assignment/resource_scope
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

**DECISION_REQUIRED / ainda não inferir:** (1) efeito de reatribuição formal sobre aceite já registrado; (2) procedimento de alteração do próprio aceite compatível com irreversibilidade da UI V1; (3) mapeamento/configuração de áreas obrigatórias e elegibilidade corporativa; (4) momento e autoridade da rejeição terminal da competência quando mais de uma área participa; (5) tratamento das tarefas pendentes dos demais revisores após rejeição terminal. Separar decisões de produto de inventários físicos (DTO, Core eligibility resolver, storage, adapters).

**Gate:** `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_RULES`; `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `IMPLEMENTATION_AUTHORIZED = NO`. Estes textos registram decisões de produto, não demonstram testes, código, contratos físicos, rebase nem execução de smoke.
