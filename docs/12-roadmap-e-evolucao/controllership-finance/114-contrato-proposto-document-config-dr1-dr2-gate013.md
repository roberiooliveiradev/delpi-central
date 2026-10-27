# 114 — GATE-013: contrato proposto DR-1 e comparativo DR-2 (PROPOSTA — não implementado)

- **Status:** `TARGET`/`PLANNED` — documento de decisão para GPT Arquiteto + Product Owner.
- **Execução:** `CF-PROC0072-DOCUMENT-CATALOG-CONTRACT-GATE-013` (READ-ONLY + DESIGN + CONTRACT + DOCUMENTATION — nenhum runtime alterado).
- **Base:** UX-012 (`8070f2c0eb`) + RW01 (`547ced03c7`); Plano 113 §28.2.
- **Autoridade:** Product Owner — DR-1 aprovado conceitualmente; DR-2 sem decisão (esta proposta devolve recomendação fundamentada).

## 1. Inventário de producers/consumers (PROVEN)

### 1.1 Producers — quem escreve em template/versões/itens

| Producer | Onde | Contrato |
|---|---|---|
| Rotas admin de checklist | `interface/http/routes/admin_checklist_routes.py` | `GET/POST/PUT /admin/checklist-templates*` (MANAGE) |
| Orquestração MFE | `plugins/.../features/closing/documentCatalog.ts` | consome os mesmos endpoints (DRAFT→REVIEW→PUBLISH) |
| Itens excepcionais de competência | `POST /closing/competences/{period}/items` | escreve no SNAPSHOT, não no template |

### 1.2 Consumers — quem lê versões publicadas do template

| Consumer | Arquivo | Efeito |
|---|---|---|
| Abertura de competência | `closing_checklist_repository.open_competence` → `resolve_published_version` | **ÚNICO** consumidor da resolução: copia itens da vencedora para o snapshot `competence_checklist_item`; sem versão → `template_version_id NULL` + snapshot vazio |
| Administração MFE | `ChecklistAdminPage`, `DocumentsAdminPage`, `DocumentConfigFormPage` | leem versões/itens/eventos via BFF |

### 1.3 Consumers — quem lê o snapshot da competência (`competence_checklist_item`)

| Consumer | Arquivo | Uso |
|---|---|---|
| Checklist da competência (P2) | `competences_routes.list_closing_competence_items` | itens esperados no fechamento |
| Anexação documental (P5) | `closing_document_repository` | vínculo item_key ↔ anexo; `locked_item_keys_in` |
| Validações | `closing_validation_repository` | estados do item, `cancel_checklist_item` |
| Pendências (P4) | `closing_pendency_repository` | pendências por item |
| Pacotes/Contabilidade | `closing_package_repository` | `recipient_area` do snapshot → pacote CONTABIL/FISCAL |
| CLARA | `governed_writes`, `operation_presentation` | contexto e escrita governada sobre itens do snapshot |

**Fato estrutural (PROVEN):** nenhum consumer de runtime lê o template diretamente — todos leem o snapshot congelado por competência. A timeline de versões só afeta competências AINDA NÃO abertas.

## 2. DR-1 — contrato proposto: operação transacional de configuração documental

### 2.1 Endpoint

```
PUT  /admin/checklist-templates/{template_id}/documents/{item_key}/requirement
operation_id: upsert_document_requirement
```

- `item_key` na rota (identidade estável, ≤32 `[A-Z0-9-]`).
- Body (`DocumentRequirementConfigRequest`):

```json
{
  "item": {
    "name": "Balancete", "purpose": "...", "origin_kind": "TOTVS",
    "recipient_area": "CONTABIL", "applicability": "REQUIRED",
    "branch_scope": "BOTH", "sheet": "ELETRONICO",
    "totvs_report_ref": null, "requirement_notes": null,
    "validation_scope": "PER_ATTACHMENT", "sort_order": null
  },
  "effective_from": "2026-11",
  "effective_until": "2026-12",
  "base_version": 7
}
```

- `item` presente → upsert (inclusão ou edição) na janela.
- `item` omitido → encerramento puro: o item deixa de ser exigido a partir de `effective_from` (equivale a `until = from − 1` na semântica de remoção).
- `effective_until: null` → exigência indefinida.
- `base_version` (opcional, OCC): último `version` conhecido; se divergir → `409 stale_revision`.

### 2.2 Semântica transacional (uma `conn.transaction()`)

1. `SELECT template_id ... FOR UPDATE` — serialização total por template (substitui a corrida de drafts na orquestração MFE).
2. Carrega versões PUBLISHED + itens; calcula o plano server-side (mesmo algoritmo hoje em `planDocumentSave`, que passa a viver no backend como owner canônico):
   - para cada boundary `b ∈ {from} ∪ {boundaries existentes em [from, until|∞]}`: alvo = `winner@b + item`; se divergir → nova versão `PUBLISHED` com `effective_from = b`;
   - com `until`: versão em `nextPeriod(until)` com `winner@(until+1 pós-inserções) − item`.
