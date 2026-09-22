# Estudo — formatação e mídia nos compositores ricos

> **Status:** **implementado** (S-0 / S-F / S-P) — `formatApply.ts`, caret pending em `applyRichTextFontSize`, insert no caret (`richTextInlineImage` + `RichTextEditorHandle`), host helpdesk só materializa File.
> **Owner:** `@delpi/plugin-ui` (kit). Consumidores: helpdesk (`RichTextEditor`) e salas (`MentionComposer`).
> **Restrição:** este documento descreve o comportamento em termos Delpi (seleção, bloco, objeto inline, Range). Não cita produtos de editores externos.

Este arquivo é a authority do diagnóstico **e** da solução-alvo de formatação fora do trecho e de colar/redimensionar imagem nos dois compositores. Plano em `.cursor/plans` não substitui este texto.

## 1. Ledger

| RQ | Requisito | Estado neste estudo |
|---|---|---|
| RQ-01 | Revisar os dois componentes | ATENDIDO — inventário §2 |
| RQ-02 | Helpdesk não anexa imagem ao colar print | ATENDIDO — S-P no kit + `HelpdeskRichTextField` materializa só |
| RQ-03 | Qualquer formatação cai na linha/bloco, não no trecho | ATENDIDO — S-F via `applyFormat` / caret pending |
| RQ-04 | Estilo no Range; colar e redimensionar imagem no fluxo | ATENDIDO |
| RQ-05 | Fluxo centralizado texto / imagem / objeto futuro | ATENDIDO — `FormatIntent` + `applyFormat` |
| RQ-06 | Alinhar `.cursor` | ATENDIDO — §8 e §10 |
| RQ-07 | Sem implementação neste entregável | SUPERADO — implementação sob pedido explícito |
| RQ-08 | Docs sem marcas de editores externos | ATENDIDO |
| RQ-09 | Documentar soluções segundo `.cursor` | ATENDIDO — §9–§12 |

## 2. Inventário (CONFIRMADO_NO_CODIGO)

| Superfície | Componente | Owner |
|---|---|---|
| Abrir / Responder helpdesk | `HelpdeskRichTextField` → `RichTextEditor` | kit + wiring H12 no MFE |
| Sala de interação | `MentionComposer` | kit |
| Extração de imagem do clipboard | `richTextClipboardImages.ts` | kit (já canônico) |
| Comandos de formatação | `formatApply.ts` → `richTextCommands` | canônico (S-0/S-F) |
| Paste helpdesk | `onPasteImages` materializa File → kit `insertInlineImages` | alinhado à sala |
| Paste sala | `insertComposerInlineImageAtCaret` (+ align/font via `applyFormat`) | caret + figure |

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
| `evidence-driven-execution.mdc` / `root-cause-generalized-fix.mdc` | Corrigir a classe (pipeline), não um botão; positive + sibling + negative |
| `platform-quality-testing.mdc` / `test-and-commit.mdc` | Prova no kit + wiring dos dois consumidores |
| Segurança / corpo helpdesk | Sanitizer do BFF continua autoridade; `blob:` só preview; `data-attachment-*` estáveis |

**⚠ Desvio de clean architecture:** corrigir um botão ou só o MFE helpdesk → **responsabilidade canônica:** kit → **risco:** salas e helpdesk divergem; objetos futuros repetem o bug.

## 9. Matriz problema → solução

