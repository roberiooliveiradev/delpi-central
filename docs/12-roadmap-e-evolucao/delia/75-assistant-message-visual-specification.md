# 75 — Especificação Visual da Mensagem da Assistente (DÉLIA)

## Status

- **Status:** implementado (v1) — `IMPLEMENTADO`
- **Data:** 2025 (sessão de implementação)
- **Task:** `DELIA-UX-ASSISTANT-MESSAGE-COMPONENT-FULL-IMPLEMENTATION-01`
- **Componente:** `DeliaAssistantMessage` (`plugins/delia/src/ui/DeliaAssistantMessage.tsx`)
- **Escopo:** apresentação da resposta da DÉLIA na timeline. Sem alteração de backend, contratos, Portal, Composer, recepção ou arquitetura de orquestração.

## Objetivo

Definir e registrar a anatomia real implementada do componente visual responsável por renderizar cada resposta da DÉLIA na timeline conversacional, alinhado à direção chat-first aprovada (doc 73) e aos conceitos visuais produzidos.

## Papel na experiência

O componente é a unidade de resposta da conversa. A `ConversationTimeline` permanece responsável exclusivamente pela **ordem dos turnos**; o `DeliaAssistantMessage` é responsável exclusivamente pela **apresentação de uma resposta DÉLIA**. O turno do usuário permanece inline na timeline (bolha leve à direita).

## Princípios visuais

1. **Chat-first, não dashboard** — a resposta é texto aberto integrado à conversa, sem card pesado.
2. **Identidade DÉLIA** — ícone `Sparkles` (mesmo glyph do launcher/dock do Portal) + rótulo "DÉLIA". **PROIBIDO** `DelpiLogoMark` ou logo Minha DELPI como avatar.
3. **Hierarquia clara** — o texto da resposta é o elemento principal; metadados são subordinados.
4. **Proporcionalidade** — estados de exceção recebem destaque proporcional; respostas normais permanecem leves.
5. **Mesma linguagem** — página completa e dock compartilham o mesmo componente responsivo.

## Anatomia implementada

```text
[Sparkles]  DÉLIA            [copy — visível no hover/focus]

            Conteúdo da resposta em texto legível
            (parágrafos e quebras preservados verbatim)

            ⚠ [Badge semântico, se aplicável]

            ▸ Orientação da fonte (owner_hint, quando presente)

            fonte: DELPI/HTTP · classificação: OBSERVATION · limitações: …

            [Confirmar] [Cancelar]  ← apenas com confirmation_request válido
```

| Elemento | Obrigatório | Notas |
| --- | --- | --- |
| Avatar `Sparkles` em disco accent | sim | identifica o autor; decorativo (label texto adjacente) |
| Rótulo "DÉLIA" | sim | head row acima do conteúdo |
| Ação "Copiar resposta" | sim | ghost icon, `aria-label` dinâmico ("Copiar resposta" → "Resposta copiada"); somente conteúdo visível; degrada se clipboard indisponível |
| Corpo textual | sim | `white-space: pre-line`; texto verbatim, nunca reinterpretado |
| Linha de estado semântico | condicional | ícone contextual + `StatusBadge`; **ausente em RESULT** |
| Owner hint | condicional | parágrafo discreto; deduplicado do conteúdo via `dedupeOwnerHintContent` |
| Meta row | condicional | `aria-label="Detalhes da resposta"`; provenance + classificação epistêmica + limitações |
| Confirmação governada | condicional | Confirmar (primary)/Cancelar (secondary) em `role="group"` |

## Estados semânticos (vocabulário fechado `presentation.v1`)

| `message_kind` | Badge | Ícone | Ênfase |
| --- | --- | --- | --- |
| `RESULT` | nenhum | — | resposta leve, sem indicador |
| `CLARIFICATION_REQUIRED` | "Esclarecimento necessário" | `CircleAlert` | warning |
| `CONFIRMATION_REQUIRED` | "Confirmação pendente" | `ShieldCheck` | warning + controles governados |
| `WRITE_REJECTED` | "Operação recusada" | `OctagonX` | error |
| `AUTHZ_DENIED` | "Acesso não autorizado" | `Lock` | error |
| `SOURCE_UNAVAILABLE` | "Fonte indisponível" | `CloudOff` | error |
| `PRECONDITION_REQUIRED` | "Pré-condição pendente" | `TriangleAlert` | warning |
| desconhecido | nenhum | — | fallback neutro, conteúdo renderizado |