3. Idempotência: boundary cujo alvo já é a configuração vigente não gera versão → retry converge, nunca duplica.
4. Cada versão criada diretamente `PUBLISHED` (`published_by=actor, published_at=now()`) com evento `VERSION_PUBLISHED` por versão + evento de resumo `DOCUMENT_CONFIG_APPLIED` (`detail`: item_key, from, until, versões geradas, base_version).
5. Rollback integral: qualquer falha aborta a transação — nenhuma versão parcial persiste (elimina a janela transitória do RW01-A).

### 2.3 Resolução e compatibilidade

- `resolve_published_version` inalterado — a operação só cria versões PUBLISHED regulares.
- Endpoints legados (`.../versions`, publish unitário) permanecem — nenhum consumer quebra; `documentCatalog.ts` migra para uma chamada única quando aprovado.
- Publicação é prospectiva por regra de negócio: `effective_from < competência atual` → `422 retroactive_effective_period` (frontend já valida; backend passa a garantir — hoje `publish_version` aceita passado, gap a fechar na mesma operação).

### 2.4 Erros

| status | code | situação |
|---|---|---|
| 400 | `invalid_period` / `invalid_window` | formato AAAA-MM; until < from |
| 400 | `item_required` | upsert sem `item` completo |
| 403 | `forbidden` | sem `controllership-finance.manage` |
| 404 | `template_not_found` | template inexistente |
| 409 | `stale_revision` | `base_version` divergente |
| 409 | `draft_already_open`? | **decisão:** NÃO bloquear — versões publicadas diretas coexistem com draft alheio (residual: draft clonado antes ficará defasado — mesmo comportamento atual) |
| 422 | `retroactive_effective_period` | from < competência atual |
| 422 | `empty_resulting_checklist` | até DR-2 ser decidido: rejeita alvo que zere itens; após DR-2-A, permitido |

### 2.5 Resposta

```json
{ "data": {
  "item_key": "DOC-A",
  "published_versions": [
    { "version": 8, "effective_from": "2026-11", "item_count": 3 },
    { "version": 9, "effective_from": "2027-01", "item_count": 2 }
  ],
  "skipped_boundaries": ["2026-12"],
  "no_changes": false,
  "audit_event_id": "..." }
}
```

- `no_changes: true` + lista vazia quando já está convergente (resposta honesta de no-op).

### 2.6 Participação transacional — confirmado

Todos os efeitos são `INSERT/UPDATE` no mesmo schema PostgreSQL (`checklist_template_version`, `checklist_template_item`, audit log) dentro de uma conexão — 100% transacional, sem efeito externo. `FOR UPDATE` elimina corrida entre administradores.

### 2.7 Riscos residuais

- Draft aberto alheio fica defasado (já é o caso hoje; mitigação: a página de Administração de versões mostra conteúdo real do rascunho).
- Migração do MFE deve remover a orquestração multi-chamada sem regredir resume (fase posterior — o plano server-side reusa `planDocumentSave` portado, ou mantém o algoritmo TS apenas para preview de "o que será publicado").

## 3. DR-2 — comparativo: representar ausência de exigências

Distinção obrigatória (não equivalentes): **A₀** competência sem template vigente (`template_version_id NULL` — PROVEN, snapshot vazio); **A₁** template com versão publicada contendo 0 itens; **A₂** "última exigência encerrada" — que, sob a alternativa A, materializa-se como A₁.

### 3.1 Alternativas

**A. Versão publicada com zero itens**
- Mudança: remover o guard `item_count == 0` em `publish_version` + relaxar `UpdateDraftRequest.items` para permitir `[]` explícito (ou aceitar publish direto via DR-1).
- `resolve_published_version` devolve a versão vazia → `open_competence` grava `template_version_id` NÃO nulo + snapshot vazio → todos os consumers veem lista vazia — igual ao caso "sem template" a jusante.
- Distinção preservada: `template_version_id` NOT NULL + evento `VERSION_PUBLISHED` com `item_count: 0` auditam "checklist vigente sem exigências" vs `NULL` "sem template".
- **Zero migration, zero schema, compatível com todo consumer de snapshot** (todos leem itens — vazio é vazio); reativar depois = publicar versão com itens (já suportado).

**B. Flag `requirements_disabled` (na versão ou no template)**
- Mudança: nova coluna + semântica em `resolve_published_version`/snapshot + payload de abertura + regra nos consumers para distinguir "desabilitado" de "vazio" + migrations.
- Ganho: semântica explícita no registro; mas A já a preserva via `template_version_id` NOT NULL + auditoria — B só explicita o óbvio com custo de schema.
- Impacto: maior surface (migration, contrato, UI, auditoria) para um estado que A representa sem inventar flag.

### 3.2 Matriz de impacto

