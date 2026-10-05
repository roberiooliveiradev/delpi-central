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

Inclui ACCESS e adiciona administração:
- templates;
- catálogos;
- validators;
- vigências;
- promoção de item excepcional;
- correções estruturais;
- publicação.

Não criar permission por botão, tela, endpoint, CRUD, filial ou unidade.

Para este Portal, filial/unidade é dimensão de dados quando aplicável, não permission code dedicado.

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
- envio de pacote sem capability.

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
