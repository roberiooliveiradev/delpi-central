# CF-CHECKLIST-LIVE-002 — Entregável 3: Mapa de UX, Cards e Vínculos Documentais

- **Status:** `PROPOSED` (Gate 1, aguardando revisão)
- **Base:** HEAD `ef02ef508e`; runtime PROD observado 2026-11-17; inventário LIVE-001 §B.5

---

## 1. Inventário AS-IS (PROVEN)

### 1.1 Componentes e dados

| Componente | Função comprovada | Fonte |
|---|---|---|
| `MonthlyDocumentsPanel.tsx` | Lista de cards da competência: um por item de snapshot (`kind:'required'`) + um por `closing_document link_kind='competence'` (`kind:'additional'`); derivação de situação (attention > accepted > sent > missing); clique navega ao detalhe | `:137-565` |
| `DocumentDetailPanel.tsx` | `isNew` (complementar), `item:{item_key}` (slot exigido), `{document_id}` (documento existente); upload/replace/cancel com OCC `revision`; 25MB; conversa `document_message`; `ItemValidationPanel`; ajustes | `:11-12` (comentário explícito: `new` nunca satisfaz exigência) |
| `MonthlyClosingPage.tsx` | Orquestra painéis; deep-link `?tab=documents` | `:423-436` |
| Admin: `ChecklistVersionPage.tsx`, `ChecklistVersionDocumentPage.tsx` | Gestão por versão (DRAFT lifecycle) | `pages/checklist/*` |
| APIs | `competencesApi.ts`, `documentsApi.ts`, `adminApi.ts` | `plugins/controllership-finance/src/api/` |
| Help | `helpTooltips.ts` | existe, precisa de sync com o gate de implementação |

### 1.2 Contrato do card — campos e fontes

| Campo | Fonte de dados | Endpoint | DTO | Componente | Evidência |
|---|---|---|---|---|---|
| Identidade do item | `competence_checklist_item.snapshot_item_id` / `item_key` | `GET /closing/competences/{p}/documents` | `items[]` | panel → rota `item:{key}` | PROVEN |
| Nome | snapshot `name` | idem | `items[].name` | card title | PROVEN |
| Finalidade | snapshot `purpose` | idem | `items[].purpose` | card/detail | PROVEN (detail; exibição no card verificar Gate 2) |
| Filial/abrangência | `branch_scope`/`applicability` | idem | `items[].branch_scope` | **GAP**: disponível no DTO? verificar exposição ao card | TO_CONFIRM |
| Obrigatoriedade | `required`/`state` | idem | `items[].required` | badge "Obrigatório" | PROVEN |
| Estado da exigência | `state` (EXPECTED/NOT_APPLICABLE/CANCELLED/…) | idem | `items[].state` | derivação de situação | PROVEN |
| Arquivo/versão | `closing_document` + `document_version` vigente | `documents[]` | `latest_version` | "vN", data | PROVEN |
| Validação | `evidence_decision`/decision state | idem | `validation` | selo | PROVEN |
| Ajustes pendentes | `document_adjustment_request` aberto | idem | `pendingRequests` | badge | PROVEN |
| Última atualização | `updated_at`/`created_at` | idem | datas | card | PROVEN |
| Rota de detalhe | `item:{item_key}` ou `{document_id}` | navegação interna | — | clique | PROVEN |

**Gaps reais:** exibição de filial/abrangência no card (verificar se DTO expõe); item `CANCELLED` por retirada não tem hoje apresentação "histórico" diferenciada; empty-state genérico (§3).

### 1.3 Vínculo — cadeia confirmada

```
checklist_template_item(item_id, item_key)
  → competence_checklist_item(snapshot_item_id, item_key,
      source_template_item_id, source_version_id)
    → closing_document(link_kind='competence_item', snapshot_item_id, item_key)
      → document_version → document_file
```

`link_kind` CHECK: `competence` (complementar, `snapshot_item_id NULL`) XOR `competence_item` (slot exigido) — V003:50-53. Upload em `item:{key}` valida FK composta → **o vínculo correto já é garantido pelo contrato**; upload via `new` é complementar por design (não é defeito).

## 2. Fluxo TARGET

```text
Admin salva revisão no catálogo (V1 publicada, série 2)
  → revisão registrada + audit + sync_event (outbox)
  → competências PENDING elegíveis sincronizadas automaticamente
  → Portal exibe status "sincronizando/sincronizado" no painel da competência
  → cards refletem novo conjunto aplicável sem ação manual
  → item retirado → card "retirado" colapsável com histórico
```

## 3. Estados vazios — desenho (10 casos do mandato)

| # | Condição | Mensagem proposta (pt-BR) | Ação |
|---|---|---|---|
| 1 | Competência não aberta | "Fechamento de {MM/AAAA} ainda não foi aberto." | CTA "Abrir fechamento" (se `manage` e regra permitir) — **consultar mês não abre competência** (regra preservada) |
| 2 | Aberta sem checklist vigente | "Este fechamento foi aberto sem checklist documental vigente no período." + data de abertura | — |
| 3 | Checklist vigente vazio | "O checklist vigente não possui exigências cadastradas." | — |
| 4 | Sem exigências aplicáveis à filial/mês | "Nenhuma exigência aplicável a esta filial/período no checklist vigente." | — |
| 5 | Filtros ocultam tudo | "Nenhum documento corresponde aos filtros aplicados." | "Limpar filtros" |
| 6 | Erro de consulta | "Não foi possível carregar os documentos." + retry | retry |
| 7 | Sem permissão | estado forbidden existente | — |
| 8 | Sync em andamento | "Atualizando exigências conforme o checklist vigente…" | progresso |
| 9 | Sync com falha | "A atualização do checklist não foi aplicada por completo." + link admin | retry admin |
| 10 | Checklist alterado após abertura (residual) | coberto por 8/9; se diff pendente: "Há alterações do checklist sendo aplicadas." | — |

