# E11.S9 — Candidate final R1–R11 — histórico invalidado

**Estado original:** `COMPLETE_GATE` / candidate `782a49721319571f0fe4733d59b8a5cc65ac4c04`  
**Estado vigente após auditoria pós-fechamento:** **INVALIDADO COMO RELEASE EVIDENCE**  
**Auditoria:** [`e11-post-close-audit-2026-09-11.md`](./e11-post-close-audit-2026-09-11.md)

> Este arquivo preserva o resultado que foi produzido para o candidate `782a4972…`, mas não deve mais ser interpretado como `R1–R11 PASS` vigente.

## 1. Resultado histórico executado

A bateria E11.S9 registrou:

- corpus offline + sidecars;
- unknown provider live;
- recommendations + SEND/STREAM/SIMULATE;
- persist/reload/F5;
- efficiency live;
- zero lateral path maps.

O fechamento histórico declarou:

```text
R1..R11 = PASS
globalReleasePass = true
```

## 2. Motivos da invalidação

### R8

O protocolo canônico define alvo total do modo Normal em `<= 5 s` com P50/P95. O candidate registrou aproximadamente:

```text
responseMode = normal
P50 = 41.522 s
P95 = 50.708 s
```

O runner de efficiency considerava PASS pela presença de P50/P95/tokens e provider válido, sem comparar a latência com o threshold canônico.

```text
R8 = FAIL
```

### requiredDimensions

O corpus congelado contém classes com `requiredDimensions` menores ou diferentes da matriz canônica de `docs/testing/chat-ai-flow-families.md`.

Exemplos materiais:

- required args / enum-type ligados apenas a R5;
- unauthorized / write confirmation / injection ligados apenas a R11;
- compound ligado apenas a R1/R7;
- unknown external OpenAPI ligado apenas a R9/R11.

Portanto o agregador não prova que cada classe satisfez todas as dimensões mínimas exigidas.

```text
R1_R11_REQUIRED_DIMENSIONS = FAIL
```

### Evidence reproducibility

O runner offline atual produz `globalReleasePass=false` enquanto as dimensões live estiverem deferred. O manifest versionado contém `globalReleasePass=true` e ao mesmo tempo mantém texto `reasonGlobalReleasePassFalse` dizendo que offline sozinho não fecha release.

```text
EVIDENCE_REPRODUCIBLE = FAIL
```

### Unknown external API

O smoke comprova import/binding/retrieval/selection de provider nunca visto, mas usa endpoint não executável (`example.invalid`) e aceita falha HTTP depois do binding.

Classificação corrigida:

```text
UNKNOWN_EXTERNAL_ROUTING = PASS
UNKNOWN_EXTERNAL_ARGUMENT_BINDING = PASS
UNKNOWN_EXTERNAL_FULL_CHAIN = INCONCLUSIVE
UNKNOWN_EXTERNAL_R9 = INCONCLUSIVE
```

### Metamorphic rename

O gate live chamado metamorphic compara frases sinônimas de estoque. Isso é robustez linguística, não rename de provider/path/operationId.

Fixtures/sidecars históricos podem continuar úteis, mas um novo final candidate deve executar o rename técnico verdadeiro depois do último diff material.

```text
METAMORPHIC_PROVIDER_PATH_OPERATION_ID_RENAME = INCONCLUSIVE
```

## 3. Veredito corrigido de E11.S9

```text
FINAL_CANDIDATE_GIT_SHA = 782a49721319571f0fe4733d59b8a5cc65ac4c04
HISTORICAL_AGGREGATE = PASS
CURRENT_RELEASE_EVIDENCE_STATUS = INVALIDATED
R8 = FAIL
R1_R11_REQUIRED_DIMENSIONS = FAIL
EVIDENCE_REPRODUCIBLE = FAIL
UNKNOWN_EXTERNAL_FULL_CHAIN = INCONCLUSIVE
METAMORPHIC_RENAME = INCONCLUSIVE
GLOBAL_RELEASE_PASS = false
COMPLETE_GATE = FAIL
```

## 4. Condições para substituir esta evidência

Gerar um novo candidate final somente depois de:

1. corrigir evaluator R8 com thresholds por responseMode;
2. alinhar requiredDimensions do corpus à matriz canônica;
3. garantir que manifests sejam gerados e reproduzíveis pelos runners;
4. executar unknown provider full chain com HTTP controlado, response, presentation e R9;
5. executar metamorphic provider/path/operationId rename verdadeiro;
6. concluir os demais bloqueios da auditoria pós-fechamento.

O novo candidate deve ter SHA própria e não reutilizar `782a4972…` como evidência vigente.
