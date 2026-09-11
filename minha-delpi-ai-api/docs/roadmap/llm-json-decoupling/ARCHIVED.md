# Histórico — Ondas A–I

**Estado em 2026-09-11:** este arquivo é **histórico**, não representa o aceite vigente do programa.  
**Programa atual:** **REABERTO — Onda J**  
**Plano ativo:** [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)

As Ondas A–I foram executadas e produziram evidências úteis, inclusive `globalReleasePass=true` em um candidate anterior. Uma auditoria posterior do código encontrou drifts materiais que invalidam o uso desses PASS como release do estado atual.

Principais motivos da reabertura:

- mapa path→domain recriado em Python após remoção do JSON;
- parameter strategy recriada por path/operationId;
- continuidade multi-turn dependente de path-tail/operationId inventory;
- registry `operationIds` residual como catálogo técnico;
- semantic authority duplicada;
- recommendations ainda com fallback/oracle estático;
- capability metadata de efeito/risco inadequada;
- Clean Architecture/DI residual;
- credential defaults em smoke;
- unknown-provider/metamorphic não reexecutados após o último diff material.

Portanto:

```text
PASS A–I = evidência histórica do estado avaliado
PASS A–I != PASS do candidate final atual
```

A documentação só volta a ser arquivada como concluída após a Onda J atingir:

```text
CUTOVER_RESULT = PASS
GENERALIZATION_RESULT = PASS
CLEANUP_RESULT = PASS
COMPLETE_GATE = PASS
VERIFY_FINAL = PASS
FINAL_RESULT = PASS
```

Fontes vigentes:

- [`README.md`](./README.md)
- [`roadmap.md`](./roadmap.md)
- [`prompt-cursor-execucao-corretiva.md`](./prompt-cursor-execucao-corretiva.md)
- [`planos/11-corrective-cutover-generalization-cleanup.md`](./planos/11-corrective-cutover-generalization-cleanup.md)

Histórico detalhado de execução permanece em [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) e no Git.

Não criar `.plan.md` paralelo para o mesmo objetivo.