| ID | Problema | Solução | Owner |
|---|---|---|---|
| H1 | Pipeline fragmentado | **S-0** `FormatIntent` → `resolveFormatTarget` → `applyFormat` | kit |
| H2 | Stamp de bloco no caret (font-size) | **S-F1** `inline` no Range; caret = pending, não stamp `<p>` | kit |
| H3 | Perda de seleção na toolbar | **S-F2** restore Range + `mousedown` preventDefault em **todos** os controles de formato | kit |
| H4 | Confundir block com inline | **S-F3** `resolveFormatTarget` classifica; align/lista ficam `block` | kit |
| H5 | `execCommand` sem Range | **S-F4** UI só emite intent; apply central restaura Range antes | kit |
| P1 | Sync bloqueado com foco | **S-P1** insert no DOM no caret **ou** sync controlado que não engole insert focado | kit |
| P2 | Append no fim do HTML | **S-P2** host não monta HTML de imagem; só materializa File→URL | kit + MFE fino |
| P3 | Drift sala × helpdesk | **S-P3** um insert canônico reusado pelos dois | kit |
| P4 | Clipboard async | **S-P4** manter `richTextClipboardImages`; erro observável; sem segundo extractor | kit |

## 10. Soluções prescritas (segundo `.cursor`)

Ordem canônica:

```text
responsabilidade transversal (frontend / kit)
→ owner: plugin-ui
→ fonte: applyFormat + resolveFormatTarget
→ consumidores: RichTextToolbar, MentionComposer, HelpdeskRichTextField (wiring)
→ contrato: FormatIntent
→ implementação (só com pedido explícito)
→ positive + sibling + negative
```

### S-0 — Fonte única de apply (obrigatória antes de patches locais)

**Fazer**

1. Criar no kit (ex. `rich-text/formatApply.ts` ou evolução de `richTextCommands.ts`) o trio:
   - `FormatIntent` — `{ class: inline|block|object|insert, op, payload }`;
   - `resolveFormatTarget(editor, selection)` — devolve Range, bloco ou elemento objeto;
   - `applyFormat(editor, intent)` — único ponto que muta o DOM / pending.
2. `RichTextToolbar` e `MentionComposer` **só** chamam `applyFormat` (ou helper fino que monta o intent). Remover chamadas diretas a `execCommand` / `applyRichTextFontSize` / `applyRichTextAlign` dos consumidores.
3. Exportar pelo barrel do kit; MFE helpdesk **não** importa internals de stamp.

**Não fazer**

- `if (helpdesk)` no apply;
- segundo helper de negrito/cor só no MFE;
- “corrigir só font-size” sem passar pelo intent.

**Prova mínima:** um teste unitário do módulo: mesma intent produz o mesmo DOM em fixture compartilhada, independente de qual UI chamou.

### S-F — Formatação no trecho (H1–H5)

#### S-F1 — Classe `inline`

| Antes | Depois |
|---|---|
| Caret colapsado → stamp no `<p>` inteiro | Caret → pending format para o próximo caractere/objeto; seleção parcial → wrap/unwrap só no Range |
| `applyRichTextFontSize` especial | Vira handler de `FormatIntent { class: inline, op: fontSize }` |

Mesma regra para negrito, itálico, sublinhado, riscado, fonte, cor: **um** caminho `inline`.

#### S-F2 — Seleção estável (H3)

- Persistir Range em `selectionchange` (já existe na ribbon); **restaurar** dentro de `applyFormat` antes de mutar.
- `onMouseDown` + `preventDefault` em **todos** os controles que disparam formato (incl. stepper e select de fonte), não só botões ícone.
- Não confiar em `focus()` da toolbar sem restore.

#### S-F3 — Classe `block` (H4)

- Align, lista, heading: `resolveFormatTarget` → bloco contendo a seleção.
- Teste sibling: seleção parcial de palavra + align → afeta o parágrafo (correto); mesma seleção + negrito → só a palavra.

#### S-F4 — Sem `execCommand` solto (H5)

- Qualquer `document.execCommand` fica **dentro** do handler do intent (se ainda for necessário como primitive), nunca no click handler da UI.
- Se o primitive for substituído por Range API depois, a UI não muda.

### S-P — Colar / inserir imagem (P1–P4)

#### S-P1 + S-P3 — Insert canônico no caret

**Fazer**

