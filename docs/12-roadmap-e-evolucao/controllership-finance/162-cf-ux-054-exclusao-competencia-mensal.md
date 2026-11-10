# 162 — CF-UX-054 — Exclusão de competência mensal

Estado: a exclusão administrativa foi implantada em produção no commit `03d194e6c41d68acc19a2c3c97a54f9887ca4231` (V021 aplicada; setembro e outubro de 2026 permanecem abertos). A revisão **CF-UX-054-UX-01** está no código e ainda não foi implantada. Nenhuma competência produtiva foi excluída.

## Escopo e owner

Bounded context `controllership-finance`. A BFF é a autoridade da exclusão. O Portal e a CLARA chamam o mesmo caso de uso. Processo `PROC-0072`. Nenhuma permission code nova foi criada.

## Decisão do PO

A exclusão é administrativa. Exige a permissão efetiva `controllership-finance.manage`. `controllership-finance.access` isoladamente não autoriza. Superusuário humano reconhecido pela Core pode excluir pelo mecanismo canônico de effective permissions. A ação aparece no Portal só para quem tem gestão efetiva. A CLARA publica `competence.delete` na ferramenta `delete`, com gate `manage`, natureza destrutiva e confirmação explícita.

## Contrato HTTP

`GET /closing/competences/{period}/deletion-eligibility`

`DELETE /closing/competences/{period}`

Autorização: `authorized_admin`. Corpo: `expected_competence_id`, `idempotency_key` e `reason` opcional (no máximo 500 caracteres; ausência, vazio e texto curto são aceitos).

Sucesso: `competence_id`, `period`, `deleted=true`, `deleted_at`, `audit_reference`.

Falhas: `competence_not_found` (404), `competence_delete_blocked` (409), `competence_delete_conflict` (409), `competence_delete_unavailable` (503), entrada inválida (422). Sem autenticação: 401. Sem `manage`: 403. RBAC indisponível: 503.

## Elegibilidade

A competência precisa existir, estar `OPEN` e não ter dependência operacional. O diagnóstico consulta as foreign keys reais de `monthly_competence`, além de propostas e lotes CLARA ainda abertos para o período. Contagem indisponível falha fechado.

Bloqueiam, entre outras: itens de checklist, documentos, decisões, correções, pendências, cutoff, conciliações, pacotes, mensagens e solicitações de ajuste. `item_count=0` e `template_version_id` nulo não provam elegibilidade.

A auditoria não bloqueia. A migration **V021** troca a FK de `closing_audit_event` para `ON DELETE SET NULL`. A linha histórica permanece, com período e identificador no `detail`. Não há `CASCADE` e logs não são apagados.

## CLARA

Capability `competence.delete`. Tool semântica `delete`. Não foi criada uma sétima ferramenta MCP. `reason` não é parâmetro obrigatório. PREPARE não altera a competência. ACT revalida `manage`, o estado selado e as dependências e continua exigindo confirmação explícita. Confirmação ausente, ator divergente, permissão revogada ou dependência surgida depois do PREPARE rejeitam a execução. Sem motivo, a apresentação diz que nenhuma justificativa foi informada. O canal conversacional vigente não exige `CLARA_CONVERSATIONAL_SECURITY_ACK`.

## Portal

«Excluir competência» fica no hero da competência aberta, só quando `useViewerCapabilities().manage` é verdadeiro. A lista de fechamentos não tem coluna de ações. O diálogo consulta o diagnóstico, empilha motivo opcional e a digitação obrigatória do período, impede envio duplo e, após o sucesso, invalida a consulta e volta à lista.

## CF-UX-054-UX-01 — Modal e posicionamento de exclusão

O botão saiu da tabela «Fechamentos abertos» e passou para a área de ações do hero, em variante discreta, sem competir com «Atualizar consulta». Quem tem apenas `access`, e o período ainda não aberto, não vê a ação. A autorização efetiva permanece na BFF.

O motivo é opcional no Portal, no `DELETE`, na persistência e na CLARA. A digitação exata de `YYYY-MM` continua obrigatória no Portal, e a confirmação explícita continua obrigatória no ChatGPT. Competência com dependência continua bloqueada, com a contagem visível. O modal usa `CfDialog`, campos oficiais e o rodapé do kit.

Testes executados nesta revisão: página de fechamento mensal (8 cenários de exclusão), rotas HTTP da competência, paridade CLARA e PostgreSQL de exclusão, incluindo motivo ausente, vazio e curto. A conferência visual no Portal publicado fica inconclusiva até o deploy desta revisão: a produção ainda mostra a revisão anterior.

## Auditoria e read-back

Evento `COMPETENCE_DELETED` em `closing_audit_event`, com ator, motivo, período, `competence_id` e chave de idempotência. A resposta só é sucesso depois que a transação confirma a ausência da competência. A mesma chave devolve a exclusão já feita e não alcança outro período.

## Competências históricas

Setembro e outubro de 2026 não foram excluídos por esta implementação. A função fica disponível para um gestor confirmar cada exclusão depois do deploy. Competência com checklist publicado continua bloqueada até que as dependências deixem de existir; a exclusão não apaga checklist, documento ou arquivo para conseguir passar.

## Riscos residuais

- A revisão UX-01 ainda não foi implantada. A exclusão real de 2026-09/2026-10 não foi executada.
- Uma proposta CLARA criada depois da contagem e antes do commit pode não ser vista se não houver FK. A revalidação imediatamente anterior ao DELETE cobre as FKs operacionais.
- A capability já está no BFF implantado em `03d194e6`. O contrato de motivo opcional só passa a valer em produção depois do deploy desta revisão.
