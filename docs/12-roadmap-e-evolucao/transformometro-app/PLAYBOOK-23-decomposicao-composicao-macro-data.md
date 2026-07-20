# Playbook 23 — Composição do macro WBS por revisões (data + escopo + conflitos)

**Status:** Fase A–C MVP (jul/2026)  
**Escopo:** `transformometro-api` + plugin `transformometro`  
**Complementa:** [PLAYBOOK-20](./PLAYBOOK-20-decomposicao-processo-arvore-mapeamento.md) (árvore + escopo + overlay)

---

## 1. Objetivo

O **macro** (mapeamento WBS do processo) permanece a base cadastrada. As **revisões ativas/vigentes** das melhorias **alteram visualmente** o macro nos nós do seu escopo. Não são mundos paralelos desconectados.

```text
macro_base
  + Δ revisão A (vigente em D, só nós do escopo A)
  + Δ revisão B (vigente em D, só nós do escopo B)
  → visão composta em D
  → conflicts[] quando 2+ revisões tocam o mesmo nó
```

---

## 2. Regras de produto

| # | Regra |
|---|--------|
| 1 | **Escopo da melhoria** = nós que a revisão pode alterar (já em `instancia_decomposicao_escopo`). |
| 2 | **Delta da revisão** = overlay (`label`, `descricao`, `highlight`, `disabled_node_ids`) **somente** dentro do escopo. |
| 3 | **Data de composição** = `data_inicio_vigencia` … `data_fim_vigencia` (implantação não entra na janela). |
| 4 | Sem revisão vigente no nó em D → mostra **base**. |
| 5 | Interseção → **nunca merge silencioso**: badge/lista `conflicts[]`; vencedor de exibição = início mais recente (empate → `versao_revisao`). |
| 6 | Alterar datas de vigência → **aviso de impacto** na UI (recompõe o macro). |
| 7 | PUT overlay fora do escopo → **400** (não só warning). |

### Fora do MVP (Fase D+)

- CRUD estrutural livre no delta (`extra_nodes` / reparent) — requer evolução de schema do overlay.
- Travas rígidas de data após medição (só confirmação no MVP).

---

## 3. Contrato API

### `GET /transformometro/processos/{processo_id}/decomposicao/composed?at=YYYY-MM-DD`

```json
{
  "processo_id": "…",
  "at": "2026-07-20",
  "tree": { "format": "decomposition_tree_v1", "nodes": [/* base + deltas aplicados */] },
  "applied_revisoes": [
    {
      "revisao_id": "…",
      "instancia_id": "…",
      "versao_revisao": "2.0.0",
      "cenario_tipo": "automacao",
      "data_inicio_vigencia": "2026-04-01",
      "node_ids_tocados": ["pk_1", "t_2"]
    }
  ],
  "conflicts": [
    {
      "node_id": "t_2",
      "field": "label",
      "winner_revisao_id": "…",
      "revisoes": [
        { "revisao_id": "…", "label": "A" },
        { "revisao_id": "…", "label": "B" }
      ]
    }
  ]
}
```

### PUT overlay

Rejeita `node_overrides` / `disabled_node_ids` fora de `expand_escopo_node_ids`.

---

## 4. Entregas MVP

| Fase | Entrega |
|------|----------|
| A | Validação de escopo no PUT; UI revisão com highlight/disable + warnings/diff |
| B | Serviço + GET `composed?at=` + testes |
| C | Seção «Macro composto» no processo + aviso ao mudar datas |

---

## 5. Checklist

- [x] Playbook
- [x] PUT overlay enforce escopo
- [x] GET composed
- [x] Testes unitários composição/conflito
- [x] MFE delta + composed + aviso data