| Efeito | A — versão vazia | B — flag |
|---|---|---|
| Abertura/snapshot | `template_version_id` set + 0 itens | requer ler flag |
| P2/P5/validações/pacotes/CLARA | lista vazia = hoje | idem, mas novo campo a propagar |
| Administração | status PUBLISHED normal | novo estado a exibir |
| Auditoria | `VERSION_PUBLISHED item_count=0` | evento novo + campo |
| Migration | nenhuma | obrigatória |
| Retrocompatibilidade | total | compatível mas invasiva |

### 3.3 Recomendação fundamentada → **Alternativa A** (versão publicada com zero itens)

Justificativa: é a menor evolução de contrato possível — um guard de validação; preserva a tríplice distinção (sem template / checklist vigente vazio / exigências ativas) apenas com dados já auditados; nenhum consumer muda; reativação usa o mecanismo existente. Condição: encerramento da última exigência deve passar por `document-config` (DR-1) ou por publish explícito — recomendar rejeitar `publish` de versão vazia por engano via `UpdateDraftRequest` exigindo `allow_empty: true` consciente.

## 4. Matriz RQ/AC (registrada no ledger 23)

| RQ | Requisito | Critério | Status |
|---|---|---|---|
| RQ-ADM-DR1-01 | configuração início+fim é atômica | uma transação; falha em qualquer etapa → nada persiste | TARGET |
| RQ-ADM-DR1-02 | propagação preserva demais exigências | boundaries futuros recebem merge winner+item; remoção em until+1 | TARGET |
| RQ-ADM-DR1-03 | concorrência e idempotência | `FOR UPDATE`; base_version OCC; retry → no_changes | TARGET |
| RQ-ADM-DR1-04 | auditoria e autorização | MANAGE; evento por versão + resumo; retro ativo → 422 | TARGET |
| RQ-ADM-DR2-01 | ausência de exigências sem documento fictício | versão com 0 itens ou flag; distinção sem-template preservada | DECISION_REQUIRED (recomendado A) |
| RQ-ADM-DR2-02 | consumers de snapshot inalterados | abertura, P2/P5, validações, pacotes, CLARA, histórico | TARGET (condição de aceite da decisão) |

## 5. Plano de testes (a executar NA implementação — declarado, não PASS)

- **Atomicidade/rollback:** falha injetada em cada passo → zero versões novas; `SELECT` de versões inalterado.
- **Temporário:** [2026-11, 2026-12] → versões em 11 e 01/2027; itens das demais preservados.
- **Overlaps futuros:** A(11), B(12), C(ate 01/27) → cada janela respeitada; publicações fora de ordem → resolução determinística.
- **Concorrência:** duas sessões simultâneas → uma serializa; `base_version` divergente → 409.
- **Retry:** mesma chamada 2× → segunda `no_changes: true`, nenhuma versão duplicada.
- **Snapshots:** competência aberta antes da publicação permanece intacta.
- **DR-2:** versão com 0 itens publicada → competência abre vazia com `template_version_id` set; encerramento do último item produz versão vazia; reativação posterior funciona.
- **Segurança:** ACCESS-only → 403; sem token → 401; `retroactive_effective_period` → 422.
- **Compatibilidade:** endpoints legados íntegros (suíte PG existente verde).
- Fixtures: template seeded + competências abertas fechadas; resultado esperado por consulta SQL à timeline.

## 6. Decisões que exigem autorização

1. **DR-1 → implementar** `PUT .../documents/{item_key}/requirement` conforme §2 (PO aprovou conceitualmente — falta autorização de implementação).
2. **DR-2 → decidir** alternativa de ausência de exigências — recomendação técnica: **A**.
3. **422 `retroactive_effective_period`** na operação nova (e eventualmente no publish legado) — endurecimento de regra de negócio.
4. **422 vs permitir** `empty_resulting_checklist` — depende da decisão DR-2.

**Próximo gate:** GPT Arquiteto revisa este contrato → PO decide DR-2 → autorização de implementação (DR-1 + decisão DR-2 juntos ou DR-1 com `empty_resulting_checklist` mantido).


## 7. Decisão PO e revisão contratual — 27/10/2026 (GATE-013-R1)

**DECISÃO CONCEITUAL, NÃO GATE DE IMPLEMENTAÇÃO.** O PO aprova conceitualmente DR-2 **alternativa A: versão PUBLISHED com zero itens**, sujeita a confirmação da semântica e compatibilidade dos consumidores antes do runtime. DR-1 permanece aprovado apenas em direção (comando transacional BFF). Não criar endpoint, migration, alterar schema, publicar checklist vazio nem modificar runtime neste gate.

### 7.1 Concorrência transversal: comando novo e endpoints legados
- Inventariar os pontos de escrita nas rotas antigas DRAFT/UPDATE/REVIEW/PUBLISH/INACTIVATE, respectiva ordem de locks e transações. O lock `SELECT ... FOR UPDATE` no template **não serializa** um writer legado que não adquira o mesmo lock.
- Propor protocolo comum de serialização por template para todos os writers concorrentes, inclusive publicação legada, ou estratégia de conflito/rollout que bloqueie interleavings. Testar dois admins, duas rotas, commit concorrente, deadlock/timeout, revisão stale e publicação fora de ordem. Nenhuma alteração do legado está autorizada nesta fase.
- DRAFT/REVIEW pré-existente: definir se bloqueia nova operação, se exige rebase ou se pode coexistir; não presumir segurança por versão imutável.

