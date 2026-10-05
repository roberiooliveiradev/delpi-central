# 00 — Governança e Authorities

## Ordem de autoridade

1. instruções oficiais do GPT Arquiteto DELPI Central;
2. regras `.cursor`;
3. ADRs/contratos canônicos;
4. schemas, manifest, migrations e código no HEAD;
5. testes;
6. documentação técnica;
7. planos/roadmaps;
8. histórico.

Esta pasta é TARGET funcional e handoff; não substitui runtime.

## Linguagem

Fatos/planejamento: `PROVEN | TO_INVENTORY | PLANNED | TARGET`.

Execução: `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`.

Premissa invalidada: `EXECUTION_DRIFT`.

Claims: `OBSERVED/INFORMED | CALCULATED | INFERRED | PROPOSED | UNKNOWN`.

## Evidência

`search miss != ausência`.

Documentação não prova runtime. Teste isolado não prova objetivo inteiro. Causa-raiz não é PROVEN sem evidência causal.

## GitHub ↔ TÉO

TÉO preserva processo, evidência, AS-IS, diagnóstico e decisões de negócio.

GitHub preserva documentação implementável, contratos, ADRs, código, testes e SHAs.

A documentação desta pasta **consolida** o que foi construído no TÉO. IDs ficam apenas em [19-rastreabilidade-teo.md](./19-rastreabilidade-teo.md).

## Drift

```text
nova evidência contradiz TARGET
→ EXECUTION_DRIFT
→ não adaptar silenciosamente
```

```text
falta binding/seed/contrato
→ TO_INVENTORY
→ confirmar
→ implementar
```

## Naming técnico

Nome de UX: **Portal Controladoria & Finanças**.

Não derivar automaticamente plugin id, basePath, BFF, schema ou topic. Identifiers técnicos devem ser definidos em inglês durante arquitetura técnica.
