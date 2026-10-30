# Doc 124 — CLARA: política de execução de escrita por risco (SEMANTIC-002)

**Status:** CANONICAL — vigente a partir de CLARA-MCP-SEMANTIC-002;
**revisão A** (`CF-CLARA-ACT-TRANSVERSAL-001`, PO): `checklist.draft_create`
e `checklist.draft_update` promovidas a `DIRECT_ALLOWED` — criar/editar
rascunho não exige confirmação adicional (§3 rev. A).
**Autoridade:** substitui prospectivamente, **somente para o subconjunto
`DIRECT_ALLOWED` abaixo**, a exigência de consentimento universal por
escrita do [Documento 106](./106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md)
§3/Adendo 2 e do [Documento 94](./94-clara-especialista-mcp-controladoria-financas.md)
§10.1. Todas as demais invariantes (D01=B, Core effective permission,
scope, business rules, auditoria, step-up consent V013/V014) permanecem.
**Decisão:** `CLARA-MCP-SEMANTIC-002`, aprovada pelo PO na autorização de
implementação + deploy produtivo — "criar/atualizar executa diretamente
quando autorizado e elegível; excluir e alto impacto mantêm confirmação
reforçada e verificável". Autorização do PO para mudar a **política** não
confere consentimento a nenhuma operação concreta — são conceitos
distintos e continuam assim no runtime.

## 1. Classes de risco

| Classe | Critério (efeito real, não verbo) | Consentimento |
|---|---|---|
| `DIRECT_ALLOWED` | Create/update não destrutivo, efeito controlado e reversível ou corriqueiro, params completos, proteção de repetição física (V019) | Não requer — executa já com AuthZ+OCC+read-back |
| `CONFIRMATION_REQUIRED` | Exclusão, cancelamento destrutivo, decisão de alto impacto, publicação oficial, fechamento definitivo, rejeição terminal, ou equivalente | PREPARE selado → consentimento Portal (step-up V014) → ACT |
| `BLOCKED` | Operação inexistente, não autorizada, fora de escopo, inválida ou sem condições de segurança | N/A — erro tipado, nenhum efeito |

## 2. O que o caminho direto mantém (não é bypass)

```text
allowlist tipada (entity,action)
→ required params + schema
→ Core effective permission (gate revalidado na execução)
→ snapshot de estado fail-closed
→ proposta selada + claim atômico + constraint única de idempotência
→ caso de uso canônico da BFF (mesmo spec["execute"])
→ verify + read-back independente (pós-condição)
→ auditoria mcp/clara (CLARA_DIRECT_ATTEMPT/ACT/REJECTED)
```

`idempotency_key` explícita ou derivada do plano canônico; retry
idêntico devolve `replayed:true` sem reexecutar efeito. Outcome UNKNOWN
é bloqueio honesto, nunca repete. O único elemento suprimido é o desafio
de consentimento — para capabilities que o plano de consentimento (doc
106) enquadraria como "aprovação rotineira sem efeito de alto impacto".

## 3. Matriz de classificação — 48 capabilities

Legenda de gate: `access` = permission de acesso; `manage` = permission
de gerência; `dre` = vínculo de destinatário externo. Coluna *Por quê* =
efeito real que determina a classe.

### 3.1 DIRECT_ALLOWED — 13 (rev. A)

| Capability | Gate | Efeito real | Reversível | Por quê |
|---|---|---|---|---|
| checklist.draft_create | manage | cria versão DRAFT de template | sim (version_discard) | rascunho não publicado — decisão do PO (CF-CLARA-ACT-TRANSVERSAL-001); `manage` revalidado na execução |
| checklist.draft_update | manage | edita itens de versão DRAFT | sim | mesma decisão; OCC por `expected_revision` no caso de uso canônico |
| clarification.open | access | abre pergunta/pendência de esclarecimento | sim (resolve) | comunicação operacional, sem decisão |
| pendency.create | access | registra pendência operacional | sim (cancelamento do próprio registro via fluxo) | registro de trabalho, efeito corriqueiro |
| pendency.claim | access | autoatribuição de pendência | sim (reassign) | afeta apenas a fila do próprio ator; OCC por expected_revision |
| pendency.transition | access | move pendência no workflow | sim | transição rotineira com OCC |
| item.mark_not_applicable | access | marca item como N/A | sim (revert_not_applicable) | decisão declarada mas reversível |
| item.revert_not_applicable | access | desfaz a marcação N/A | sim | reversão explícita |
| item.request_correction | access | solicita correção a item | sim (revisão posterior) | pedido, não decisão |
| document.post_message | access | anexa mensagem ao documento | append-only por natureza | canal de comunicação; idempotência nativa do serviço de documentos |
| document.answer_adjustment | access | responde solicitação de ajuste | sim | resposta operacional |
| received.post_message | dre | mensagem do destinatário ao documento | append-only | mesmo canal, gate dre |
| received.create_adjustment | dre | abre solicitação de ajuste | sim (confirm posterior) | pedido, não confirmação |

### 3.2 CONFIRMATION_REQUIRED — 35 (rev. A)