### 7.2 Idempotência e controle de revisão
- Não confundir igualdade do estado final com identidade de requisição. Propor `Idempotency-Key` persistida e escopada por template, ator/tenant conforme Core, operação, payload hash e janela; retry com mesma chave/payload retorna a resposta original, chave igual com payload diferente gera conflito; definir expiração e armazenamento transacional/limpeza.
- Para gravações baseadas em leitura prévia, definir `expected_revision`/`base_version` obrigatório e o token de revisão que muda em **qualquer** publicação relevante, inclusive por endpoint legado; documentar retorno 409, retry após atualização e regras de no-op. Não assumir que `max(version)` sozinho resolve toda concorrência.
- Especificar eventos de auditoria sem duplicação para retries; request/response e código de conflito devem ser congelados apenas após inventário.

### 7.3 REVIEW — inventário de governança obrigatório, sem escolha antecipada
- Inspecionar owner e regras de DRAFT→REVIEW→PUBLISHED, quem pode submeter/aprovar/publicar, trilha de eventos e consumidores (inclusive documentação de processo, TÉO se AS-IS relevante). Separar transição técnica de aprovação independente.
- Comparar: (A) transação BFF com publicação direta somente se REVIEW não tiver aprovação obrigatória; (B) preparação/revisão governada e confirmação transacional da janela após aprovação. Evidenciar efeitos sobre atomicidade, auditoria, perfis, segregação de funções e UX. Devolver `DECISION_REQUIRED` se houver escolha real de governança; não bypassar REVIEW por conveniência.

### 7.4 Competências abertas e prospectividade
- Uma versão publicada após a abertura de um fechamento **não altera** seu snapshot, mesmo que `effective_from` corresponda ao mês atual. Identificar se o comando deve rejeitar períodos com competência já aberta, permitir com aviso explícito de aplicação somente a futuras aberturas ou restringir a competência posterior — escolha de regra de negócio exige decisão do PO.
- Testar competência atual aberta, futura não aberta, já finalizada, várias filiais quando pertinente, data de abertura versus publicação, períodos sem versão, e reabertura se existente. Exibir no retorno o alcance efetivo e snapshots não afetados, sem prometer aplicação retroativa.
- `retroactive_effective_period` 422 no comando novo é **TARGET proposto**, não regra congelada para endpoints legados; qualquer endurecimento do legado precisa de gate separado e compatibilidade comprovada.

### 7.5 DR-2 alternativa A — condições de aceite
- Confirmar `template_version_id` não nulo com 0 itens versus NULL quando não existe versão aplicável; validar todos os consumidores de snapshot, P2/P5, fechamento, pacotes, auditoria, CLARA e acesso. Testar encerramento do último item, reativação e estados de listagem, com zero documento fictício.
- Definir proteção contra publicação vazia acidental, por intenção explícita (`allow_empty` ou contrato equivalente), sem afirmar que esse campo está implementado. Verificar se a proposta requer relaxar validadores de endpoints legados ou somente o novo comando.

### 7.6 RQ/AC complementares e testes de contrato (todos TARGET/TEST_NOT_RUN)
- RQ-ADM-DR1-05: escritores novos e legados não produzem atualização perdida; conflitos/locks testados em PostgreSQL.
- RQ-ADM-DR1-06: idempotency-key, payload hash, revisão obrigatória e auditoria convergem sob retry/concorrência.
- RQ-ADM-DR1-07: governança REVIEW inventariada e preservada ou alterada somente após decisão explícita.
- RQ-ADM-DR1-08: resultado do comando distingue vigência planejada de efeito sobre snapshots já abertos.
- RQ-ADM-DR2-03: checklist publicado vazio distinguível de ausência de versão, com consumers e snapshots compatíveis.

**Próxima entrega:** inventário READ-ONLY dos writers legados, da governança REVIEW, dos consumidores de competência aberta e das dependências da alternativa A; contrato DR-1 revisado, matriz RQ/AC/testes e proposta de rollout. **GATE DE RUNTIME = BLOQUEADO** até revisão arquitetural e autorização explícita do PO.

---

## 8. Consolidação GATE-014 (28/10/2026) — especificação apta à decisão final

**Status:** `TARGET` — proposta revisada; nenhum runtime alterado.

### 8.1 Inventário de writers do checklist (CP1 — PROVEN)

