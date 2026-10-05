# Authority Index — Portal Controladoria & Finanças

> **Status:** TARGET / implementation handoff  
> **Consolidação:** 2026-10-05

## Ordem de autoridade

Em conflito:

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. regras `.cursor` aplicáveis
3. ADRs e contratos canônicos vigentes
4. schemas, manifest, migrations e implementação real no HEAD
5. testes automatizados atuais
6. documentação técnica vigente
7. planos/roadmaps ativos
8. documentação histórica

Para processo/negócio do PROC-0072, o snapshot TÉO preserva origem, diagnóstico e decisões. Evidência nova que invalide TARGET gera `EXECUTION_DRIFT`.

## Naming

```text
OFFICIAL_PORTAL_NAME = Portal Controladoria & Finanças
PORTAL_SCOPE = MULTI_MACROPROCESS
CLOSING_FEATURE_NAME = Central de Fechamento
PROC_0072 = FIRST_IMPLEMENTED_PROCESS
LEGACY_WORKING_LABEL = Portal Controladoria/Financeiro
```

## Mapa

### Produto / TO-BE
- 31.19 — naming/escopo
- 31.18 — authority/readiness
- 31 — desenho funcional master
- 31.1 — UX/wireframes
- 31.2 — RQ/AC/estados/auditoria
- 31.3–31.13 — P2
- 31.14 — P3
- 31.15 — P4
- 31.16 — P5
- 31.17 — P6
- 33 — decisões consolidadas
- 34 — backlog de implementação

### Origem / AS-IS / diagnóstico
- 01–10.2
- 20
- 30
- 04.1 / 06.1

## TÉO x GitHub

- **TÉO:** processo, evidência, diagnóstico e decisão de negócio.
- **GitHub:** snapshot versionado e handoff técnico.
- Mudança em um lado não implica sincronização automática no outro.
- Divergência material deve ser reconciliada explicitamente.
