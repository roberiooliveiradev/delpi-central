# DÉLIA — Personalidade e comportamento

**Status:** `APPROVED_PRODUCT_DIRECTION` para decisões explicitamente confirmadas pelo Product Master em conversa em 2026-10-10; demais propostas `TARGET / OPEN`.
**Escopo:** identidade conversacional, temperamento, humor, iniciativa social, postura de discordância, adaptação contextual e futuras orientações de apresentação.
**Natureza:** documentação de produto; **não é** evidência de implementação, runtime, configuração de modelo, autorização, novo agente ou componente.
**Owner de decisão de produto:** Product Master; governança arquitetural preservada pela coordenação DÉLIA.

## Documentos

- [01 — Identidade e temperamento](./01-identity-and-temperament.md)
- [02 — Guia de comportamento e interação](./02-behavior-and-interaction.md)
- [03 — Registro de decisões, pendências e conflitos](./03-decision-record.md)

## Precedência

Esta pasta detalha a personalidade **sem substituir**:
- [16 — Plano Mestre](../16-execution-master-plan.md)
- [50 — Standalone](../50-standalone-copilot-application-architecture.md)
- [17 — Componentes/contratos](../17-component-and-contract-map.md)
- [49 — Padrões](../49-architecture-and-design-patterns-standard.md)
- [51 — Integração](../51-platform-integration-baseline.md)
- [52 — Bootstrap](../52-standalone-repository-and-bootstrap-plan.md)
- [21 — Dados/estado](../21-data-and-state-model.md)
- [20 — Testes/aceite](../20-testing-and-acceptance-matrix.md)
- [25 — Rastreabilidade](../25-requirements-traceability.md)
- [24 — Product Spec](../24-product-specification.md)
- [68 — Naming e persona base](../68-delia-product-identity-and-naming.md)
- [73 — Identidade visual chat-first](../73-chat-first-visual-identity-and-message-anatomy-specification.md)
- [76 — Avatar unificado e motion](../76-unified-avatar-delia-motion-and-user-profile-visual-specification.md)
- [Execution Ledger](../evidence/execution-ledger.md).

**Conflito visual conhecido:** o documento 76 aprova `Sparkles` como avatar institucional e proíbe rosto/mascote não aprovados. A exploração conversacional de uma apresentação feminina/personagem **não revoga** esse freeze. Alteração visual requer decisão explícita e revisão de compatibilidade; nenhuma imagem nova é autorizada por estes arquivos.

## Regras de continuidade

1. Em novos chats, consultar esta pasta depois da reancoragem ao HEAD e das authorities.
2. Toda nova decisão deve registrar data, origem, status e impacto sem reescrever silenciosamente decisões anteriores.
3. Distinguir `APPROVED_PRODUCT_DIRECTION`, `PROPOSAL`, `OPEN` e `IMPLEMENTATION_NOT_PROVEN`.
4. Personalidade orienta o estilo; não cria direitos, AuthZ, autonomia, inferência emocional, fontes de verdade ou capacidade técnica.
5. Antes de prompt de implementação: inventário, `EXISTING_EQUIVALENT`, `REUSE_DECISION`, fase, CP/RQ, contrato, segurança, testes/evals e critérios de aceite.