1. Generalizar o insert da sala (`insertComposerInlineImageAtCaret` ou equivalente) para API do kit usável pelo `RichTextEditor`:
   - `applyFormat({ class: insert, op: image, payload: { src, attrs } })` no caret / Range.
2. No paste do RTE: após extrair `File[]` via `richTextClipboardImages`, chamar host **só** para materializar URL/pending/upload; o **insert visual** fica no kit.
3. Eliminar dependência de “atualizar `value` React + esperar useEffect” para a imagem aparecer enquanto focado (resolve P1 sem gambiarra de blur).

**Não fazer**

- Continuar `appendInlineImageHtml` como dono da posição da imagem;
- Copiar `MentionComposer` inteiro para o helpdesk;
- Segundo parser de clipboard no MFE.

#### S-P2 — Papel do host helpdesk

```text
onPasteImages / onUploadFiles
  → File → pendingId | documentId | src estável (blob só preview)
  → devolve metadados ao kit
  → kit applyFormat(insert)
```

`HelpdeskRichTextField` deixa de concatenar HTML de `<img>` no fim da string. No máximo reescreve attrs `data-attachment-*` depois do upload (já alinhado a H12).

#### S-P4 — Clipboard

- Manter `richTextClipboardImages` como única extração.
- Erro async → `onPasteImagesError` com mensagem já existente; não engolir.
- Validar live Snipping Tool / Edge como aceite (P4).

#### Objeto `object` (resize)

- Resize de imagem permanece no kit (handles já no RTE / figure na sala).
- Unificar seleção de objeto: caret/clique na imagem → target `object`; align de imagem não “vaza” para parágrafo errado (já há cuidado parcial em `findRichTextAlignBlock`).

### S-X — Extensão futura (OCP)

Novo objeto (tabela selecionada, HR, embed):

```text
1. Novo FormatIntent.op / target.type no módulo canônico
2. Handler em applyFormat
3. Teste positive + negative
4. UI emite intent — zero if no helpdesk
```

## 11. Ordem de implementação

| Ordem | Entrega | Estado |
|---|---|---|
| 1 | S-0 esqueleto `FormatIntent` + `applyFormat` | FEITO — `formatApply.ts` |
| 2 | S-F1–S-F4 toolbar + MentionComposer via `applyFormat`; caret pending fontSize | FEITO |
| 3 | S-P1–S-P3 insert imagem canônico no RTE; host helpdesk só materializa | FEITO |
| 4 | S-P4 validação live clipboard | ACEITE MANUAL (Snipping Tool / Edge) |
| 5 | verify-final: testes unitários do módulo + irmãos | FEITO (unit); live P4 pendente |

## 12. Critérios de aceite (quando implementar)

| Caso | Esperado |
|---|---|
| Positive — seleção parcial + negrito / tamanho / cor | só o trecho muda |
| Sibling — seleção parcial + align | bloco inteiro alinha (correto) |
| Negative — caret + tamanho | não stamp do parágrafo; pending ou no-op controlado |
| Object — resize imagem | handles no objeto; texto vizinho intacto |
| Paste focado (helpdesk) | imagem no caret, visível sem blur |
| Irmão — paste na sala | comportamento preservado (sem regressão) |
| Invariante | BFF sanitiza; sem secret em log; CSS só no kit |

## 13. O que este estudo não faz

- não unifica layout das toolbars (cosmético);
- não troca o helpdesk por `MentionComposer`;
- não reabre M-23 (`@` escrita) nem inventários 12–15 como autorização de código;
- não cita marcas de editores externos.
- validação live de clipboard (P4) permanece aceite manual pós-deploy.

## 14. Ponte helpdesk

Produto Meus Chamados de TI: inventário de corpo em [`docs/12-roadmap-e-evolucao/helpdesk/12-conteudo-da-mensagem.md`](../../../docs/12-roadmap-e-evolucao/helpdesk/12-conteudo-da-mensagem.md). Premissa de implementação: §§9–12 deste arquivo. Código no kit; MFE só upload/auth/pending.
