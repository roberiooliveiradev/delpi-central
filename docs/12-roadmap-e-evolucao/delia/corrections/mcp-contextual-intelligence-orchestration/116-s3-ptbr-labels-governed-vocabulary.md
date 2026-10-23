# 116 — S3 Comunicação PT-BR — vocabulário governado `field_labels` (v4)

**Track:** `DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01` / STEP=S3
**Plano:** [112](./112-self-awareness-finite-delivery-plan.md) §9 ·
**Matriz:** [113](./113-s0-contract-freeze-and-responsibility-matrix.md)
**Autorização PO:** `f7b6a601cb3770a2e592989d0a83371b95bbfaf0`
**Status:** `IMPLEMENTED` — `INDEPENDENT_REVIEW_PENDING`

---

## 1. Escopo e correção de direção

Implementa **RQ-SA05** (D8). A diretriz vinculante §9 do doc 112
(`645684d24b`) corrigiu a ampliação de `_FIELD_CLAUSE_LABELS` dentro
de `orchestration.py`: rótulos declarados pertencem ao recurso JSON
governado; resolução de rótulos ao módulo de apresentação legítimo.

## 2. Arquitetura entregue

```text
config/cri_presentation.delpi.json  (v4 — nova seção field_labels)
  → cri_instruction_resource.py     (validação fail-closed, versionada)
  → CriPresentationVocabulary.field_labels
  → conversational_response.py      (UNICA resolução de rótulos)
  → orchestration.py                (consome; nenhum mapa local)
```

- **`cri_presentation.delpi.json` v4**: seção `field_labels` com 183
  chaves canônicas → `{article, label, suffix}` (ex.
  `updatedat → a / data de atualização / informada`,
  `cnpj → o / CNPJ / informado`). Conteúdo migrado 1:1 do mapa
  Python — zero duplicação.
- **Loader**: `field_labels` é seção **opcional** (ausente ⇒ `{}`);
  quando presente, validação estrutural fail-closed — chave
  `^[a-z0-9]+$` ≤64 chars, exatamente 3 partes, article ∈ {o,a},
  sem placeholders, ≤256 entradas, ≤96 chars por texto. Versões
  aceitas `{2,3,4}`; versão desconhecida falha.
- **`conversational_response.py`** (leaf, sem ciclo — orchestration
  já a importa): `FieldLabels`, `field_label_parts`,
  `field_display_label`, `field_clause_label`,
  `unmapped_field_label` — a única projeção de rótulos para CRI,
  detalhe, lista e comparação.
- **`orchestration.py`**: `_FIELD_CLAUSE_LABELS`, `_clause_prefix` e
  `_unmapped_field_label` removidos; `field_labels` trilha por
  `self._field_labels` até `_detail_lines`, `_compose_answer`,
  `_proven_field_differences`, `_selected_proven_differences` e
  `_cri_presented_record`.
- **`root_composer.py`**: o vocabulário de apresentação é carregado
  **incondicionalmente** — `field_labels` alimenta o caminho
  baseline mesmo com `response_intelligence_enabled` off; falha de
  recurso ⇒ warning + fallback neutro, e (se CRI pedido) CRI
  desativa fail-closed como antes. Comportamento de ativação CRI
  preservado (só `vocabulary.sections` alimenta `compose_cri_response`).

## 3. Contrato do fallback (campo desconhecido)

- Chave de palavras não mapeada ⇒ humaniza (`codigo_processo` →
  `Codigo processo`) — palavras do owner preservadas, nunca
  traduzidas, nunca fundidas (`Codigoprocesso`).
- Chave com dígitos (`b2_cm1`) ⇒ byte-exact — código empresarial
  pesquisável não pode ser adulterado.
- Acrônimos (`CNPJ`, `SKU`, `CEP`) preservam forma canônica via
  capitalização só do primeiro caractere.
- Valores, códigos, descrições, medidas, unidades e proveniência:
  verbatim, sempre.

## 4. Evidência

- `tests/test_c3_self_awareness_ptbr_labels.py` — 12 testes:
  golden D8 (7 campos), unknown/humanize/verbatim, clause path,
  CRI parity, baseline-sem-vocabulário neutro, diffs (raw key +
  label conhecido), guidance skip-keys, preservação de conteúdo,
  e contrato do recurso (v4 carrega, versão 99 falha, formas
  inválidas falham, >256 entradas falha, seção ausente ⇒ `{}`).
- Regressões existentes alinhadas: helpers de teste que dependem de
  rótulos recebem o recurso real carregado
  (`test_intelligence_loop_evals`, `test_specialist_capability_orchestration`,
  `test_stage05_grounded_response`, `test_q02c_b2_typed_comparison_outcome`,
  `test_cri_e3_conversational_presentation` version→4).
- Suíte backend completa: **verde** (exit 0).

## 5. Decisões de escopo registradas

- `active`/`ativo`, `order`, `role` removidos do mapa: rótulo
  "ativo" poderia mascarar a tradução não autorizada de valor
  codificado ("S"); `order`/`role` são ambíguos. AC §9(i) — só
  entradas justificáveis por semântica reconhecida.
- Caminho de diffs usa a mesma projeção (capitalizada) — alinhado
  com detalhe/CRI; expecteds atualizados (`- Status:`, `- Código:`).

## 6. Resíduos

- Campos novos do domínio exigem revisão de conteúdo no JSON
  governado (versionado, code-reviewed) — por desenho.
- `INDEPENDENT_REVIEW_PENDING`.