| Operação | Endpoint | Tx | Concorrência | Auditoria |
|---|---|---|---|---|
| Criar rascunho | `POST /admin/checklist-templates/{id}/versions` | sim | índice único parcial `ck_template_version_one_open` (DRAFT **ou** REVIEW) | `DRAFT_CREATED` |
| Editar itens do draft | `PUT .../versions/{v}` | sim (delete+insert) | OCC `revision` → `stale_revision` | `DRAFT_UPDATED` |
| Submeter revisão | `POST .../submit-review` | sim | status DRAFT-only | `VERSION_SUBMITTED_FOR_REVIEW` |
| Devolver a rascunho | `POST .../return-to-draft` | sim | status REVIEW-only + `reason` obrigatório | `VERSION_RETURNED_TO_DRAFT` |
| Publicar | `POST .../publish` | sim | status REVIEW-only; ≥1 item | `VERSION_PUBLISHED` |
| Inativar | `POST .../inactivate` | sim | status PUBLISHED-only | `VERSION_INACTIVATED` |
| Item excepcional | `POST /closing/competences/{p}/items` | sim | snapshot da competência (contrato distinto) | `ITEM_CREATED` |
| Abertura | `POST /closing/competences` | sim | `ON CONFLICT DO NOTHING` | `COMPETENCE_OPENED` |

**Resposta à questão central:** `SELECT … FOR UPDATE` no template NÃO basta sozinho — os writers legados não adquirem o mesmo lock hoje. **Estratégia:** adquirir o lock de linha do template (ordem fixa: sempre `checklist_template` → tabelas de versão/itens) em TODOS os writers que tocam o estado publicado (`publish_version`, `inactivate_version`) e na operação nova; writers de draft/review podem manter o índice `one_open` + OCC — a corrida residual "draft publicado entre fetch e lock" é serializada pelo lock da publicação. Sem alteração de contrato — mudança interna de repositório.

### 8.2 Parecer sobre REVIEW (CP2 — PROVEN)

- **Semântica:** estágio de conferência do lifecycle P6 aprovado (V010: `DRAFT → REVIEW → PUBLISHED → INACTIVE`); "salvar ≠ publicar" (doc 13 §Template mestre).
- **Aprovação independente?** NÃO — o mesmo `authorized_admin` (MANAGE) cria, submete, devolve e publica; não há capability nem ator distinto (D-FINAL-02 não exige mínimo de revisores). REVIEW é janela de conferência auditada, não segregação de funções.
- **Consumidores:** nenhum consumer de runtime depende de REVIEW (só a página admin legacy lista o estado).
- **Recomendação — Alternativa A com paridade de auditoria:** a operação `document-config` publica em transação única registrando, por versão gerada, a sequência de eventos `DRAFT_CREATED` → `VERSION_SUBMITTED_FOR_REVIEW` → `VERSION_PUBLISHED` + resumo `DOCUMENT_CONFIG_APPLIED`. A linha pode transitar DRAFT→REVIEW→PUBLISHED **dentro** da mesma transação — a trilha de auditoria fica idêntica ao fluxo manual e o estágio continua registrado, sem janela intermediária persistida. Alternativa B (preparar→revisar→confirmar em duas chamadas) só se justifica se o PO quiser janela de conferência humana para configurações de documento — o fluxo UX-012 nunca a teve (já publica em sequência). Sem `DECISION_REQUIRED` adicional — a escolha é consistente com a autoridade vigente; fica registrada para confirmação do PO.

### 8.3 Idempotência e concorrência (CP3)

**Idempotency-Key (padrão canônico V004/upload — `document_version.idempotency_key` + `request_hash`):**

- Header `Idempotency-Key` obrigatório (1–128 chars).
- Escopo: `UNIQUE (template_id, idempotency_key)` em tabela nova `document_requirement_operation` — registra `request_hash`, `actor`, `result JSONB`, `created_at` (auditoria-grade, sem expiração).
- `request_hash` = SHA-256 do JSON canônico de `{item_key, item, effective_from, effective_until}` — `base_version` fica fora (é OCC, não identidade — mesmo precedente de `revision` no upload).
- Mesma chave + mesmo hash → retorna o resultado armazenado (`replayed: true`, sem duplicar versão nem auditoria).
- Mesma chave + hash divergente → `409 idempotency_conflict`.
- Igualdade de conteúdo dos boundaries permanece apenas como otimização de skip, NUNCA como prova de identidade da operação.

**OCC / concorrência:**

- `base_version` = `MAX(version)` visto pelo cliente; divergente → `409 stale_revision` (cobre toda mudança de timeline, inclusive de endpoints legados, porque qualquer publicação cria versão nova).
- Lock: `SELECT template_id … FOR UPDATE` no início da transação; ordem fixa de aquisição (template → versões → itens) → sem ciclo de deadlock.
- `lock_timeout` ~5s → `409 busy` honesto; READ COMMITTED basta (serialização pelo lock).
- Writers legados que publicam/inativam adquirem o mesmo lock (compatibilidade interna, §8.1).
- Edição simultânea de documentos diferentes ou competências diferentes → serializados pelo mesmo lock do template (menor unidade de serialização, correto: qualquer versão publicada recompõe o conjunto inteiro).

### 8.4 Competências já abertas (CP4 — política recomendada)

