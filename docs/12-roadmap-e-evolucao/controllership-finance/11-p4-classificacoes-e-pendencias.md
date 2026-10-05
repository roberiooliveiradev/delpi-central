# 11 — P4 — Classificações e Pendências

## Classificação / CC

```text
dados/evidências
→ regra determinística + IA explicativa
→ sugestão
→ humano confirma
→ decisão auditada no Portal
```

V1 não grava a correção no ERP.

## IA

Pode:
- explicar;
- sugerir;
- apontar evidência;
- comparar padrões;
- resumir recorrências.

Não pode:
- gravar ERP;
- resolver ambiguidade sozinha;
- alterar owner;
- validar documento.

## Ownership

Pendências pertencem a fila/papel configurado.

Usuário autorizado pode assumir.

Histórico preserva:
- fila;
- responsável anterior;
- responsável atual;
- timestamps.

## Estados

- OPEN
- IN_ANALYSIS
- WAITING_EXTERNAL
- RESOLVED
- DISMISSED

Não criar estados livres.

## Resolução

Responsável atual ou papel autorizado pode resolver.

Justificativa/evidência quando aplicável.

## DISMISSED

Usado quando a pendência é não procedente/dispensada por regra autorizada.

Não usar para esconder blocker ou substituir NOT_APPLICABLE.

Justificativa obrigatória.

## UX

Mostrar:
- estado;
- severidade quando houver regra;
- unidade;
- source;
- fila/responsável;
- pending_since;
- evidência;
- ação.

Sem SLA/overdue.

## Auditoria

- PENDENCY_CREATED
- PENDENCY_CLAIMED
- PENDENCY_REASSIGNED
- PENDENCY_ANALYSIS_STARTED
- PENDENCY_WAITING_EXTERNAL
- PENDENCY_RESOLVED
- PENDENCY_DISMISSED
- CLASSIFICATION_SUGGESTED
- CLASSIFICATION_CONFIRMED
