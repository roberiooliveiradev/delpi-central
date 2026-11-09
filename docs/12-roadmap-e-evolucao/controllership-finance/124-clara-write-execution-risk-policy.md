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


## 8. Decisão de produto posterior — confirmação conversacional padrão TÉO (09/11/2026)

**Status: PO_APPROVED_UX / SECURITY_GATE_PENDING / `IMPLEMENTED_NOT_CUTOVER` / CUTOVER_BLOCKED.** O PO escolheu substituir a navegação obrigatória para `/closing/clara-consent` pelo fluxo de confirmação na conversa, para todas as capabilities, inclusive as 35 `CONFIRMATION_REQUIRED`.

**Padrão TÉO inspecionado:** `transformometro-api/tm_app/interface/mcp/server.py` + `tool_bridge_v3.py` aceitam proposta pendente selada e `proposal_id + confirmation=true` somente na confirmação; operações diretas seguem política por risco. É referência de **UX/API de chamada**, não evidência de equivalência ao consentimento Portal V014. Texto no chat e flag `confirmation=true` são modeláveis pelo cliente; a prova de aprovação humana autenticada do plano selado não foi demonstrada.

**Implementação independente (código):** contrato `proposal_pending_confirmation` + `confirmation` no MCP CLARA; schema `get_context` alinhado ao canal; lote com modo `MCP_CONFIRMATION` (migration V020); canal `CLARA_CONSENT_CHANNEL` default `portal`; ACT conversacional só arma com `CLARA_CONVERSATIONAL_SECURITY_ACK=R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED`. Sem ack, `confirmation=true` **não** substitui V014. Detalhe: doc 150 §20.9–§20.10.

**Gate obrigatório R-CLARA-01:** Segurança/Plataforma e Controladoria devem registrar a decisão formal do §20.10 (ACCEPT_TEO_RESIDUAL / REQUIRE_HOST_ATTESTED / KEEP_V014 + ACCEPT_OPERATIONAL_RISK). HOST_ATTESTED em produção permanece `NOT_CONFIGURED`. Até assinatura + cutover verificado, **PREPARE → Portal V014 → ACT continua vigente**, tal como §§1–7. **Cutover por env sem essa assinatura é proibido.**

**Invariantes para a evolução:** proposta única vinculada a ator, recurso, versão, plano e TTL; identidade + effective permissions via Core; resource_scope/ownership + business_rule fail-closed; atomic claim, OCC, idempotência física, audit trail, read-back; sem edição de migrations aplicadas; sem execução para `confirmation=true` desacompanhado de proposal válida. Inventário/planos em doc 150 §20.


## 9. Diretriz PO sobre fronteira de responsabilidade (09/11/2026)

PO determinou que CLARA não duplique **RBAC nem effective permissions**, cuja authority é a Core, e siga a experiência conversacional do TÉO, sem página de consentimento externa no TARGET. A BFF da CLARA deve continuar impondo `capability AND resource_scope/ownership AND business_rule`, verificando transições, integridade, idempotência e auditoria. **Permissão Core e consentimento humano vinculado ao plano são provas diferentes**: esta diretriz não equivale à autorização formal de substituir V014 para as 35 operações sensíveis. Aguardar decisão de Segurança/Plataforma + Controladoria documentada em doc 150 §20.10; não armar ack como substituto. Critérios de cutover e execução única em [doc 161](./161-cf-ux-053-decisao-po-fronteira-core-e-execucao-conversacional-2026-11-09.md). Até gate, política produtiva §§1–8 mantém Portal V014 obrigatório.


## 10. Decisão superveniente do PO e responsável pela Controladoria — CF-UX-053 (09/11/2026)

**OWNER_DECISION_PROVEN:** o PO e responsável pela área declarou expressamente que **autoriza modificar CLARA, Portal e a obrigatoriedade do fluxo V014**, assumindo a decisão operacional de passar ao padrão conversacional TÉO, sem página externa no TARGET. Registro canônico e texto de aceitação em [doc 150 §20.16](./150-plano-unico-correcao-integral-portal-ux-funcional-2026-11-02.md). **CONTROLLADORIA_DECISION = ACCEPT_OPERATIONAL_RISK** conforme declaração do responsável pela área; esta escolha não deve ser reapresentada ao mesmo owner.

**Distinção de autoridade:** a autodeclaração do PO como responsável pela área não constitui, por si só, assinatura independente do guardião Segurança/Plataforma. Os textos de §§1–9 descrevem a política e o runtime V014 anterior; não utilizar esses trechos históricos para negar que o **responsável operacional já autorizou a evolução**. Não declarar `SECURITY_PLATFORM_DECISION=ACCEPT_TEO_RESIDUAL` em nome de um guardião diferente sem evidência específica.

**TARGET autorizado pelo responsável operacional:** PREPARE → proposta selada apresentada no ChatGPT → confirmação explícita e específica → ACT autenticado; Core effective permissions; BFF resource_scope/ownership/business_rule e salvaguardas transacionais. No canal conversacional, o argumento `confirmation=true` não substitui AuthZ nem as condições de validade da proposta. **CUTOVER_NOT_DONE** em produção até alteração técnica, gate corporativo efetivamente aplicável, deploy e smoke ChatGPT; nenhuma configuração alterada por este registro.
