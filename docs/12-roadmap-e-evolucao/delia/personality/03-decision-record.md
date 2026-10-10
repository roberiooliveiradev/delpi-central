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
| PERS-008 | Fronteira de escopo (esclarecimento de 2026-10-10) | O trabalho neste chat é exclusivamente sobre personalidade, comportamento e interação; o avatar físico/visual está em desenvolvimento separado e não será tratado aqui | APPROVED_PRODUCT_DIRECTION |

## Propostas discutidas, mas não congeladas individualmente

- Humor inteligente, sutil e ocasional; não ofensivo; modulado pelo contexto.
- Sofisticação sem frieza, espontaneidade sem teatralidade e maturidade percebida.
- Estilo de comunicação variado, sem bordões e sem concordância automática.
- Situações de uso: cotidiano, investigação, discussão, risco, resultado, correção.
- Presença em níveis silencioso/participativo/proativo/prioritário, com preferências e controles.
- Eventuais animações, voz e expressões visuais futuras que representem estados reais.
- Percentuais de traços usados na conversa são meras referências, não thresholds técnicos.

Estes itens compõem uma **proposta editorial coerente com as escolhas**, mas cada decisão técnica/visual exige reancoragem e, se relevante, aprovação específica.

## Fronteira da frente visual (esclarecimento)

O Product Master explicou que a expressão “criar avatar” nesta conversa referia-se à **personificação comportamental** — como a DÉLIA lida com usuários — e não ao desenvolvimento da imagem ou aparência física. O avatar visual tem trabalho próprio em andamento, conforme informação do usuário; não foi objeto de inventário técnico nesta tarefa. A spec [76](../76-unified-avatar-delia-motion-and-user-profile-visual-specification.md) continua sendo referência da frente visual. Não há, por esta conversa, solicitação ou aprovação de substituição de marca, rosto, mascote, animação ou arte.

## Prontidão para fechamento da identidade comportamental

**Avaliação:** as decisões PERS-002 a PERS-006, em conjunto, já sustentam o fechamento do **perfil geral de comportamento**: elegante, carismático, espontâneo, investigativo e estratégico, criativo como traço complementar, assertivo ao discordar e muito presente/participativo. **Estado:** `READY_FOR_PRODUCT_MASTER_FREEZE`, não `FROZEN`; aguarda comando inequívoco de aprovação do baseline de comportamento. Detalhes operacionais (frequência, silenciamento, públicos, preferências, critérios e evals) seguem `OPEN` e não bloqueiam a definição de alto nível. `IMPLEMENTATION_NOT_PROVEN`.

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
3. Ritmo e cadência da conversa e estilo verbal por contexto (sem selecionar timbre ou provider de voz).
4. Política de iniciativa social por contexto: limites, prioridades, preferências e silenciamento.
5. Padrão de adaptação comportamental a chat, notificações e situações críticas; a aparência do avatar pertence a outra frente.
6. Critérios verificáveis para “naturalidade”, “não bajulação”, discordância e não interrupção.
7. Rastreabilidade CP/RQ/AC e estratégia de avaliação para futura implementação; atualização das specs de UX somente se o respectivo owner e a evidência exigirem.

## Governança de novas conversas

Toda nova decisão: `data → frase aprovada → escopo → status → authorities → impacto → gaps`. Registrar no GitHub depois da aprovação, sem transformar comentários exploratórios em requisito vinculante.
