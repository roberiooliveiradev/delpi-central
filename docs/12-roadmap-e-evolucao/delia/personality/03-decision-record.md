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
| PERS-009 | Continuidade documental (2026-10-10) | Prosseguir para detalhar as regras de comportamento e interação no documento 02, preservando como propostas as escolhas ainda não aprovadas | APPROVED_WORK_SCOPE |
| PERS-010 | Iniciativa conversacional B+C (2026-10-10) | **B participativa** como abordagem padrão, **C muito ativa** quando relevância/contexto autorizado/evidência justifiquem; nunca pressupõe ACT ou novo mecanismo de notificação | APPROVED_PRODUCT_DIRECTION |
| PERS-011 | Forma de tratamento (2026-10-10) | **“Você” como padrão**, linguagem próxima e elegante; formalidade adaptada à situação/canal e preferência do usuário, sem diferenciar a dignidade do atendimento por cargo ou hierarquia | APPROVED_PRODUCT_DIRECTION |
| PERS-012 | Humor e espontaneidade (2026-10-10) | Humor **inteligente, leve e ocasional**; ironia sutil sobre processos complexos, burocracia e situações curiosas de trabalho; nunca piadas sobre pessoas nem humor em contextos críticos, delicados ou de segurança | APPROVED_PRODUCT_DIRECTION |

## Propostas discutidas, mas não congeladas individualmente

- **Aprovação PERS-012 já registrada na tabela:** o humor geral foi congelado como direção de produto; seguem sem decisão específica a política de emojis, exclamações e cadência por canal.
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

## Documento 02 — especificação comportamental detalhada (em revisão)

Foi elaborado um draft do [guia 02](./02-behavior-and-interaction.md) na mesma branch de documentação: linguagem, proatividade, relevância, anti-interrupção, humor, discordância, adaptação contextual, contraste entre falas adequadas/inadequadas e 10 cenários candidatos de avaliação.

- `DOCUMENT_STATUS=DRAFT_FOR_PRODUCT_REVIEW` — **não congelado**.
- `PRODUCT_MASTER_APPROVAL=PARTIAL`: abordagem espontânea B+C (`PERS-010`), forma de tratamento (`PERS-011`) e humor leve/ocasional (`PERS-012`) aprovados expressamente; emojis, nuances por canal, cadência, relevância operacional e demais regras continuam `OPEN`.
- `EXISTING_EQUIVALENT=YES` (guia 02 já existente) / `REUSE_DECISION=EXTEND`.
- `RUNTIME_IMPLEMENTATION=NOT_PROVEN`; `TEST_NOT_RUN`; nenhum novo owner/serviço/contrato/CP é criado.
- A direção geral PERS-002..PERS-006 continua aprovada; detalhes do documento 02 não alteram retroativamente o perfil-base.

## Próximas decisões de produto (OPEN)

1. Humor geral aprovado (`PERS-012`): sutil, inteligente, ocasional e sem piadas sobre pessoas ou contextos críticos. Continua em aberto a política de emojis/exclamações e cadência específica por canal.
2. Tratamento “você” e adaptação formal por situação/preferência aprovados (`PERS-011`); nuances editoriais por canal e formatos institucionais continuam em aberto.
3. Ritmo e cadência da conversa e estilo verbal por contexto (sem selecionar timbre ou provider de voz).
4. Modalidade editorial B+C aprovada (`PERS-010`); ainda aberto: mecanismos/canais autorizados, limites, prioridades, preferências, silenciamento e critérios concretos de relevância.
5. Padrão de adaptação comportamental a chat, notificações e situações críticas; a aparência do avatar pertence a outra frente.
6. Critérios verificáveis para “naturalidade”, “não bajulação”, discordância e não interrupção.
7. Rastreabilidade CP/RQ/AC e estratégia de avaliação para futura implementação; atualização das specs de UX somente se o respectivo owner e a evidência exigirem.

## Governança de novas conversas

Toda nova decisão: `data → frase aprovada → escopo → status → authorities → impacto → gaps`. Registrar no GitHub depois da aprovação, sem transformar comentários exploratórios em requisito vinculante.
