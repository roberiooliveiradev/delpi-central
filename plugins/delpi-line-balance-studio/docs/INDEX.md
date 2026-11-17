# Documentação — DELPI Line Balance Studio

**Status:** DOCUMENTED / IMPLEMENTATION_PENDING. **Data:** 2026-11-17.  
**Produto:** Studio reutilizável, com primeira integração Portal Engenharia > Processos. **Autorização de produto:** concedida. **Contrato inicial:** [README principal](../README.md).

## Mapa de leitura
1. [Arquitetura e boundaries](architecture.md) — ownership, módulos, integrações, decisões.
2. [Modelo e contratos candidatos](contracts.md) — estudo, operação, tempos, cenário, ports.
3. [Experiência V4 e wireframes](ux-workspace-v4.md) — entrada, tabela, postos, gráfico, estados e mobile.
4. [Catálogo dos seis métodos](methods-catalog.md) — status, requisitos e evolução de cada um.
5. [Yamazumi V4](yamazumi-spec.md) — comportamentos, cálculos permitidos, interatividade.
6. [Turnos e pausas](shift-schedule-spec.md) — dois modos de entrada, validações e prévias.
7. [Integração e estratégia de extração](integration-and-migration.md) — adapters, primeiro consumidor, sequência segura.
8. [Testes e aceite](acceptance-and-test-matrix.md) — requisitos e gates.
9. [Roadmap e registro de evidências](roadmap-and-ledger.md) — entregas, owners, status.

## Fontes
- [Plano mestre V3 de seis métodos](../../../docs/12-roadmap-e-evolucao/engineering/ux/routing/line-balancing-v3-six-methods-master-plan.md) (corrigir link relativo se a árvore for movida).
- [Issue #250 — Processos + Yamazumi V3](https://github.com/roberiooliveiradev/delpi-central/issues/250).
- Código legado da experiência: `plugins/engineering/src/features/processes/line-balancing/`; referência de composição `LineBalancingPage.tsx`, `yamazumi.ts`, `methodCatalog.ts`.
- Biblioteca canônica de UI: `@delpi/plugin-ui`.
- Autoridade de cálculo: `engineering-api/engineering_app/domain/routing/line_balance.py`.

**Regra:** fontes oficiais não podem ser confundidas com documentação TARGET. Os contratos abaixo são candidatos até implementação/testes no SHA. Não gerar runtime a partir de README.
