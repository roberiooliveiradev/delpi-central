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

TÉO / Transformômetro é a authority da **descrição e evidência do processo**: AS-IS, proveniência operacional, diagnóstico e decisões de negócio registradas no processo.

GitHub é a authority da **especificação funcional TARGET da ferramenta a implementar**, além de contratos, ADRs, código, testes e SHAs quando existirem.

A documentação desta pasta usa o TÉO como fonte de processo, mas **não é um espelho documental do TÉO**. Diferenças deliberadas entre AS-IS e TO-BE são esperadas quando representam redesign aprovado. IDs ficam apenas em [19-rastreabilidade-teo.md](./19-rastreabilidade-teo.md).

## Drift

```text
AS-IS diferente do TO-BE
!= EXECUTION_DRIFT
```

```text
nova evidência do processo
invalida uma premissa necessária do TARGET
→ EXECUTION_DRIFT
→ não adaptar silenciosamente
```

Se a nova evidência apenas descreve um comportamento atual que o TARGET decidiu melhorar/substituir, preservar a evidência e o rationale sem reabrir automaticamente a decisão de produto.

```text
falta binding/seed/contrato
→ TO_INVENTORY
→ confirmar
→ implementar
```

## Naming técnico

Nome de UX: **Portal Controladoria & Finanças**.

Não derivar automaticamente plugin id, basePath, BFF, schema ou topic. Identifiers técnicos devem ser definidos em inglês durante arquitetura técnica.
