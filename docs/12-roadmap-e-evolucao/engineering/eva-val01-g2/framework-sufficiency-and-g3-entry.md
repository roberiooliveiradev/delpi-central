# G2 — Suficiência do framework e entrada G3

## Decisão

```text
FRAMEWORK_SUFFICIENCY_DECISION=
  SLANet_ALONE_INSUFFICIENT_FOR_DENSE_HIERARCHY_AND_FOOTER_REJECTION
  OCR_TOKENS_SUFFICIENT_AS_EVIDENCE_STREAM
  UNDERSTANDING_FAILS_TO_CONSUME_RECOVERY_SIGNALS (line_texts)

G3_ENTRY_DECISION=RECOMMENDED_AFTER_COORDINATION_ACK
  Motivo: primeira perda geométrica PROVEN no SLANet (fusão/rowspan/footer cells);
  benchmark de parâmetros/crop/DPI/alternativas sandbox (perfil A vs B) ainda é
  necessário antes de G4 para não inventar parser paralelo prematuro.

G4_NOT_AUTHORIZED=true
IMPLEMENTATION_FORBIDDEN_IN_G2=true
```

## Fundamentação

1. **OCR (PaddleOCR)** separa A2/A3, códigos, 502257xx e dígitos de rodapé — não é a causa raiz.
2. **SLANet** funde bandas Y de códigos (p10), gera rowspan monolítico (p12) e incorpora tokens de rodapé `4`/`5` (p13).
3. **Adapter** já emite `line_texts`/`line_centers` quando há bandas — sinal útil **não** promovido a ocorrências distintas no Understanding para a coluna de código.
4. Portanto: framework **não basta sozinho** na configuração atual para M1 estrutural desses layouts; porém **há evidência de recuperação parcial** sem novo motor — G3 deve medir se ajuste de crop/DPI/engine alternativa reduz a fusão SLANet; G4 (futuro) deve priorizar o menor ajuste na camada dona da perda residual (consumer Understanding e/ou config de crop), **sem** parser paralelo.

## Proposta de menor ajuste (NÃO implementar no G2)

Ordem candidata para Coordination/G4:

1. **Crop / exclusão de rodapé** na região tabular (evitar tokens 1..8 de folha como células).
2. **Understanding:** promover `line_texts` da coluna `component_code` a linhas lógicas quando centros Y alinham a itens distintos (generalizar; sem hardcode 90264135).
3. **Papéis:** subset_code com rowspan ≠ `component_code`; popular `parent_group_candidate` a partir da âncora de grupo, sem deduplicar filhos.
4. Só se G3 mostrar insuficiência residual **após** (1)–(3): considerar benchmark de engine alternativa (PP-Structure etc.) em sandbox — nunca instalar em produção no G3.

## Lacunas / responsabilidades

| Lacuna | Responsável |
|---|---|
| GT owner ainda DRAFT | Engenharia |
| Thresholds G1 | Engenharia |
| Amostra Totus live 90264135 | Executor+Auth usuário / Domain API |
| `occurrence_id` ausente no contrato structure | Domain API / Coordination se novo campo |
| G3 benchmark | Gate seguinte (não G2) |
