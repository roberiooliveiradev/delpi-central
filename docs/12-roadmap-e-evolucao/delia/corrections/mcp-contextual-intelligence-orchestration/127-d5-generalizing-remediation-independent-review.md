# 127 — Revisão independente: remediação D5/D5-R, release e outcomes
**Data:** 2026-10-23. **TASK:** DELIA-C3-D5-GENERALIZING-EVIDENCE-RELEVANCE-REMEDIATION-01. **Base:** contrato [124](./124-d5-generalizing-root-cause-and-implementation-contract.md), execução [126](./126-d5-remediation-execution-deploy-and-production-homologation.md), baseline [123](./123-production-authenticated-homologation-d4-d5-d8.md), autoridades 16→50→17→49→51→52→21→20→25 + 03/24/60, ADR58, roadmap59, ledger e plano [125](./125-orchestration-complete-refactoring-finite-plan.md).
**Reviewed code SHA:** `ea2f59e930a7056e6364acf640629eb99c82621a`. **Reviewed docs SHA:** `e10299a1f9cfb16e41e5201e0ca60d83efcfad1d`. **Review method:** diff e documentação via GitHub; sem reexecução independente de pytest, SSH ou turnos Kimi. Estado observado do host é evidence reportada pelo executor.

## Veredito
**IMPLEMENTATION=ACCEPT_WITH_RESIDUAL**: correção bounded prova via diff a exigência de `contract_subject=True` para `OUTCOME_CONTRACT_FACTS` e defer de composição CRI quando existe projeção determinística governada. Sem blacklist de `entities.playlist` ou branch VISTA; `selection-only` e owners mantidos no diff. Testes e runtime são PASS **reportados**, não reexecutados por reviewer.
**RELEASE=ACCEPT_WITH_RESIDUAL_REPORTED_EVIDENCE**: imagem `dc8b59fb4fa78a4ef6f3f4c8fbdc70a67b2c798c73cf7cc5ce8cbb481f34f39f` healthy, health 200, 401 sem bearer, rollback informado.
**D5 ORIGINAL=PARTIAL**, não PASS: o dump proibido `entities.playlist` desapareceu, mas resposta projetou índice `productGuide` amplo sem os formatos concretos publicados em `displayFormatCatalog`; contrato 124 AC-D5-01/08 não está integralmente demonstrado como outcome de formatos.
**D5-R=PASS reportado** para pergunta reformulada sobre tipos de visualização (documentação `block_types` real); não substituir por evidência sobre display formats se pergunta difere.
**D4/D8/N1=PASS reportado**; **D8-R=PARTIAL nesta amostra**, contra PASS na baseline 123. Causa não demonstrada como regressão causada pelo diff D5; variância de seleção/encadeamento é HYPOTHESIS até traces e repetição controlada, e deve ser marcada como observação a preservar.
**PLAN_112_COMPLETE=NO**. Refactor [125](./125-orchestration-complete-refactoring-finite-plan.md) R0–R7 não é autorizado por este aceite; baseline D5 ainda não está congelado como PASS funcional.

## Revisão causal e ressalvas técnicas
1. O erro determinístico de promover qualquer contrato de DISCOVERY a `CONTRACT_FACTS` foi corrigido na assinatura `assess_outcome(..., contract_subject=False)` e na borda CRI; isso elimina a causa observada do JSON na amostra testada.
2. O campo `contract_subject` é hipótese tipada do modelo e não authority. Casos com proposal contraditório/malicioso, request implícito e modelo que omite flag permanecem pontos de generalização; não inventar classificador lexical.
3. A borda CRI agora defere em situações `ENVELOPE_ONLY`/`INSUFFICIENT` ou `ANSWERED` com `_deterministic_guidance_content`. É necessário preservar coerência entre texto terminal e verdict/limitations, especialmente quando guidance amplo é verdadeiro mas não suficiente à pergunta. `GROUNDED` ou `limitations=[]` não significa ANSWERED.
4. `get_catalog` não é seleção automaticamente incorreta; seu payload pode conter documentação de formatos. O problema remanescente é pertinência e granularidade da projeção, não uma escolha fixa de ferramenta.
5. Rótulos inglês `title/summary`, `Group code` etc. são dívida de apresentação separada, sujeita a JSON governado e contrato, nunca substituição de valores empresariais.

## Próximo passo
**NÃO iniciar segundo rework implícito** do pacote 124 nem misturar com a refatoração 125. Devolver ao Product Master decisão bounded sobre o residual D5 (amplitude `productGuide`/dados concretos `displayFormatCatalog`) e controle D8-R, com AC explícitos e critérios de parada. Até lá, preservar baseline de produção estável; no-go para declarar D5 completo. Toda próxima decisão deve começar por HEAD/authorities/ledger. Não promover fase. Registrar execução/teste como `PASS|FAIL|PARTIAL|TEST_NOT_RUN` com SHA/model/config.
```text
COORDINATION_VERDICT=ACCEPT_WITH_RESIDUAL
D5=PARTIAL
D5_R=PASS_REPORTED
D4=PASS_REPORTED
D8=PASS_REPORTED
D8_R=PARTIAL_OBSERVED_CAUSE_UNPROVEN
PLAN_112_COMPLETE=NO
REFACTOR_125_AUTHORIZED=NO
NEXT=PRODUCT_MASTER_BOUNDED_RESIDUAL_DECISION
```
