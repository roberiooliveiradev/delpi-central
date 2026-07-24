# Especificação funcional e técnica — Lançamento de Notas Fiscais

> **Plugin:** `lancamento-notas-fiscais`  
> **Status:** contrato alinhado ao MVP implementado (MFE + api-delpi)  
> **Última revisão:** 2026-07-24  
> **Base:** Etapas 0 e 1A (homologação TOTVS) — este documento **não** repete o relatório de descoberta.  
> **Operação / deploy:** [PLAYBOOK.md](./PLAYBOOK.md) · [README.md](./README.md) · [API](../../../api-delpi/docs/api/lancamento-notas-fiscais.md)

---

## 1. Escopo e arquitetura

| Camada | Decisão |
|--------|---------|
| Microfrontend | `plugins/lancamento-notas-fiscais` |
| Backend | rotas novas na `api-delpi` (sem `*-api` própria) |
| Persistência operacional | `postgres-plugins` (migrations do pacote `api-delpi`) |
| ERP (somente leitura) | Protheus — matching em `SF1010`; confirmação opcional em `SD1010`; fornecedores em `SA2010` |

**Filiais:**

| Código | Unidade |
|--------|---------|
| `01` | Santa Catarina |
| `02` | Espírito Santo |

**Fora do escopo da primeira versão:** prioridade manual na fila; documentos alfanuméricos novos; agendamento concreto do reconciliador (só contrato de comportamento); registro de manifesto/RBAC no Core (feito em etapa posterior); **permissões por filial** (`.view.filial-01|02`).

**Escopo de consulta (v1):** quem tem `view` consulta solicitações das filiais `01` e `02` (sem RBAC granular por filial).

**MVP (atual):** migrations V001–V003, endpoints HTTP, MFE (fila/form/detalhe), conciliação sob demanda (`/reconciliation/refresh` + `/run`).  
**Backlog:** job agendado de conciliação; RBAC `.view.filial-*`; resumo KPI da fila.

---

## 2. Chave fiscal e normalizações

### 2.1 Chave de conciliação / duplicidade

```text
filial
+ fornecedor (A2_COD)
+ loja (A2_LOJA)
+ document_match_key
+ série normalizada
```

Matching principal: **`SF1010`** com `D_E_L_E_T_ = ''`.  
Confirmação opcional: existência de itens ativos em **`SD1010`** (`D_E_L_E_T_ = ''`) na mesma chave.  
**Valor da nota não participa da chave.**

### 2.2 Documento (número da nota)

| Regra | Detalhe |
|-------|---------|
| Aceitos | somente dígitos `0-9` |
| Comprimento | 1 a 9 dígitos |
| ≤ 9 dígitos | zeros à esquerda até **9** para **exibição / armazenamento de apresentação** e chave de match |
| 9 dígitos | preservados integralmente |
| Truncamento | **proibido** |
| Alfanumérico | legado no Protheus; **não** aceito em novos cadastros v1 |

```text
document_match_key = documento numérico com zeros à esquerda até 9 posições
```

Exemplos:

| Entrada | Exibição (`document_number`) | `document_match_key` |
|---------|------------------------------|----------------------|
| `123456` | `000123456` | `000123456` |
| `00123456` | `000123456` | `000123456` |
| `123456789` | `123456789` | `123456789` |

No ERP, comparar `document_match_key` com `RIGHT(REPLICATE('0',9) + RTRIM(F1_DOC), 9)` quando `F1_DOC` for numérico.

### 2.3 Série

| Regra | Detalhe |
|-------|---------|
| Máximo | 3 caracteres |
| Transformação | trim + uppercase |
| Vazia | representada por `''` |
| `'0'` | **permanece distinta** de `''` |

### 2.4 Fornecedor

- Identidade: `A2_COD + A2_LOJA` (`A2_FILIAL` **não** entra no matching).
- Bloqueado: `A2_MSBLQL = '1'` — ocultar na busca operacional padrão; admin/`manage` pode listar se necessário.
- Exclusão lógica: `D_E_L_E_T_ = ''` na busca.
- Snapshot no cadastro: código, loja, nome (e opcionalmente nome reduzido) no momento da criação.

---

## 3. Máquina de estados

### 3.1 Status

| Status | Significado |
|--------|-------------|
| `pending` | Recebida; aguardando atendimento |
| `in_progress` | Responsável iniciou o tratamento |
| `blocked` | Impedimento registrado (motivo + descrição obrigatórios) |
| `posted` | Lançamento confirmado no Protheus (terminal no fluxo normal) |
| `cancelled` | Cancelada com justificativa (terminal) |

### 3.2 Motivos de bloqueio (`blocked_reason`)

```text
purchase_order          — aguardando pedido de compra
supplier_registration   — aguardando cadastro
information_correction  — aguardando correção
other                   — outra pendência operacional
```