Dados já disponíveis no payload para distinguir 1–4 (`opened_without_template`, `template_version` NULL, contagem de itens aplicáveis) — **nenhum endpoint novo é estritamente necessário**; pode bastar um campo `checklist_context` enriquecido na resposta existente (proposta: `checklist_context: {state: opened_without_template|empty_catalog|filtered_out|syncing|sync_failed}`).

## 4. "Adicionar documento" — comportamento confirmado

- Cria **documento complementar** (`link_kind='competence'`, `snapshot_item_id NULL`) — semântica correta por contrato; **nunca** satisfaz exigência (comentário explícito no código).
- **Lacuna demonstrada:** quando não há exigências (casos 2–4), o botão é a única ação visível, sem contexto — usuário pode anexar acreditando estar cumprindo exigência.
- **Melhoria proposta (mínima):** no empty-state, texto auxiliar "Documentos adicionados aqui são complementares e não substituem exigências do checklist." + quando houver exigências, CTA contextual no card de exigência "Anexar arquivo" → navega ao detalhe `item:{key}` (sem criar item novo, sem duplicar exigências).

## 5. Admin da V1 publicada — wireframe textual

```
Administração ▸ Checklist documental
┌────────────────────────────────────────────────────────┐
│ Checklist de fechamento mensal          Série 2 · V1   │
│ PUBLISHED · vigente desde 2026-01 · revisão 7          │
│ [Adicionar documento] [Histórico de revisões]          │
├────────────────────────────────────────────────────────┤
│ ⣿ Relatório P7 Bloco H        obrigatório  todas      │
│ ⣿ FIN-PAGOS-DATA              obrigatório  filial-01  │
│ … (drag para reordenar)              [editar] [retirar]│
├────────────────────────────────────────────────────────┤
│ Impacto: 1 fechamento em andamento será atualizado     │
│ Sync: ◔ aplicando… / ✓ aplicado 12:41 (ver detalhes)   │
└────────────────────────────────────────────────────────┘
Histórico ▸ revisão 7 — "retirada EXT-BNB-CC" por @user
            antes/depois · motivo · [reverter]
```

- Edição direta na V1 publicada via revisões (ADR-005 §5.3); sem DRAFT intermediário; `reason` opcional/obrigatório conforme política.
- Reordenação por drag-and-drop (persiste via `reorder_items`).
- "Impacto" vem do preview `sync-impact` (Entregável 2 §6.2); status do sync vem de `checklist-sync-status`.
- Componentes: `@delpi/plugin-ui` primeiro (cards, tabela editável, badges, modal confirmação host-contained, skeleton/empty/error states, tema claro/escuro, teclado/foco).

## 6. Contratos de API afetados (resumo UX)

| Necessidade UX | Contrato | Novo/Existente |
|---|---|---|
| Cards + vínculo | `GET /closing/competences/{p}/documents` | existente — adicionar `checklist_context` e campos `branch_scope`/`state_reason` |
| Status do sync no painel | `GET .../checklist-sync-status` | novo (E2) |
| Cards de histórico (retiradas) | `items[].state='CANCELLED'` + `state_reason` | existente — FE renderiza seção colapsável |
| Admin edição V1 | revisões ADR-005 (`POST/PATCH` items, reorder, revisions, revert) | novo |
| Preview de impacto | `GET /admin/checklist-catalog/sync-impact/preview` | novo (E2) |
| Upload com vínculo | `POST documents` com `snapshotItemId` | existente — sem alteração |

## 7. Help e acessibilidade

- `helpTooltips.ts`: novos textos para "documento complementar × exigido", "sincronização do checklist", "exigência retirada" — no mesmo gate de implementação (`feature-help-sync`).
- Estados: loading skeleton, error com retry, forbidden, empty diferenciado; claro/escuro; teclado para drag-reorder (fallback botões ↑↓); pt-BR.

## 8. Testes frontend (proposta)

- `MonthlyDocumentsPanel`: card esperado sem arquivo; com arquivo; validado; com ajuste; retirado (seção histórico); complementar; empty-states 1–9; sync badge; claro/escuro; navegação `item:{key}`.
- `DocumentDetailPanel`: upload com `snapshotItemId` correto; complementar não satisfaz exigência.
- Admin V1: add/edit/retire/reorder/revisions/revert, OCC stale, sync-impact preview.

## 9. O que NÃO mudar

- Separação exigido × complementar (`link_kind`) — invariante.
- `derive_closing_state` e o painel de pacotes.
- Deep-link `?tab=documents`, rotas existentes de detalhe.
- "Consultar mês não abre competência".

## 10. DECISION_REQUIRED remanescentes

1. Exibir `branch_scope`/abrangência no card (espaço visual vs informação) — proposta: badge secundária quando ≠ "todas".
2. Seção "retiradas": visível por padrão ou colapsada — proposta: colapsada com contador.
3. `reason` obrigatório em toda revisão de catálogo ou só em retiradas — proposta: obrigatório em RETIRE/REVERT.