Razões por bloco (efeito real):

- **Decisões de fechamento / alta materialidade:** `evidence.decide_version`,
  `evidence.decide_item_set`, `review.record_decision`, `item.reverse_decision`,
  `item.review_correction`, `item.create_exceptional`, `item.cancel`,
  `p3.confirm_cutoff`, `p3.upsert_reconciliation`, `p3.revalidate` —
  alteram estado oficial do fechamento ou reprocessam valores.
- **Workflow do pacote / competência (publicação, fechamento, rejeição
  terminal):** `competence.open`, `package.finalize`, `package.reopen`,
  `package.complement`, `package.submit_review`, `package.start_review`,
  `package.assignment_create`, `package.assignment_deactivate`,
  `package.confirm_terminal_rejection` (destrutiva),
  `package.revert_terminal_rejection` — efeito sobre o fluxo oficial ou
  sobre vínculos de outras pessoas.
- **Destrutivas/cancelamento (rota `delete`):** `document.cancel`,
  `item.cancel`, `catalog.entry_deactivate`, `checklist.version_discard`,
  `checklist.version_inactivate`, `package.confirm_terminal_rejection` —
  irreversíveis ou com efeito destrutivo real.
- **Catálogo/template de governança:** `catalog.entry_create`,
  `catalog.entry_update`, `catalog.entry_reactivate`,
  `checklist.version_submit`, `checklist.version_return`,
  `checklist.version_publish`, `checklist.doc_requirement` — alteram
  conteúdo oficial reutilizado por competências futuras (doc 119 §5).
  (`checklist.draft_create`/`draft_update` saíram deste bloco na rev. A:
  versões DRAFT não são conteúdo oficial publicado — só `submit`/
  `publish`/`doc_requirement` tocam o template efetivo.)
- **Operações sobre terceiros/ownership:** `pendency.reassign`,
  `pendency.confirm_classification`, `clarification.resolve` —
  efetuam decisão sobre item de outro ator ou encerram
  esclarecimento (efeito terminal local).
- **Confirmação DRE:** `received.confirm_adjustment` — confirmação
  terminal de solicitação por parte do destinatário.

### 3.3 BLOCKED — definição operacional

Não é uma lista de capabilities: `BLOCKED` é o resultado tipado quando
qualquer pré-condição falha — capability desconhecida
(`not_implemented`), permission revogada (`forbidden`), recurso fora de
escopo, params ausentes (`validation_error`), snapshot indisponível
(`snapshot_unavailable`), proposta stale (`proposal_stale`), key
duplicada com outcome desconhecido (`idempotency_conflict`), consent
ausente para governadas (`consent_required`). Nenhum desses caminhos
aplica efeito.

## 4. Orquestração multi-operação (`execute` `batch`)

`phase` omitida/`direct`/`run` ⇒ modo orquestrado: classificação via
`plan_batch` (mesma máquina — deps explícitas + implícitas por recurso +
fail-closed de snapshot); diretas executam já em ordem; governadas
voltam `pending_confirmation` com `confirmation_url` própria e
bloqueiam dependentes (`dependency_not_executed`); falhas são
parciais e honestas. `phase='prepare'` mantém o caminho consolidado
governado do doc 106 (uma confirmação para todo o plano) — útil quando
o plano é majoritariamente governado. Não há transação global.

## 5. Requisitos para promover uma capability a DIRECT_ALLOWED

1. Efeito não destrutivo, reversível ou corriqueiro.
2. AuthZ efetiva revalidada na execução (gate do Portal equivalente).
3. Snapshot de staleness e pós-condição por read-back implementados.
4. Idempotência física (V019) — implícita para todo caminho direto.
5. Gate do Portal equivalente não exigir confirmação adicional na UI.
6. Registro nesta matriz + testes positive/sibling/negative.

Capabilities que não atenderem todos os itens permanecem governadas —
não inventar mecanismo inseguro para aumentar a contagem.

## 6. Migração do catálogo

| Classe | Ferramenta | Fase padrão | Consentimento |
|---|---|---|---|
| DIRECT_ALLOWED | `execute` | `direct` | nenhum (idempotência física) |
| CONFIRMATION_REQUIRED | `execute`/`delete` | `prepare` | step-up Portal (V014) |

Retrocompatibilidade preservada: `phase='prepare'` continua válido para
capabilities diretas (o caminho governado permanece disponível) e o
consentimento consolidado por lote (`phase='prepare'` em `batch`) segue
o contrato do doc 106 sem alteração.

## 7. Proveniência

| Item | Valor |
|---|---|
| Execução | CLARA-MCP-SEMANTIC-002; rev. A CF-CLARA-ACT-TRANSVERSAL-001 |
| Base | CLARA-MCP-SEMANTIC-001 (doc 119, commit 3f36137dc3) |
| Implementação | `governed_writes.execute_direct`, `semantic_bridge` (fase direct + `_run_operations`), V019 |
| Auditoria | `CLARA_DIRECT_ATTEMPT/ACT/REJECTED` em `closing_audit_event` |
