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

## Validator

Validator é papel/responsabilidade operacional, não sinônimo de MANAGE.

```text
MANAGE_APPROVAL != EVIDENCE_VALIDATION
```

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
- envio de pacote sem capability;
- usuário sem ACCESS consultando perfil do Portal;
- perfil de outro usuário vazando permissions/capabilities.

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