Fatos PROVEN: `monthly_competence.status` admite apenas `OPEN`; snapshots são congelados; `open_competence` resolve a versão vigente UMA vez na abertura. Logo, publicar `effective_from ≤` competência já aberta cria divergência catálogo/snapshot silenciosa (o catálogo diria "exigido" num mês cujo checklist não o contém).

**Recomendação: rejeitar** — `422 window_covers_open_competence` quando a janela `[effective_from, effective_until]` intersecta o período de qualquer competência já aberta. Corretivo legítimo para competência aberta permanece o **item excepcional** (`POST /closing/competences/{p}/items`) — contrato distinto, preservado. Alternativa avaliada: permitir com warning explícito — registrada, mas a rejeição elimina a divergência em vez de apenas declará-la. Confirmação do PO registrada como pendência formal.

### 8.5 DR-2 — compatibilidade da versão publicada vazia (PROVEN por inspeção)

- `publish_version`: único guard `item_count == 0` — liberação condicionada a intenção explícita: `PublishVersionRequest.allow_empty: bool = false` → sem `allow_empty` continua 422/400 (proteção contra erro operacional, sem inventar documento).
- `UpdateDraftRequest.items`: `min_length=1` → aceitar `[]` somente com `allow_empty: true` no mesmo request.
- `resolve_published_version`: inalterado — devolve a versão vazia.
- `open_competence`: grava `template_version_id` NOT NULL + snapshot com 0 itens → válido; distinção sem-template (NULL) vs checklist-vazio preservada e auditável (`item_count: 0` no evento).
- Consumers de snapshot (P2, P5, validações, pendências, pacotes, CLARA, histórico, ajuda): todos leem listas — vazio ≡ hoje (PROVEN por `V015`: a abertura sem template já produz snapshot vazio idêntico).
- Reativação: publicar versão com itens — mecanismo existente.
- `derive_closing_state`/conclusão: vacuidade de checklist nunca conclui por vacuidade (pacotes/conciliações regem a conclusão — comentário normativo de V015).

### 8.6 Contrato DR-1 consolidado

```
PUT /admin/checklist-templates/{template_id}/documents/{item_key}/requirement
operation_id: upsert_document_requirement
Headers: Idempotency-Key (obrigatório)
Body: {
  item?: ChecklistItemInput,            # presente = upsert; ausente = encerramento
  effective_from: "YYYY-MM",            # > última competência aberta
  effective_until?: "YYYY-MM"|null,
  base_version?: int
}
Response 200: { item_key, published_versions[], skipped_boundaries[],
                no_changes, replayed, audit_event_ids[] }
Erros: 400 invalid_period|invalid_window|item_required|allow_empty_required
       401 unauthorized · 403 forbidden (sem MANAGE)
       404 template_not_found
       409 idempotency_conflict|stale_revision|busy
       422 retroactive_effective_period|window_covers_open_competence|
           empty_resulting_checklist (absent allow_empty)
```

Transação: `FOR UPDATE` template → verifica idempotência → valida janela/abertura → plano de boundaries → insere versões com trilha DRAFT→REVIEW→PUBLISHED auditada → grava operação idempotente → commit. Rollback integral por construção. Migration prevista (V017, **não executada**): tabela `document_requirement_operation` + `allow_empty` no publish legado (decisão DR-2).

### 8.7 Rollout

1. Migration V017 (tabela de idempotência) + guard `allow_empty`.
2. Endpoint + repository (`FOR UPDATE` também nos writers legados de publicação/inativação).
3. MFE `documentCatalog.ts` passa a chamar a operação única (remove orquestração multi-chamada; mantém derivação de vigências).
4. Endpoints legados permanecem (edição manual de template).

Rollback: endpoint novo é aditivo — desativar rota/devolver orquestração MFE; dados já publicados são versões regulares (compatíveis).

### 8.8 Decisões pendentes (fechamento para o PO)

| # | Decisão | Recomendação |
|---|---|---|
| D1 | Autorizar implementação do endpoint transacional | Sim (spec pronta) |
| D2 | DR-2 alternativa A com `allow_empty` explícito | A (PO já aprovou conceitualmente) |
| D3 | Política `window_covers_open_competence` (rejeitar vs warning) | Rejeitar (422) |
| D4 | Publicação direta com trilha REVIEW auditada (A) vs preparação/confirm em duas chamadas (B) | A — REVIEW não é aprovação independente |
| D5 | `base_version` obrigatório vs opcional | Opcional (compat com clientes simples); MFE envia |


## 9. Deliberação PO pós-GATE-014 — contrato condicionado e gate de implementação (27/10/2026)

