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
- blocker, warning ou mention sem **obrigação governada pelo owner** (individual ou por área) não geram TaskProjection;
- nenhum permission code novo é criado para source/task/action;
- source failure não pode ser convertido em empty;
- due/overdue só existem quando o owner possuir regra formal.

## Administração

Contrato detalhado: [28-administracao.md](./28-administracao.md).

AuthZ:

```text
authenticated
AND effective_permission(controllership-finance.manage)
AND authorized_administrative_resource_scope
AND administrative_business_rule
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

### Orientação e análise

IA assistiva pode explicar, resumir, sugerir, investigar, apontar evidência e comparar padrões; **não cria fonte de verdade de domínio** e não afirma aceite por inferência.

### Decisão PO de 24/10/2026 — CLARA-D01=B: execução delegada com aval humano

**A CLARA poderá executar pelo MCP as mesmas operações que o usuário efetivamente estiver autorizado a executar no Portal**, inclusive **validar, rejeitar e concluir**, mediante **solicitação e confirmação explícitas no chat para cada operação sensível**. A mesma regra se aplica a anexar, corrigir, finalizar, enviar para análise, administrar ou outra capacidade **somente quando tal operação existir no contrato do Portal e estiver autorizada ao ator**. Isso resolve o conflito anterior de proibição absoluta: **a IA não decide nem aprova por conta própria, mas pode ser o canal da ação humana delegada**. Referência: [94 — CLARA, decisão D01=B](./94-clara-especialista-mcp-controladoria-financas.md) e [93 — roadmap checkpoints MCP](./93-roadmap-executivo-central-fechamento-end-to-end-checkpoints.md).

Para operações sensíveis, exigir `PREPARE → descrição de objeto, competência, versão, motivo/efeitos e riscos → aval explícito do usuário → ACT`, com proposta governada vinculada ao ator, versão e prazo. A confirmação não é uma permissão adicional, não é blanket consent e **não é decisão de negócio do modelo**. O backend da `controllership-finance-api` aplica **fresh effective permissions do Core AND resource_scope/ownership AND business_rule**, revalida estado e versão, impõe idempotência/concorrência, audita o ator e canal `mcp/clara` e só declara sucesso após comprovar a pós-condição.

**Exemplos:** se a Joici puder anexar e validar o mesmo documento de forma separada, poderá pedir essas duas ações à CLARA, com confirmações e eventos próprios; anexar não autoaceita. Se o usuário elegível puder rejeitar evidência, a rejeição delegada exige motivo e preserva histórico. Concluir a competência exige **todas** as condições do contrato P5 (inclusive a reconciliação de C2), não apenas a palavra "concluir" no chat. O DRE/Contabilidade permanece consulta/download sem aceite na primeira versão.

**Continua proibido:** a CLARA conceder permissões, fazer bypass de ownership, autenticar-se como administrador genérico, autorizar-se sozinha, validar/rejeitar/concluir sem consentimento explícito e regra válida, executar SQL arbitrário, acessar bancos vizinhos, falsificar estado/cálculo ou sacramentar no Protheus quando a operação não existir como capacidade autorizada do Portal. O **ato de sacramentação no ERP está fora da V1 P3** e não pode ser criado por equivalência genérica.

**Estado de implementação:** `CLARA-D01=B / PO_APPROVED_PRODUCT_DECISION`. Contratos físicos de PREPARE/ACT, MCP, OAuth, delegação, segurança, testes e GO page-by-page continuam pendentes: `IMPLEMENTATION_AUTHORIZED=NO`. Nenhuma operação MCP sensível existe no runtime atual por esta decisão.

## Dados sensíveis

Não expor secrets/tokens em frontend state, prompts comuns ou logs.

**Decisões P5 vigentes:** [37 — contrato canônico de revisão, C2, P5-A..J e DEC-01..04](./37-p5-submissao-e-revisao-no-portal.md). RQ/AC em [23](./23-ledger-rq-ac-testes.md); histórico de gates não é contrato ativo. `IMPLEMENTATION_AUTHORIZED=NO`.
