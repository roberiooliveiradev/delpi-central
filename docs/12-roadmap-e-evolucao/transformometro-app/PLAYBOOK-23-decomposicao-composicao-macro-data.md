# Playbook 23 — Composição do macro WBS por revisões (data + escopo + conflitos)

**Status:** entregue (jul/2026) — fases A–D + âncora na referência  
**Escopo:** `transformometro-api` + plugin `transformometro`  
**Complementa:** [PLAYBOOK-20](./PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md) (árvore + escopo + overlay) · [PLAYBOOK-18](./PLAYBOOK-18-instancias-filial-setor-escopo.md) (instâncias/melhorias)

---

## 1. Objetivo

O **macro** (mapeamento WBS do processo-mestre) permanece a fonte cadastrada. As **revisões vigentes** das melhorias **alteram visualmente** esse macro nos nós do seu escopo. Não são mundos paralelos desconectados.

```text
macro_base (processo_decomposicao)
  + Δ revisão A (vigente em D, só nós do escopo A)
  + Δ revisão B (vigente em D, só nós do escopo B)
  → visão composta em D  («macro composto» / «agora»)
  → conflicts[] quando 2+ revisões tocam o mesmo nó
```

---

## 2. O que foi feito (entregas)

| Fase | Entrega | Onde |
|------|---------|------|
| **A** | PUT overlay fora do escopo → **400**; warnings/diff na UI da revisão | `revisao_decomposicao_merge_service.assert_overlay_within_escopo`, `RevisaoDecompositionSection` |
| **B** | `GET …/decomposicao/composed?at=` + conflitos + testes | `decomposicao_composition_service`, `decomposition_routes` |
| **C** | Seção «Macro composto» no processo; aviso ao mudar vigência | `ProcessoDecompositionComposedSection`, `RevisaoVigenciaSection` |
| **D** | CRUD estrutural no delta (`extra_nodes`, disable, reparent/`ordem`) | overlay schema + `DecompositionTreeEditor` na revisão |
| **D+** | Confirmação ao alterar vigência se já há medição (`confirm_vigencia_change` / 409) | `update_revisao`, `RevisaoCadastroPanel` |
| **Âncora** | Edição parte do mapeamento da **revisão de referência** (overlay vazio); diff «vs referência» | `build_revisao_view`, UI |

Commits de referência (main): `4bb0615ee` (A–C), `019a7f6d8` (D), `28160588d` (âncora na referência).

---

## 3. Como funciona hoje

### 3.1 Hierarquia de artefatos

```text
Processo-mestre
  └── processo_decomposicao          ← macro WBS (cadastro)
  └── Melhoria A (instância)
  │     └── escopo WBS
  │     └── Revisões: Baseline → v1 → v2…
  │           └── revisao_decomposicao_overlays  ← delta absoluto vs macro
  └── Melhoria B (instância)
        └── … (timeline e escopo próprios)
```

### 3.2 Três visões de mapeamento

| Visão | O que mostra | Uso |
|-------|--------------|-----|
| **Macro do processo** | Árvore cadastrada (`processo_decomposicao`) | Fonte estrutural canônica |
| **Mapeamento da revisão** | Macro ∩ escopo + overlay desta revisão; com overlay vazio, **seed** = mapeamento da referência | Editar o delta to-be |
| **Macro composto** | Macro + overlays das revisões **vigentes** na data `at` | «Como está agora» no processo |

### 3.3 Overlay (persistência)

- Formato: `decomposition_overlay_v1`
- Campos: `node_overrides` (label, descricao, highlight, **parent_id**, **ordem**), `disabled_node_ids`, **`extra_nodes`**
- Semântica de gravação: **absoluto em relação ao macro do processo** (no escopo da melhoria), não relativo à referência
- Motivo: a composição «agora» aplica todos os deltas vigentes sobre a mesma base, sem precisar percorrer a cadeia de referências

### 3.4 Âncora na revisão de referência (edição)

Exceto **baseline**, toda revisão aponta para outra (`revisao_referencia_id`, ou fallback baseline da instância).

| Situação | Comportamento |
|----------|----------------|
| Overlay **vazio** | UI inicia na árvore mesclada da **referência** (`seeded_from_reference`) |
| Overlay **com conteúdo** | UI mostra macro + overlay desta revisão |
| Diff na tela | «vs referência (vX.Y.Z)» (`reference_diff`) |
| Ao salvar | `diff(macro_no_escopo, árvore_editada)` → overlay absoluto |

API `GET /revisoes/{id}/decomposicao` devolve:

- `tree_base` — macro no escopo (base de persistência)
- `tree_reference` — mapeamento mesclado da referência
- `tree` — árvore de trabalho (seed ou merge próprio)
- `referencia`, `seeded_from_reference`, `reference_diff` / `baseline_diff`

### 3.5 Composição temporal («agora»)

- Janela: `data_inicio_vigencia` ≤ `at` ≤ `data_fim_vigencia` (fim aberto = vigente)
- **Baseline não compõe** (cenário não comparável)
- Ordem de aplicação: início de vigência ascendente; empate → `versao_revisao`
- Interseção no mesmo nó → `conflicts[]`; exibição vencedora = última na ordem
- Endpoint: `GET /transformometro/processos/{id}/decomposicao/composed?at=YYYY-MM-DD`

### 3.6 Várias melhorias no mesmo processo — o que a baseline consome

**Cada melhoria tem baseline própria.** A baseline **não** herda o estado composto das outras melhorias.