**DECISÃO FORMAL DE PRODUTO, NÃO EVIDÊNCIA DE RUNTIME.** PO delibera:
- **D1:** AUTORIZAR a implementação **somente após** incorporar os ajustes contratuais abaixo, verificar as autoridades e ultrapassar gates transversais e de deploy aplicáveis. Esta decisão não permite começar runtime sem o fechamento dos gates.
- **D2 / DR-2:** preservar alternativa **A** — versão PUBLISHED com zero itens, acionada com intenção explícita; nenhuma versão vazia ou migration foi implementada nesta etapa.
- **D3:** **REJEITAR** com HTTP 422 `window_covers_open_competence` qualquer janela de alteração de exigência que intersecte competência já aberta; correção excepcional em competência aberta permanece em contrato próprio. Verificar colisão transacional com abertura simultânea.
- **D4:** **REVIEW AUDITADO DENTRO DA TRANSAÇÃO**, mantendo eventos DRAFT_CREATED → VERSION_SUBMITTED_FOR_REVIEW → VERSION_PUBLISHED por versão e resumo DOCUMENT_CONFIG_APPLIED; sem janela humana independente, conforme inventário GATE-014. Não suprimir provenance de eventos.
- **D5:** `base_version` **OBRIGATÓRIO**, não opcional, para mutações documentais. Validar no backend e devolver 409 stale_revision após comparação com token de versão atual. `Idempotency-Key` continua independente, obrigatória e distinta do OCC.

### 9.1 Ajustes de contrato obrigatórios antes de runtime
1. Substituir na proposta §8.6 `base_version?: int` por `base_version: int` requerido; proibir omissão e definir 400/422 de validação para campo ausente, respeitando convenção vigente. A política de replay idempotente deve preceder a avaliação de revisão stale para retries da **mesma** operação concluída, evitando falha falsa após sucesso; chave igual + hash diferente retorna 409.
2. Definir `allow_empty` explícito e consistente em novo comando e operações legadas aplicáveis (normalização da intenção, default false, erro sem intenção). Separar versão vazia de template ausente pelo `template_version_id` e auditoria. Confirmar invariantes dos consumers e a interação entre publicar zero itens e snapshots.
3. Compartilhar protocolo de lock (template antes de versão/itens) entre comando novo, publicação/inativação legadas **e abertura da competência**, com ordem e isolamento definidos; a regra D3 deve ser checada sob o mesmo controle transacional capaz de impedir corrida com uma abertura simultânea. Se a abertura não puder adquirir o mesmo lock sem impacto indevido, emitir `EXECUTION_DRIFT/DECISION_REQUIRED` antes de implementar, com alternativas.
4. Integrar `Idempotency-Key` em persistência transacional e escopo comprovado com hash canônico do payload, incluindo a semântica de `base_version` no replay. Definir audit event idempotente, tenant/actor/scope e estratégia para falha de commit e retry.
5. Determinar a semântica de `effective_from` para competência atual ainda não aberta e o resultado retornado para competência já aberta/erro 422; preservar prospectividade, imutabilidade do snapshot, autorização manage fail-closed e compatibilidade.
6. Especificar rollout/rollback seguro para migração aditiva, endpoint, writers legados, abertura e MFE, incluindo compatibilidade de versões e plano de testes PostgreSQL com concorrência real.

### 9.2 Próximo gate de execução — IMPLEMENTATION-GATE-015 (condicional)
**Primeira entrega:** inventário HEAD/status e diff contratual de §8.6-§8.8 alinhado a D1-D5, matriz de consumers/writers e plano de migrations/testes. **GATE TRANSVERSAL EXPLÍCITO** antes de editar runtime ou schema. Depois, implementar em etapas pequenas e verificáveis: (a) backend/domain/application/ports/adapters, locks inclusive abertura e testes concorrentes; (b) endpoint + autorização fail-closed + idempotência, versão vazia explicitamente intencional e migração governada; (c) MFE troca orquestração por chamada única mantendo UX-012 e legacy; (d) regressão P2/P5/documentos/histórico e Help; (e) deploy local, verificação de resultado, produção só após gate separado, docs/evidência/CLARA. Nenhuma etapa de runtime executada nesta deliberação.

### 9.3 RQ/AC adicionais (TARGET / TEST_NOT_RUN)
- **RQ-ADM-DR1-09:** `base_version` exigido e 409 no stale; replay da mesma operação concluída é determinístico sem duplicar.
- **RQ-ADM-DR1-10:** publicação e abertura concorrentes não escapam de D3; 422 quando a competência já abriu, ou snapshot novo coerente quando abertura vem depois da publicação.
- **RQ-ADM-DR2-04:** `allow_empty` é intencional e auditado; último item pode terminar sem documento-sentinela, sem modificar snapshots anteriores.
- **RQ-ADM-DR1-11:** etapa REVIEW audita transições na mesma transação, rollback elimina também eventos de auditoria em falha.

**Classificação:** D1-D5 = PRODUCT_APPROVED com condições; contrato atualizado = TARGET; implementation/tests/deploy = NOT_STARTED/TEST_NOT_RUN. Sem autorização genérica para criar mudanças de runtime sem gates.

## 10. Registro de implementação — IMPLEMENTATION-GATE-015 (PROVEN, 28/10/2026)

