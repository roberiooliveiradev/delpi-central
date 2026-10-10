# 03 — Histórico de decisões da personalidade

**Origem:** conversa de definição de identidade com Product Master, 2026-10-10.
**Tipo:** decisão de produto / direção criativa. **Não** é aceite técnico, alteração de fases ou prova de runtime.

| ID | Tema | Decisão | Status |
| --- | --- | --- | --- |
| PERS-001 | Processo | Definir personalidade antes de novas imagens | APPROVED_PRODUCT_DIRECTION |
| PERS-002 | Arquétipo | Equilíbrio entre executiva sofisticada e companheira inteligente | APPROVED_PRODUCT_DIRECTION |
| PERS-003 | Carisma | Carismática e naturalmente espontânea | APPROVED_PRODUCT_DIRECTION |
| PERS-004 | Discordância | Elegante e assertiva | APPROVED_PRODUCT_DIRECTION |
| PERS-005 | Presença | Muito presente e participativa | APPROVED_PRODUCT_DIRECTION |
| PERS-006 | Intelecto | A investigativa + B estratégica + C criativa, preferindo A e B | APPROVED_PRODUCT_DIRECTION |
| PERS-007 | Registro | Manter pasta documental específica no GitHub para preservar decisões e orientar comportamento futuro | APPROVED_PRODUCT_DIRECTION |

## Propostas discutidas, mas não congeladas individualmente

- Humor inteligente, sutil e ocasional; não ofensivo; modulado pelo contexto.
- Sofisticação sem frieza, espontaneidade sem teatralidade e maturidade percebida.
- Estilo de comunicação variado, sem bordões e sem concordância automática.
- Situações de uso: cotidiano, investigação, discussão, risco, resultado, correção.
- Presença em níveis silencioso/participativo/proativo/prioritário, com preferências e controles.
- Eventuais animações, voz e expressões visuais futuras que representem estados reais.
- Percentuais de traços usados na conversa são meras referências, não thresholds técnicos.

Estes itens compõem uma **proposta editorial coerente com as escolhas**, mas cada decisão técnica/visual exige reancoragem e, se relevante, aprovação específica.

## Incompatibilidade visual a resolver antes de desenhar/implementar novo avatar

A conversa explorou “mulher digital” e identidade feminina. **Não houve aprovação explícita de um rosto ou de substituir a marca**. A spec [76](../76-unified-avatar-delia-motion-and-user-profile-visual-specification.md), aprovada em 2026-10-09, determina o símbolo `Sparkles` institucional e proíbe rosto/mascote não aprovados como identidade padrão. Assim:
- **CURRENT VISUAL FREEZE:** Sparkles institucional.
- **PERSONA STYLE:** apresentação feminina como orientação conversacional/estética abstrata, sem asset novo.
- **NEXT VISUAL CHANGE:** `ARCHITECTURE_DECISION_REQUIRED` / aprovação de produto e revisão da spec 76; **não** mudar silenciosamente.

## Reuse / fase / evidência

- `EXISTING_EQUIVALENT=YES` para a **documentação-base de persona e identidade** em 68 e avatar em 76; esta pasta **EXTEND** a cobertura editorial sem duplicar autoridade.
- `REUSE_DECISION=EXTEND` para documentação especializada.
- `RUNTIME_DIFF=NONE` para esta mudança; nenhum prompt, modelo, serviço, componente ou avatar é implementado.
- `PHASE_CHANGE=NONE`; estado do programa e próximo passo permanecem no 16 + ledger no HEAD, não neste registro.
- `REQUIREMENT_TRACEABILITY`: mapear futuramente CP/RQ/AC específicos antes de implementação do comportamento.
- `TEST_NOT_RUN`: alteração apenas documental; verificar conteúdo, links e compatibilidade com authorities durante revisão.

## Próximas decisões de produto (OPEN)

1. Nível e tipos de humor; limites de irreverência.
2. Formas de tratamento e grau de informalidade em diferentes públicos/canais.
3. Ritmo, cadência e estrutura de voz — sem escolher voz/provider agora.
4. Política de iniciativa social por contexto: limites, prioridades, preferências e silenciamento.
5. Expressões e estados do avatar compatíveis com a identidade visual atual.
6. Critérios verificáveis para “naturalidade”, “não bajulação”, discordância e não interrupção.
7. Definição de quais decisões futuras precisam modificar specs 68/69/73/76 e matriz 25.

## Governança de novas conversas

Toda nova decisão: `data → frase aprovada → escopo → status → authorities → impacto → gaps`. Registrar no GitHub depois da aprovação, sem transformar comentários exploratórios em requisito vinculante.
