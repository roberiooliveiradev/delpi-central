# G3 — Decisão de suficiência estrutural

## Três hipóteses (Doc 119 §59.2 G3)

| Hipótese | Veredito G3 | Evidência |
|---|---|---|
| **H1** Framework atual suficiente; defeito principalmente na integração | **ACEITA (principal)** | Crop G1 DRAFT vs crop Understanding: P13 `4 5` some; P12 perde rowspan monolítico e preserva AE/AH/AG+códigos; P10 permanece fundido no SLANet mas com `line_texts` utilizáveis |
| **H2** Recurso nativo existente produz estrutura superior | **REJEITADA / UNAVAILABLE** | PP-StructureV3, TableRecognitionPipelineV2, TableCellsDetection importáveis porém **não operacionais** sem provisionar pesos/deps — proibido instalar em produção neste gate |
| **H3** Evidência inconclusiva | **NÃO** para a decisão de caminho | Comparativo A (SLANet×crop) é suficiente para orientar G4; alternativas nativas ficam `TEST_NOT_RUN` até Abstraction Gate de provisionamento |

```text
FRAMEWORK_SUFFICIENCY_DECISION=
  CURRENT_SLANET_SUFFICIENT_AS_GEOMETRY_ENGINE_WHEN_CROP_CORRECT
  RESIDUAL_DEFECTS_MOSTLY_INTEGRATION=
    regioner_crop_footer_and_table_tightness
    understanding_line_texts_split_for_fused_code_cells
    subset_role_and_parent_group_projection
  NATIVE_ALTERNATES=IMPORTABLE_NOT_OPERATIONAL_WITHOUT_NEW_WEIGHTS
  DO_NOT_PROVISION_NEW_FRAMEWORK_IN_G4_BY_DEFAULT
```

## Generalization limitations

- G1 DRAFT não é GT homologado — métricas são **estruturais candidatas**.
- Melhora por crop **não** autoriza hardcode de coordenadas do `90264135`; G4 deve generalizar exclusão de banda administrativa / aperto de região tabular por evidência geométrica.
- P12: preservação de filhos ≠ recuperação automática do pai subset no Understanding.
- P10: SLANet continua fundindo códigos adjacentes verticalmente mesmo com crop justo — integração deve consumir `line_texts`.
- Alternates: qualquer adoção futura exige gate de modelos/owner (Doc 116) — fora do G3.

## Menor implementação futura (G4 — NÃO implementar agora)

Ordem recomendada (camada dona da perda):

1. **Regioner / crop** (application perception path): excluir faixa de rodapé de índices; preferir bbox tabular apertado coerente com `component_table` (sem coordenadas por PDF).
2. **Understanding:** promover `line_texts` da coluna de código a ocorrências distintas quando centros Y alinham a itens distintos; tipar `subset_code` ≠ `component_code`; preencher `parent_group_candidate` a partir de âncora rowspan/grupo.
3. **Só se (1)+(2) falharem em regressão autorizada:** reabrir Abstraction Gate para provisionar PP-Structure/TRPV2 em sandbox — nunca como parser paralelo no Understanding.

```text
G4_ENTRY_RECOMMENDATION=AUTHORIZED_CANDIDATE_AFTER_COORDINATION_ACK
RECOMMENDED_MINIMAL_DIFF=regioner_crop_hardening + understanding_line_texts_and_roles
NEW_FRAMEWORK_INSTALL=NOT_RECOMMENDED
```