Implementação do contrato consolidado (§8.6) sob decisões PO D1–D5 (§9). Menor diff possível: nenhuma persistência paralela de catálogo foi criada — a operação reusa o modelo versionado existente.

### 10.1 Contrato implementado (PROVEN em runtime local)

`PUT /admin/checklist-templates/{template_id}/documents/{item_key}/requirement` (`operationId: upsert_document_requirement`, MANAGE-only, fail-closed):
- Request: `item` (DraftItemInput) **ou** ausente = encerramento; `effective_from` `YYYY-MM`; `effective_until` opcional; `base_version` obrigatório (`ge=0` — 0 designa timeline vazia, coerente com `COALESCE(MAX(version),0)` do OCC); `allow_empty` (default `false`); header `Idempotency-Key` 1–128.
- Resposta 200: `item_key`, `published_versions[]` (`version`, `version_id`, `effective_from_period`, `item_count`), `no_changes`, `replayed`, `audit_event_ids`.
- Erros comprovados em smoke autenticado local (gateway + Keycloak dev): `401` sem token; `403` com `access` sem `manage`; `409 idempotency_conflict`; `409 stale_revision`; `409 catalog_draft_conflict` (rascunho/revisão aberto divergente); `422 empty_resulting_checklist` sem `allow_empty`; `422 window_covers_open_competence` (provado em suíte PG).

### 10.2 Persistência — migration V017 (PROVEN)

`V017__document_requirement_operations.sql` cria `document_requirement_operation` (template_id + idempotency_key UNIQUE, request_hash SHA-256, actor, result JSONB, created_at) — gravada na **mesma transação** das versões e eventos. Aplicada na subida local: `migration_applied name=V017__document_requirement_operations.sql`.

### 10.3 Semântica transacional (PROVEN em testes PG + smoke)

- Lock `FOR UPDATE` na linha do template (ordem canônica template → versão → itens); mesmo lock adquirido por `publish_version`, `inactivate_version`, `create_draft_version` e `open_competence` (este trava todos os templates ordenados antes de resolver a versão — publicação e abertura serializam).
- Replay idempotente avaliado **antes** do OCC: mesma chave + mesmo hash retorna o resultado persistido (`replayed: true`) sem nova versão/evento; chave igual + hash divergente → `409 idempotency_conflict`.
- `base_version` ≠ `MAX(version)` → `409 stale_revision`; nenhuma configuração alheia é sobrescrita.
- Trilha REVIEW auditada dentro da transação por versão: `DRAFT_CREATED → DRAFT_UPDATED → VERSION_SUBMITTED_FOR_REVIEW → VERSION_PUBLISHED` + `DOCUMENT_CONFIG_APPLIED` (resumo com item_key, operação, janela, allow_empty, idempotency_key, versões publicadas). Verificado no banco: sem duplicatas após replay.
- DR-2 A: versão PUBLISHED com `item_count: 0` somente com `allow_empty: true`; `template_version_id` preenchido + snapshot de zero itens permanece distinto de `NULL` (sem template aplicável).
- Falha em qualquer etapa faz rollback integral de versões, auditoria e registro idempotente (Teste A da suíte PG).

### 10.4 Frontend (PROVEN)

O MFE não orquestra mais versões: `saveDocumentConfig`/`endDocumentRequirement` emitem **uma** chamada `saveDocumentRequirement` com `base_version` (`MAX(version)` visto), `Idempotency-Key` por intenção (nova chave quando `allow_empty` muda o payload) e confirmação explícita para checklist vazio. `stale_revision` oferece recarregar estado; `window_covers_open_competence`, `empty_resulting_checklist`, `busy`, `catalog_draft_conflict` têm copy própria. Interfaces UX-012 preservadas (páginas, filtros na URL, histórico, breadcrumb, light/dark).

### 10.5 Evidência executada

- Backend: `689 passed` (suíte completa pytest c/ PostgreSQL efêmero isolado); planner unit 15, PG document-requirement 13, rotas 30.
- Frontend: `337 passed` (vitest); `tsc --noEmit` e `eslint` limpos nos arquivos do escopo; build MFE ok.
- Smoke local autenticado (Keycloak dev, usuários `cf-e2e-peer` MANAGE / `cf-e2e-access` ACCESS): ciclo completo cadastro → replay → conflitos → encerramento do último item com checklist vazio publicado; auditoria conferida na tabela.
- Pendente registrado: `DocumentDetailPanel` avatar test é flake pré-existente fora do escopo (intermitente em `main`, sem alteração neste gate).

### 10.6 Limitações remanescentes

- `effective_from` em competência já aberta → 422 (D3); correção excepcional segue contrato próprio por competência.
- Deploy produtivo **não realizado** — requer gate separado (CP10); V017 é aditiva e retrocompatível.
- Writers legados mantidos compatíveis; novos comandos documentais devem preferir este endpoint.

**Classificação:** contrato §8.6 implementado = PROVEN; D1–D5 aplicadas = PROVEN; produção = PENDING gate próprio.
