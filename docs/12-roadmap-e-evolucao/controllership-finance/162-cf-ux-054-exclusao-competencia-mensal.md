# 162 — CF-UX-054 — Exclusão de competência mensal

Estado: **implementado no código, sem deploy e sem exclusão produtiva**.

## Escopo e owner

Bounded context `controllership-finance`. A BFF é a autoridade da exclusão. O Portal e a CLARA chamam o mesmo caso de uso. Processo `PROC-0072`. Nenhuma permission code nova foi criada.

## Decisão do PO

A exclusão é administrativa. Exige a permissão efetiva `controllership-finance.manage`. `controllership-finance.access` isoladamente não autoriza. Superusuário humano reconhecido pela Core pode excluir pelo mecanismo canônico de effective permissions. A ação aparece no Portal só para quem tem gestão efetiva. A CLARA publica `competence.delete` na ferramenta `delete`, com gate `manage`, natureza destrutiva e confirmação explícita.

## Contrato HTTP

`GET /closing/competences/{period}/deletion-eligibility`

`DELETE /closing/competences/{period}`

Autorização: `authorized_admin`. Corpo: `expected_competence_id`, `reason`, `idempotency_key`.

Sucesso: `competence_id`, `period`, `deleted=true`, `deleted_at`, `audit_reference`.

Falhas: `competence_not_found` (404), `competence_delete_blocked` (409), `competence_delete_conflict` (409), `competence_delete_unavailable` (503), entrada inválida (422). Sem autenticação: 401. Sem `manage`: 403. RBAC indisponível: 503.

## Elegibilidade

A competência precisa existir, estar `OPEN` e não ter dependência operacional. O diagnóstico consulta as foreign keys reais de `monthly_competence`, além de propostas e lotes CLARA ainda abertos para o período. Contagem indisponível falha fechado.

Bloqueiam, entre outras: itens de checklist, documentos, decisões, correções, pendências, cutoff, conciliações, pacotes, mensagens e solicitações de ajuste. `item_count=0` e `template_version_id` nulo não provam elegibilidade.

A auditoria não bloqueia. A migration **V021** troca a FK de `closing_audit_event` para `ON DELETE SET NULL`. A linha histórica permanece, com período e identificador no `detail`. Não há `CASCADE` e logs não são apagados.

## CLARA

Capability `competence.delete`. Tool semântica `delete`. Não foi criada uma sétima ferramenta MCP. PREPARE não altera a competência. ACT revalida `manage`, o estado selado e as dependências. Confirmação ausente, ator divergente, permissão revogada ou dependência surgida depois do PREPARE rejeitam a execução. O canal conversacional vigente não exige `CLARA_CONVERSATIONAL_SECURITY_ACK`.

## Portal

Na lista «Fechamentos abertos», o botão «Excluir competência» só é montado quando `useViewerCapabilities().manage` é verdadeiro. O diálogo consulta o diagnóstico, exige motivo e a digitação do período, impede envio duplo e, após o sucesso, recarrega a lista. Se a competência excluída for a selecionada, a navegação volta à lista.

## Auditoria e read-back

Evento `COMPETENCE_DELETED` em `closing_audit_event`, com ator, motivo, período, `competence_id` e chave de idempotência. A resposta só é sucesso depois que a transação confirma a ausência da competência. A mesma chave devolve a exclusão já feita e não alcança outro período.

## Competências históricas

Setembro e outubro de 2026 não foram excluídos por esta implementação. A função fica disponível para um gestor confirmar cada exclusão depois do deploy. Competência com checklist publicado continua bloqueada até que as dependências deixem de existir; a exclusão não apaga checklist, documento ou arquivo para conseguir passar.

## Riscos residuais

- Deploy produtivo e a exclusão real de 2026-09/2026-10 não fazem parte deste gate.
- Uma proposta CLARA criada depois da contagem e antes do commit pode não ser vista se não houver FK. A revalidação imediatamente anterior ao DELETE cobre as FKs operacionais.
- O plugin ChatGPT passa a ver a capability depois do deploy e da reconexão; isso ainda não ocorreu.