Quando `status = blocked`: `blocked_reason` e `blocked_description` **obrigatórios**.

### 3.3 Transições permitidas

```text
pending     → in_progress | blocked | posted | cancelled
in_progress → pending | blocked | posted | cancelled
blocked     → in_progress | posted | cancelled
posted      → (nenhuma transição normal)
cancelled   → (nenhuma transição normal)
```

- **`resume`:** exclusivamente `blocked → in_progress`, **preservando** o responsável pelo tratamento (`assignee_*`).
- **Matching automático** pode levar `pending` | `in_progress` | `blocked` → `posted`.
- **Conclusão manual** (`POST .../post-manual`, botão **Já lançada**): `process` **ou** `manage`; justificativa **opcional**; evento `manual_posted` / `completion_source=manual`.
- **Divergência pós-`posted`:** se o cabeçalho sumir do ERP (`D_E_L_E_T_` ou ausência), **não** reabrir; setar alerta de divergência para análise humana.

**Cancelamento (fechado):**

| Quem | Pode cancelar |
|------|----------------|
| `create` | somente solicitação **própria** em `pending`, com justificativa |
| `manage` | qualquer solicitação **não terminal** (`pending`, `in_progress`, `blocked`), com justificativa |

`posted` e `cancelled` não aceitam cancelamento.

---

## 4. Regras funcionais

### 4.1 Cadastro

**Obrigatórios:** filial (`01`|`02`); número da nota; fornecedor; loja; data de emissão; valor; data/hora do recebimento físico (`received_at`).

**Opcionais:** série; observação.

**Automáticos:** usuário criador; `created_at`; snapshot do fornecedor; `document_number` / `document_match_key` / série normalizada; `status = pending`.

### 4.2 Duplicidade

Bloquear nova solicitação **não cancelada** com a mesma chave fiscal (§2.1).

Resposta API: **409 Conflict**, corpo indicando `existing_request_id` (e status atual quando útil).

### 4.3 Edição

| Quem | Quando | O quê |
|------|--------|-------|
| Solicitante (`create`) | `pending` ou `blocked`, própria solicitação | corrigir dados permitidos |
| Processador / admin | conforme `process` / `manage` | corrigir conforme política do endpoint |

- Após `posted`: **proibida** alteração da chave fiscal (filial, fornecedor, loja, documento, série).
- Toda alteração gera evento em histórico (antes/depois).

### 4.4 Fila

- Ordenação padrão: `received_at ASC` (FIFO pelo recebimento físico).
- Filtros mínimos: filial; status; fornecedor; número da nota; período de recebimento; período de emissão.
- Sem prioridade manual na v1.

### 4.5 Comentários

- Canal entre solicitante e processador.
- Não alteram status.
- Autor + timestamp; sem edição silenciosa (v1: imutáveis após criação).
- Visíveis na linha do tempo junto ao histórico.

### 4.6 Conciliação automática

Comportamento implementado:

- Processamento em **lote** via `POST /reconciliation/run` (`manage`) e `POST /reconciliation/refresh` (abertura da fila; cooldown **45 s**).
- Consulta principal `SF1`, `D_E_L_E_T_ = ''`, chave homologada.
- Confirmação opcional de itens ativos em `SD1`.
- Idempotente: reprocessar solicitação já `posted` não altera estado; pode apenas revalidar alerta.
- Persistir referência técnica `sf1_recno`, `erp_entry_date`, `reconciled_at`, `completion_source`.
- Cron/agendamento periódico: **backlog** (onda 5 do playbook).

---

## 5. Modelo conceitual (sem SQL)

### 5.1 `InvoicePostingRequest`

| Grupo | Campos conceituais |
|-------|--------------------|
| Identificação | `id` (UUID), filial |
| Chave fiscal | `document_number`, `document_match_key`, `series`, `supplier_code`, `supplier_store` |
| Fornecedor (snapshot) | `supplier_name` (+ opcional `supplier_short_name`) |
| Valores / datas | `issue_date`, `amount`, `received_at`, `observation` |
| Estado | `status`, `blocked_reason`, `blocked_description` |
| Pessoas | `created_by_*`, `assignee_*` (responsável pelo tratamento, quando houver) |
| Conciliação | `sf1_recno`, `erp_entry_date`, `reconciled_at`, `reconcile_source` (`auto` \| `manual`) |
| Divergência | `divergence_alert` (bool), `divergence_detected_at`, `divergence_detail` |
| Timestamps | `created_at`, `updated_at` |

### 5.2 `InvoicePostingHistory`

