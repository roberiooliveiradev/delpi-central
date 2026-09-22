# Estudo — formatação e mídia nos compositores ricos

> **Status:** diagnóstico (22/09/2026). **Não autoriza implementação.**
> **Owner:** `@delpi/plugin-ui` (kit). Consumidores: helpdesk (`RichTextEditor`) e salas (`MentionComposer`).
> **Restrição:** este documento descreve o comportamento em termos Delpi (seleção, bloco, objeto inline, Range). Não cita produtos de editores externos.

Este arquivo é a authority do diagnóstico de formatação fora do trecho e de colar/redimensionar imagem nos dois compositores. Plano em `.cursor/plans` não substitui este texto.

## 1. Ledger

| RQ | Requisito | Estado neste estudo |
|---|---|---|
| RQ-01 | Revisar os dois componentes | ATENDIDO — inventário §2 |
| RQ-02 | Helpdesk não anexa imagem ao colar print | ATENDIDO — causas P1–P4 §4 |
| RQ-03 | Qualquer formatação cai na linha/bloco, não no trecho | ATENDIDO — classe H1–H5 §3 |
| RQ-04 | Estilo no Range; colar e redimensionar imagem no fluxo | ATENDIDO — modelo §5 |
| RQ-05 | Fluxo centralizado texto / imagem / objeto futuro | ATENDIDO — contrato §5–§6 |
| RQ-06 | Alinhar `.cursor` | ATENDIDO — §7 |
| RQ-07 | Sem implementação neste entregável | ATENDIDO |
| RQ-08 | Docs sem marcas de editores externos | ATENDIDO |

## 2. Inventário (CONFIRMADO_NO_CODIGO)

| Superfície | Componente | Owner |
|---|---|---|
| Abrir / Responder helpdesk | `HelpdeskRichTextField` → `RichTextEditor` | kit + wiring H12 no MFE |
| Sala de interação | `MentionComposer` | kit |
| Extração de imagem do clipboard | `richTextClipboardImages.ts` | kit (já canônico) |
| Comandos de formatação | `richTextCommands.ts` + `document.execCommand` espalhado | **fragmentado** |
| Paste helpdesk | `onPasteImages` → `appendInlineImageHtml` + `onChange` | divergente da sala |
| Paste sala | `insertComposerInlineImageAtCaret` | caret + figure |

Não existe hoje um único entrypoint “recebe intenção de formatação → aplica ao alvo da seleção”. Há:

- `execRichTextCommand` / `document.execCommand` (negrito, itálico, fonte, listas, …);
- `applyRichTextFontSize` / `applyRichTextFontFamily` / `applyRichTextAlign` (APIs ad hoc);
- caminhos de imagem separados (concatenação de HTML no host vs insert no DOM).

**Classe do problema:** dispersão do *apply*, não um bug isolado de tamanho de fonte.

## 3. Formatação fora do trecho — hipóteses

### H1 — CONFIRMADO (pipeline fragmentado)

Cada botão ou atalho escolhe um caminho diferente. Qualquer formatação herda o mesmo risco de alvo errado. O sintoma “qualquer formatação na linha toda” é esperado enquanto não houver `applyFormat` único.

### H2 — CONFIRMADO (prova da classe em font-size)

Em `applyRichTextFontSize` (`richTextCommands.ts`), com `range.collapsed`:

```text
stampRichTextFontSize(bloco inteiro p / h2 / li / …)
```

O apply atual resolve o alvo como **parágrafo** por padrão no caret. `MentionComposer` e a ribbon do helpdesk reusam essa função → bug **transversal no kit**.

### H3 — MEDIA_CONFIANCA (perda de seleção)

Clique na toolbar / stepper / select → Range colapsa ou `restoreRichTextSelection` falha → comandos `inline` operam sem seleção efetiva → browser ou código caem em bloco ou pending mal aplicados. A ribbon tem `onMouseDown` + `preventDefault` nos botões ícone; controles de fonte/tamanho podem ainda roubar foco. Relato “qualquer formatação” casa com H1+H3.

### H4 — SEMANTICA block vs inline

Alinhamento e lista **devem** afetar o bloco que contém a seleção/caret. O erro é misturar `inline` e `block` no mesmo caminho sem `resolveFormatTarget`. Align-bloco **não** é bug por si.

### H5 — INFERENCIA

Negrito / cor / fonte via `execCommand` sem Range vivo = mesmo sintoma de “linha toda” ou no-op. Na implementação futura: provar selection restore + intent central **antes** de patch por botão.

## 4. Colar print no helpdesk — causas

```text
Ctrl+V print
  → RichTextEditor.handlePaste
  → richTextClipboardImages (sync e/ou async)
  → onPasteImages(files)  [se host passou callback]
  → HelpdeskRichTextField.ingestFiles
  → appendInlineImageHtml (fim do HTML)
  → onChange(value)
  → resolvedHtml muda
  → useEffect de sync: se focusedRef === true → NÃO escreve innerHTML
  → usuário não vê a imagem
```

