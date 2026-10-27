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