```text
Melhoria A — baseline  →  Macro ∩ escopo A   (as-is desta timeline)
Melhoria B — baseline  →  Macro ∩ escopo B   (as-is desta timeline; independente de A)

«Agora» no processo   →  Macro + Δ vigentes de A e B (e demais)
```

| Pergunta | Resposta atual |
|----------|----------------|
| Baseline da melhoria B parte do que a A já mudou? | **Não.** Parte do **macro cadastrado** no escopo B. |
| Onde aparece o efeito cruzado de A e B? | Só no **macro composto** (e em conflitos se tocarem o mesmo nó). |
| Timeline de medição/ROI de cada melhoria | Isolada por instância (Playbook 18); referência de comparação = revisão da **mesma** instância. |

### 3.7 Vigência e medição

- Mudar início/fim: aviso na UI (recompõe o macro)
- Se já existe **medição**: PUT revisão exige `confirm_vigencia_change=true` (senão **409**)

---

## 4. Regras de produto (resumo)

| # | Regra |
|---|--------|
| 1 | Escopo da melhoria = nós alteráveis (`instancia_decomposicao_escopo`). |
| 2 | Delta = overlay absoluto no macro; UI ancora na referência quando overlay vazio. |
| 3 | Composição por vigência (não por data de implantação). |
| 4 | Sem revisão vigente no nó → mostra base do macro. |
| 5 | Interseção → `conflicts[]` (sem merge silencioso). |
| 6 | Vigência com medição → confirmação explícita. |
| 7 | Overlay fora do escopo → **400**. |
| 8 | Baseline de cada melhoria → macro ∩ escopo **dessa** melhoria (não o composto global). |

---

## 5. Contrato API (principais)

### `GET /processos/{id}/decomposicao/composed?at=&instancia_id=`

Retorna `tree`, `applied_revisoes`, `conflicts`, `at`.

### `GET /revisoes/{id}/decomposicao`

Retorna merge + `tree_base` + `tree_reference` + diffs vs referência.

### `PUT /revisoes/{id}/decomposicao/overlay`

Valida escopo + estrutura (`extra_nodes` / reparent); 400 se inválido.

### `PUT /revisoes/{id}`

Campo opcional `confirm_vigencia_change` quando há medição e datas mudam.

---

## 6. Limites e não-objetivos (hoje)

| Limite | Detalhe |
|--------|---------|
| Baseline ≠ composto | Baseline **não** inicia no «agora» de outras melhorias; só no macro ∩ escopo. |
| Overlay absoluto | Gravação não é «diff só vs referência»; a UI ancora na referência, a persistência é vs macro. |
| Baseline fora da composição | Cenário `baseline` não entra em `composed`. |
| PK novo no delta | Só com `inherit_all` no escopo; escopo parcial → só nós sob o recorte. |
| Sem travas rígidas pós-medição | Só confirmação na UI/API; não bloqueia edição de overlay após medir. |
| Conflitos = aviso | Lista `conflicts[]` + badge; não impede salvar nem força resolução. |
| Diagrama (hoje) | Playbook 19 S0–S6: overlay clássico sobre o macro; **ainda sem** seed na referência nem `diagrama/composed`. Planejado em **PB19 S7** (espelhar este playbook). |
| Medição por nó WBS | Ainda não há ROI/medição granular por `node_id` (ideia futura PB20). |
| Propagação ao cadastrar macro | Alterar o macro mestre **não** reescreve overlays já gravados; deltas podem ficar órfãos/avisos se nós sumirem. |

### Evoluções possíveis (não implementadas)

1. **Diagrama = mesmo conceito deste playbook (PB19 S7)** — âncora na referência, `GET …/diagrama/composed?at=`, visão vigente primeiro no processo, conflitos de interseção. Spec detalhada em [PLAYBOOK-19 § S7](./PLAYBOOK-19-diagramas-processo-revisao-escopo.md).  
2. Baseline da melhoria B partir do **composto na data de início** dela (foto do «agora» global) — WBS e, depois, diagrama.  
3. Overlay relativo à referência na persistência (cadeia na composição).  
4. Resolução obrigatória de conflitos / trava de vigência após medição.  
5. Motor unificado WBS+diagrama (só se S7 mostrar duplicação excessiva; preferir serviços irmãos).

---

## 7. Arquivos canônicos

| Camada | Arquivo |
|--------|---------|
| Domain overlay/tree | `tm_app/domain/decomposition/decomposition_tree_v1.py` |
| Merge + âncora | `tm_app/application/services/revisao_decomposicao_merge_service.py` |
| Composição | `tm_app/application/services/decomposicao_composition_service.py` |
| HTTP | `tm_app/interface/http/routes/decomposition_routes.py` |
| MFE revisão | `plugins/transformometro/.../RevisaoDecompositionSection.tsx` |
| MFE composto | `.../ProcessoDecompositionComposedSection.tsx` |
| Diff overlay | `.../utils/decompositionOverlayDiff.ts` |
| Testes | `tests/test_decomposition_services.py`, `tests/test_decomposicao_composition_service.py` |

---

## 8. Checklist

- [x] Playbook (este documento)
- [x] PUT overlay enforce escopo
- [x] GET composed + conflitos
- [x] Macro composto no processo
- [x] CRUD estrutural no delta
- [x] Confirmação de vigência com medição
- [x] Âncora de edição = revisão de referência
- [x] Documentação do modelo multi-melhoria / baseline / limites
