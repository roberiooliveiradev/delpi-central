# 09 — P2 — Checklist e Documentos

## Job

"Quero saber quais entregáveis são esperados, quais estão satisfeitos, quais dependem de terceiros/validação e o que falta para liberar o pacote."

## Lista e filtros

Filtros:
- todos;
- pendentes;
- aguardando terceiros;
- em validação;
- concluídos;
- grupo;
- origem;
- destinatário;
- requirement;
- busca.

Cada item mostra:
- nome;
- requirement;
- origem;
- destinatário;
- provider/responsável;
- satisfaction;
- blocking;
- estado;
- ação.

## Detalhe

Seções:
- identificação;
- regra;
- origem;
- escopo;
- evidências;
- validação;
- histórico;
- notificações;
- ações.

## Rejeição

Motivo estruturado obrigatório.

Núcleo inicial:
- Competência incorreta
- Documento incompleto
- Arquivo ilegível
- Informação divergente
- Documento incorreto
- Outro

Outro exige comentário.

```text
REJECTED → REPLACEMENT_REQUIRED
```

Versão rejeitada permanece histórica.

## Reversão de rejeição

O mesmo validador que rejeitou pode reverter se nenhuma nova versão foi anexada.

Justificativa obrigatória.

Resultado explícito:
- UNDER_REVIEW; ou
- ACCEPTED.

Nova versão existente bloqueia reversão da rejeição anterior.

A reversão notifica os mesmos destinatários efetivamente notificados na rejeição original.

## Multi-anexo

### PER_ATTACHMENT
Cada arquivo é validado de forma independente. Rejeição parcial não invalida anexos aceitos.

### WHOLE_SET
O conjunto é validado como unidade lógica. É possível substituir somente o arquivo necessário, mas a nova composição inteira volta para validação.

## N/A

Somente CONDITIONAL.

Exige justificativa e auditoria.

Pode ser revertido por ACCESS autorizado para PENDING antes de PACKAGE_SENT.

REQUIRED nunca N/A.

## Item excepcional

ACCESS pode criar item apenas para a competência corrente.

Exige:
- justificativa;
- auditoria;
- scope.

ACCESS pode selecionar apenas opções existentes:
- requirement_type;
- origin_type;
- recipient/responsible;
- satisfaction_rule;
- validator;
- validation_scope;
- notification targets;
- attachment roles catalogados.

Não altera o template mestre.

## Edição

Antes de evidência/validação/evento material:
- ACCESS pode ajustar configuração permitida.

Depois:
- campos estruturais ficam bloqueados;
- descrição/observação operacional continuam editáveis;
- título fica protegido.

## Cancelamento

Pré-execução:
- ACCESS pode cancelar;
- justificativa obrigatória;
- estado CANCELLED;
- sem delete;
- sai da completude ativa.

Após evento material:
- cancelamento simples bloqueado.

CANCELLED é terminal; se voltar a ser necessário, criar novo item.

## Correção estrutural pós-execução

```text
ACCESS REQUEST
→ MANAGE REVIEW
→ APPROVE / REJECT
→ NEW REVISION
```

Aprovação preserva revisão anterior, evidências e validações históricas.

Se a mudança afetar validade:
- evidência suficiente → UNDER_REVIEW;
- evidência insuficiente → PENDING.

MANAGE pode autoaprovar a própria solicitação, mantendo request e approval como eventos separados e auditados.

## Promoção ao mestre

Somente MANAGE:
- cria draft;
- revisa todos os campos;
- define effective_from;
- publica versão futura;
- sem retroatividade.

## ACCESS vs MANAGE

ACCESS opera a competência.

MANAGE administra regras futuras, templates e catálogos.

Nenhuma permission por botão.