Regras: o estado deriva **somente** do `presentation` validado pelo adapter — nunca do texto. `RESULT` nunca recebe badge de sucesso fictício. Ícones restritos aos exports confirmados do lucide-react instalado.

## Provenance

Quando `groundingStatus === "GROUNDED"` e há provenance real, a meta row exibe `fonte: {specialist_id}/{protocol}` (maiusculizado). **PROIBIDO**: inventar fonte por heurística, exibir IDs de MCP/control-plane, ou tratar provenance como autorização. `NON_GROUNDED` exibe "sem fonte vinculada". Classificação epistêmica (`OBSERVATION`, `HYPOTHESIS`, etc.) é exibida verbatim — não é indicador de confiabilidade absoluta.

## Limitações

Valores reais de `limitations[]` são exibidos verbatim após `limitações:`, na mesma meta row subordinada. Sem explicações inventadas, sem ocultação.

## Confirmação governada

- Controles existem **somente** com `confirmation_request` válido, não respondido e sem loading.
- `Confirmar` envia `decision = CONFIRM`; `Cancelar` envia `REJECT` — ambos com `proposal_digest`, `preview_fingerprint` e `session_id` **verbatim** via callback existente.
- Digests são eco de transporte — nunca renderizados.
- `allowed_interactions` é ignorado para inferência de permissão.
- Confirmação ≠ autorização; nenhum clique contorna AuthZ/Policy/Decision.

## Responsividade

- **Página completa:** coluna da timeline, meta row com wrap, sem largura fixa.
- **Dock/narrow (≤640px):** mesma anatomia, quebra de linha garantida (`min-width: 0`, `flex-wrap`, `overflow-wrap` no corpo).
- Um único componente responsivo — **PROIBIDO** variante separada para dock.

## Acessibilidade

- Estrutura semântica dentro de `role="log"` na timeline (ordem preservada).
- Avatar decorativo (autor identificado por texto adjacente).
- Estados comunicados por ícone + texto — nunca só por cor.
- Ação de cópia com `aria-label` e `title` dinâmicos, focus-visible visível.
- Meta row com `aria-label` identificando a região.
- Conteúdo hostil permanece texto inerte — nenhum HTML executável.
- `prefers-reduced-motion` respeitado (transição da ação desligada).

## Segurança

- Nenhum dado estruturado oculto é copiado — apenas o texto visível.
- Nenhum campo de control-plane (agent_directives, capability_surface, telemetria) é renderizado.
- Nenhuma ação inventada: sem feedback +/-, sem compartilhar, sem link para fonte sem contrato.

## Aprovado × Implementado × Planejado

| Item | Estado |
| --- | --- |
| Identidade Sparkles + label, corpo aberto, estados semânticos, provenance, limitações, confirmação, cópia | **IMPLEMENTADO** (v1) |
| Tabelas, gráficos, métricas, artifacts ricos | **PLANEJADO** — requer extensão contratual de `presentation.v1` (hoje apenas `text`/`notice`) |
| Feedback de resposta (positivo/negativo) | **PLANEJADO** — requer contrato de persistência |
| Navegação para fonte/detalhes | **PLANEJADO** — requer URL legítima publicada |
| Markdown/estruturação rica no corpo | **PLANEJADO** — requer decisão de renderer seguro |

## Referências

- Doc 69 — wireframes e plano de atividade da experiência conversacional
- Doc 70 — especificação de transparência de atividade e fontes
- Doc 73 — identidade visual chat-first e anatomia de mensagem
- Doc 74 — especificação visual do Message Composer
- Doc 38 — UX de provenance e epistemicidade
- `plugins/delia/src/api/presentation.ts` — `presentation.v1` (adapter parse-only)
- `plugins/delia/src/ui/ConversationTimeline.tsx` — responsável pela ordem dos turnos