| ID | Evidência | Veredito |
|---|---|---|
| P1 | `focusedRef` bloqueia sync de `resolvedHtml` enquanto o editor está focado (`RichTextEditor.tsx`) | CONFIRMADO |
| P2 | `appendInlineImageHtml` concatena `<p><img…></p>` no **fim** do HTML, não no caret | CONFIRMADO |
| P3 | Sala injeta no DOM no caret (`insertComposerInlineImageAtCaret`); helpdesk não | CONFIRMADO (drift de contrato) |
| P4 | Clipboard com `Files` vazio / `clipboard.read()` sem permissão | HIPOTESE_A_VALIDAR em live |

Alvo: insert de imagem entra no pipeline canônico como intenção `insert` / alvo `object`, não como concatenação no MFE.

## 5. Modelo-alvo Delpi

```text
UI (ribbon | toolbar da sala | atalho)
  → FormatIntent { kind, payload }
  → resolveFormatTarget(editor, selection)
        → { type: inline | block | object | caret, range | element }
  → applyFormat(editor, intent, target)   // ÚNICO dono no kit
  → emitChange / snapshot
```

### Tipologia de intenção

| Classe | Exemplos | Alvo correto |
|---|---|---|
| `inline` | negrito, itálico, sublinhado, riscado, fonte, tamanho, cor | só o **Range** selecionado; caret colapsado = pending para o próximo caractere/objeto, **sem** stamp do `<p>` inteiro |
| `block` | alinhamento, lista, heading | bloco que contém a seleção/caret |
| `object` | resize / alinhamento de imagem (futuros: tabela selecionada, HR, …) | o **objeto inline** sob seleção/foco |
| `insert` | colar/anexar imagem, HR, tabela | caret (ou substituição do Range); nunca append no fim do HTML do host |

Consumidores (`RichTextToolbar`, `MentionComposer`, futuros) **só emitem intent**. Não chamam `execCommand` / stamp / align direto.

Extensão: novo objeto = novo `target.type` + handler no **mesmo** módulo — sem `if` no helpdesk.

## 6. Arquitetura-alvo (documentada; não implementada)

```text
FormatIntent → resolveFormatTarget → applyFormat (kit)
  inline  → wrap/unwrap no Range | pending no caret
  block   → bloco contendo a seleção
  object  → elemento inline focado (img hoje; extensível)
  insert  → caret / replace Range (imagem, HR, …)

RichTextToolbar ──┐
MentionComposer ──┼── emitem intent; não aplicam direto
atalhos ──────────┘

HelpdeskRichTextField → onPasteImages só materializa File → URL / auth / pending;
                        insert visual = kit applyFormat(insert)
```

## 7. Matriz de paridade (estado vigente)

| Capacidade | Helpdesk / `RichTextEditor` | Sala / `MentionComposer` |
|---|---|---|
| Apply `inline` no Range | fragmentado; font-size stamp bloco no caret | mesmo font-size + `execCommand` |
| Apply `block` | align no bloco | align no bloco |
| Insert imagem no caret | host string + sync focado quebrado | insert no caret |
| Resize objeto | handles no RTE | figure + resize |
| Clipboard extract | `richTextClipboardImages` | mesmo módulo |

## 8. Diretrizes `.cursor`

| Regra | Implicação |
|---|---|
| `centralized-rules-first.mdc` | Um módulo `applyFormat` + `resolveFormatTarget`; proibido terceiro caminho no MFE |
| `plugins-reusable-components.mdc` / `platform-frontend-mfe-experience.mdc` | Owner = `plugin-ui`; helpdesk só upload / auth / pending |
| `clean-code-architecture-guardrails.mdc` | OCP: novo objeto = handler no contrato do kit, sem regra no host |
| Segurança / corpo helpdesk | Sanitizer do BFF continua autoridade; `blob:` só preview; `data-attachment-*` estáveis |
| Qualidade | Positive: seleção parcial + `inline`; sibling: `block` align; object: resize imagem; negative: caret não stamp parágrafo; paste focado visível |

**⚠ Desvio de clean architecture:** corrigir um botão ou só o MFE helpdesk → **responsabilidade canônica:** kit → **risco:** salas e helpdesk divergem; objetos futuros repetem o bug.

## 9. O que este estudo não faz

- não implementa `applyFormat` / correção de `focusedRef` / unificação de insert;
- não unifica layout das toolbars (cosmético);
- não troca o helpdesk por `MentionComposer`;
- não reabre M-23 (`@` escrita) nem inventários 12–15 como autorização de código;
- não cita marcas de editores externos.

## 10. Ponte helpdesk

Produto Meus Chamados de TI: inventário de corpo em [`docs/12-roadmap-e-evolucao/helpdesk/12-conteudo-da-mensagem.md`](../../../docs/12-roadmap-e-evolucao/helpdesk/12-conteudo-da-mensagem.md). Quando houver pedido para **implementar** o fluxo canônico, este estudo é a premissa; o código nasce no kit e o MFE só liga upload/auth.