| Campo | Uso |
|-------|-----|
| `id`, `request_id` | vínculo |
| `event_type` | ex.: `created`, `updated`, `status_changed`, `reconciled`, `divergence_detected`, `manual_posted`, `cancelled`, `comment_added` (opcional se comentário tiver entidade própria na timeline) |
| `actor_type` / `actor_id` | usuário ou `system` |
| `from_status`, `to_status` | quando aplicável |
| `changes` | mapa/JSON de campos alterados (antes → depois) |
| `justification` | obrigatória em cancelamento e bloqueio; opcional em postagem manual |
| `created_at` | instante do evento |

### 5.3 `InvoicePostingComment`

| Campo | Uso |
|-------|-----|
| `id`, `request_id` | vínculo |
| `author_*` | autor |
| `body` | conteúdo |
| `created_at` | instante |

Sem entidades extras na v1 (motivos de bloqueio = enum/campo; sem tabela de prioridade).

---

## 6. Permissões (registradas no manifesto)

| Código | Responsabilidade |
|--------|------------------|
| `lancamento-notas-fiscais.access` | Abrir o plugin |
| `lancamento-notas-fiscais.create` | Cadastrar; corrigir próprias (`pending`/`blocked`); cancelar própria em `pending` |
| `lancamento-notas-fiscais.view` | Consultar solicitações das filiais `01` e `02` |
| `lancamento-notas-fiscais.process` | Iniciar atendimento, bloquear, retomar, comentar, **Já lançada** |
| `lancamento-notas-fiscais.manage` | Administrar; cancelar não terminais; conciliação em lote (`/reconciliation/run`) |

**v1:** sem permissões `.view.filial-*`.

---

## 7. Contrato da API (implementado)

Base: `/apps/api-delpi/lancamento-notas-fiscais`  
Doc completa: [lancamento-notas-fiscais.md](../../../api-delpi/docs/api/lancamento-notas-fiscais.md).

| Método | Rota | Finalidade | Permissão |
|--------|------|------------|-----------|
| `GET` | `/suppliers` | Buscar fornecedores SA2 | `create` |
| `POST` | `/requests` | Criar solicitação | `create` |
| `GET` | `/requests` | Listar fila (filtros + paginação) | read do plugin* |
| `GET` | `/requests/{id}` | Detalhe + timeline + `allowed_actions` | read* |
| `PATCH` | `/requests/{id}` | Corrigir dados (não status arbitrário) | `create` / `process` / `manage` |
| `POST` | `/requests/{id}/start` | `→ in_progress` | `process` / `manage` |
| `POST` | `/requests/{id}/block` | `→ blocked` (+ motivo) | `process` / `manage` |
| `POST` | `/requests/{id}/resume` | `blocked → in_progress` (preserva assignee) | `process` / `manage` |
| `POST` | `/requests/{id}/comments` | Comentar | `create` / `process` / `manage` |
| `POST` | `/requests/{id}/cancel` | Cancelar (+ justificativa) | `create` (própria/`pending`) ou `manage` (não terminal) |
| `POST` | `/requests/{id}/post-manual` | Já lançada | `process` / `manage` |
| `POST` | `/reconciliation/refresh` | Sync ao abrir fila (cooldown 45s) | read* |
| `POST` | `/reconciliation/run` | Conciliação administrativa em lote | `manage` |

\* `access` \| `create` \| `view` \| `process` \| `manage` — com escopo: só `create` vê próprias.

Envelope e `meta` seguem `api_delpi_success` / `route_contract_registry`. Transições **somente** via ações explícitas.

**Backlog (não na v1):** `GET /queue/summary`.

---

## 8. Critérios de aceite desta especificação

- [x] Decisões 1A consolidadas (SF1, chave, filiais, bloqueio SA2, divergência sem reabertura).
- [x] Normalização de documento (9 dígitos apresentação/match) e série.
- [x] Máquina de estados e motivos de bloqueio.
- [x] Modelo conceitual em 3 entidades.
- [x] Duplicidade e fila FIFO por `received_at`.
- [x] API por ação (implementada) + MFE.
- [x] Migrations do plugin (V001–V003); sem inventar campos Protheus além dos homologados.
- [x] Documentação monorepo (README plugin, API, playbook, índices).

---

## 9. Referências

- Homologação TOTVS (Etapa 1A): conversa / auditoria — `SF1010`, `SD1010`, `SA2010`.
- [PLAYBOOK.md](./PLAYBOOK.md) · [ROADMAP.md](./ROADMAP.md) · [Plugin README](../../../plugins/lancamento-notas-fiscais/README.md)
- Padrões: `new-api-route-checklist.mdc`, `api-delpi-response-contract.mdc`, `plugins-documentation.mdc`, `migrations-immutable-checksum.mdc`.
- Referências de produto: `plugins/inspecoes-entrada`, `plugins/quality-action-plans`, `plugins/estoque-seguranca`.
