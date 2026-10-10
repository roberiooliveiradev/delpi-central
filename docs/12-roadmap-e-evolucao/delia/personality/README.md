# DÉLIA — Personalidade e comportamento

**Status:** **PRODUCT_BEHAVIOR_BASELINE=APPROVED_PRODUCT_DIRECTION; EDITORIAL_DOCUMENTATION=COMPLETE** (Product Master, 2026-10-10). Os detalhes derivados foram consolidados sob PERS-018, sem se passarem por aprovações individuais. **RUNTIME_IMPLEMENTATION=NOT_PROVEN / BEHAVIORAL_EVAL=TEST_NOT_RUN**.
**Escopo:** exclusivamente identidade comportamental e conversacional: temperamento, humor, iniciativa social, postura de discordância, adaptação contextual e interação com usuários. **Não abrange** aparência física, rosto, corpo, arte do avatar, animações visuais ou redesign de identidade gráfica.
**Natureza:** documentação de produto; **não é** evidência de implementação, runtime, configuração de modelo, autorização, novo agente ou componente.
**Owner de decisão de produto:** Product Master; governança arquitetural preservada pela coordenação DÉLIA.

## Documentos

- [01 — Identidade e temperamento](./01-identity-and-temperament.md)
- [02 — Especificação completa de comportamento e interação](./02-behavior-and-interaction.md)
- [03 — Registro PERS-001..018, origem e decisões](./03-decision-record.md)
- [04 — Avaliação comportamental: cenários, qualidade e evidência futura](./04-behavioral-quality-evaluation.md)

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

**Fronteira com a frente visual:** o Product Master esclareceu em 2026-10-10 que a referência a “criar o avatar” nesta conversa significava definir a **personalidade e o comportamento** da DÉLIA. O avatar visual já é tratado em outra frente; seu status técnico não foi inventariado nesta tarefa. A spec [76](../76-unified-avatar-delia-motion-and-user-profile-visual-specification.md) permanece válida e independente. Nenhum desenho, imagem ou mudança visual é proposto aqui.

## Fechamento editorial de personalidade e comportamento

A identidade e o guia de interação foram finalizados nesta rodada por instrução expressa do Product Master (PERS-018). **Nenhuma escolha adicional de temperamento, humor ou estilo é pré-requisito para a próxima etapa técnica.**

O produto aprova: executiva sofisticada + companheira inteligente; curiosidade e estratégia predominantes, criatividade complementar; carisma; discordância elegante; tratamento por “você”; humor leve e emojis ocasionais; presença inicial perceptível; B participativa + C mais direta quando justificada; adaptação a pedidos de silêncio ou maior comunicação; preferência temporária por conversa e possível oferta de persistência consentida; agrupamento de mensagens de baixa prioridade; **transparência sobre por que a DÉLIA iniciou a conversa**.

O [02](./02-behavior-and-interaction.md) diferencia:
- **decisões individuais expressas:** PERS-002..008 e PERS-010..017;
- **escopo de consolidação autorizado:** PERS-009 e PERS-018;
- **EDITORIAL_DEFAULT_DERIVED:** redação e padrões comportamentais complementares derivados da personalidade aprovada, não aprovação item por item;
- **TO_INVENTORY / TEST_NOT_RUN:** mecanismos, owner/contratos, persistência, thresholds, fontes, gatilhos, notificações, avaliação de modelo e efeitos reais.

A documentação **não** prova modelo, configuração, gravação de preferências, notificação funcional, detecção de presença, criação de serviço, autorização de ACT, nem avanço de fase. Owner/phase/gates vêm do 16 + ledger no HEAD. A personalidade é um **contrato de experiência**, não autorização de operação.

## Regras de continuidade

1. Em novos chats, consultar esta pasta depois da reancoragem ao HEAD e das authorities.
2. Toda nova decisão deve registrar data, origem, status e impacto sem reescrever silenciosamente decisões anteriores.
3. Distinguir `APPROVED_PRODUCT_DIRECTION`, `EDITORIAL_DEFAULT_DERIVED`, `TO_INVENTORY`, `TEST_NOT_RUN` e `IMPLEMENTATION_NOT_PROVEN`. A documentação está fechada editorialmente; isso não altera o status de execução.
4. Personalidade orienta o estilo; não cria direitos, AuthZ, autonomia, inferência emocional, fontes de verdade ou capacidade técnica.
5. Antes de prompt de implementação: inventário, `EXISTING_EQUIVALENT`, `REUSE_DECISION`, fase, CP/RQ, contrato, segurança, testes/evals e critérios de aceite. Ver [04](./04-behavioral-quality-evaluation.md).
