# CF-UX-054-R3 — Exclusão definitiva de versão de checklist

Estado: implementada (em revisão, sem deploy). Bounded context
`controllership-finance`. A BFF é a autoridade da exclusão. O Portal e
a CLARA chamam o mesmo caso de uso. Nenhuma permission code nova foi
criada; a autorização é sempre a efetiva `controllership-finance.manage`
resolvida pelo Core no backend.

## O que a operação é — e o que não é

`delete_checklist_template_version` remove **definitivamente** uma
versão do checklist mestre e seus itens de configuração, na mesma
transação. É deliberadamente diferente de três operações já existentes:

- **Descartar rascunho** (`DELETE /versions/{n}`, `version_discard`):
  mesma remoção física, mas restrita a `DRAFT`, com OCC só de
  `expected_revision` — continua existindo e sendo o caminho do ciclo
  de vida do rascunho.
- **Inativar** (`version_inactivate`): mudança de estado prospectiva,
  não remoção — continua sendo a política normal de encerramento.
- **Excluir fechamento** (`competence.delete`): cascata sobre dados
  operacionais da competência — a exclusão de versão é o inverso: nunca
  toca competências, snapshots nem documentos.

## Elegibilidade

Elegível em **qualquer estado** (`DRAFT`, `REVIEW`, `PUBLISHED`,
`INACTIVE`) quando **nenhuma referência operacional** existir.
O diagnóstico inventaria o grafo real por `pg_constraint` (não lista
fixa) e classifica:

- `checklist_template_item` → dependência **exclusiva**, removida junto;
- `monthly_competence.template_version_id` (FK RESTRICT) → **bloqueio**,
  com os períodos vinculados listados;
- `competence_checklist_item.source_version_id` (proveniência congelada
  do snapshot, sem FK) → **bloqueio**, com os períodos listados;
- qualquer outra tabela com FK para a versão → **bloqueio** (fail-closed:
  evolução de schema nunca vira cascade silencioso);
- dependência fora do schema → indisponível, nunca exclusão.

A decisão de permitir exclusão de versões `PUBLISHED`/`INACTIVE` sem
vínculos é uma evolução deliberada do invariante «versão publicada é
histórico imutável», autorizada pelo pedido do produto (§11): a
integridade histórica é preservada pela trilha append-only e pela
impossibilidade de excluir versões referenciadas — não pela imutabilidade
da linha de configuração.

## Contrato

- `GET /admin/checklist-templates/{id}/versions/{n}/deletion-eligibility`
  (`diagnose_checklist_template_version_deletion`) → `outcome`
  `eligible|blocked`, `version_id`, `status`, `revision`, `item_count`,
  `reasons[]` (código, contagem, rótulo, períodos) e
  `dependents.exclusive[]`.
- `POST /admin/checklist-templates/{id}/versions/{n}/delete`
  (`delete_checklist_template_version`) com `expected_version_id`,
  `expected_revision`, `expected_item_count`, `reason` (opcional) e
  `idempotency_key` obrigatória.
- Erros: `version_not_found` 404 · `version_delete_blocked` 409 com
  `details.reasons` · `version_delete_conflict` 409 (manifesto
  divergente, replay de chave em outro recurso) ·
  `version_delete_invalid` 422 · `version_delete_unavailable` 503.

Execução: lock do template → replay por `idempotency_key` na trilha →
releitura da versão `FOR UPDATE` → validação de `expected_version_id` →
reinventário das dependências → validação do manifesto
(`revision` + `item_count`) → remoção dos itens → remoção da versão com
`revision` no WHERE → evento `VERSION_DELETED` → read-back. Tudo na
mesma transação; falha em qualquer etapa é rollback integral.

## Auditoria e numeração

`VERSION_DELETED` é append-only em `closing_audit_event` com
`template_id`, `version`, `version_id`, `status`, `revision`, contagem
de itens, motivo, canal e chave — sem copiar conteúdo das linhas
removidas. `list_template_events` passou a `LEFT JOIN` com fallback ao
`detail`, para que a trilha de versões excluídas continue visível na
Administração e na API de eventos.

A numeração nunca retrocede: `create_draft_version` e
`apply_document_requirement` calculam a próxima versão pela alta-marca
`GREATEST(MAX(versão existente), MAX(versão citada na trilha))+1` —
excluir a última versão não reutiliza o número.

## CLARA

Capability `checklist.version_delete` (gate `manage`, `DESTRUCTIVE`,
`prepare→consent→commit`). O PREPARE roda o diagnóstico real: vínculos
impeditivos falham já no PREPARE com `version_delete_blocked` e o
detalhe dos vínculos; o estado selado contém `version_id`, `status`,
`revision` e `item_count`. No ACT, o estado atual é comparado ao selado
(staleness), o executor relê o diagnóstico e invoca
`delete_template_version` com os `expected_*` — mesma BFF, mesmo OCC.
`reason` é opcional. Não é uma ferramenta MCP paralela: usa o fluxo
governado existente.

## Portal

«Excluir versão» aparece na página da versão para estados `REVIEW`,
`PUBLISHED` e `INACTIVE` (`DRAFT` mantém «Descartar», o nome canônico do
ciclo de vida). O diálogo consulta o diagnóstico ao abrir: versão
bloqueada mostra os vínculos com contagens e períodos; versão elegível
mostra o que será removido e exige a digitação de `v{n}` antes de
habilitar «Excluir definitivamente». O envio carrega o manifesto selado
do diagnóstico e chave de idempotência gerada por tentativa. Após a
exclusão a navegação volta à Administração.

## O que ficou de fora

- Não há `checklist.template_delete`: o template é a raiz do agregado,
  referenciada pelo ledger de idempotência
  `document_requirement_operation`, e recadastro pós-exclusão já é
  possível criando nova versão — a numeração alta-marca garante que o
  histórico não é reescrito.
- O descarte de rascunho continua existindo como operação do ciclo de
  vida (sem manifesto de vínculos — rascunho não é referenciável por
  competência).

## Testes

- Rotas: diagnóstico, exclusão, replay, `access`→403, sem token→401,
  validação de manifesto 422, `version_delete_blocked/conflict/
  unavailable` mapeados com `details` (test_admin_checklist_routes).
- PostgreSQL (`test_pg_checklist_version_delete`): exclusão com itens e
  trilha preservada; bloqueio por competência + proveniência de snapshot
  com períodos; conflito de manifesto não remove nada; replay
  idempotente; recadastro nunca reutiliza o número excluído.
- CLARA: capability no catálogo com contrato completo, `destructive`,
  gate `manage` e presenter exibível (test_clara_parity_016).
- Portal: diálogo de exclusão com manifesto e confirmação digitada;
  bloqueio por vínculos sem formulário de confirmação
  (ChecklistVersionPage.test).
