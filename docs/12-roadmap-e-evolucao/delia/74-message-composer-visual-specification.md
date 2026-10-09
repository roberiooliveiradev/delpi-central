# DÉLIA — Especificação visual do Message Composer

**Status:** `APPROVED_PRODUCT_UX_DIRECTION` — direção visual expressa pelo Product Master; documento de design, não evidência de implementação nem aceite de runtime.  
**Escopo:** componente de envio de mensagem do MFE standalone `plugins/delia`, na página `/apps/delia` e no dock global do Portal.  
**Autoridade de base:** [73 — Identidade visual chat-first](./73-chat-first-visual-identity-and-message-anatomy-specification.md) → [69 — Experiência conversacional](./69-conversation-experience-ux-wireframes-and-activity-plan.md) → [09 — UX](./09-ux-copilot.md).  
**Nome canônico:** `Message Composer` — alias PT-BR: *Componente de envio de mensagem*.

## 1. Objetivo

Formalizar a direção visual e comportamental do Message Composer: a peça única de entrada de linguagem natural da conversa com a DÉLIA, clean e chat-first, integrada ao fluxo da conversa — nunca um formulário corporativo separado nem um card destacado do restante da página.

Este documento descreve a intenção visual. Comportamentos de contrato (payload, confirmação governada, contexto de turnos) pertencem às autoridades de backend/presentation já vigentes e **não são alterados** por esta especificação.

## 2. Papel na experiência

- Entrada principal e única de intenção do usuário para a conversa.
- Linguagem natural primeiro: sem seletores, sem modos, sem catálogos técnicos.
- Parte visual da conversa: alinhado à coluna de mensagens, ancorado na base da área de conversa.
- Mesma peça conceitual em página completa e dock; diferença apenas de densidade.

## 3. Princípios visuais

- **Clean e leve:** superfície única; nada de card dentro de card.
- **Chat-first:** a leitura dominante é a conversa; o composer acompanha, não compete.
- **Uma peça:** container único que agrupa input e ação de envio.
- **Contemporâneo:** cantos arredondados, foco discreto, sombra mínima ou nula.
- **Honesto:** nenhum affordance visual sem capability real por trás.

## 4. O que o composer NÃO é (proibido)

- Não é um formulário separado com título, seções ou botões administrativos.
- Não é um card destacado da conversa (sem moldura pesada, sem sombra dura, sem fundo contrastante agressivo).
- Não carrega o logo DELPI nem o wordmark DÉLIA dentro do campo.
- Não exibe ações concorrentes de envio (um único destino de submit).
- Não exibe ícones decorativos de capabilities não contratadas (anexo, voz, câmera, ferramentas, web) — ver §9.

## 5. Anatomia

```text
+--------------------------------------------------------------+
|  (área opcional de ações secundárias)   [área de texto]       |
|                                      [ação de envio ▶]       |
+--------------------------------------------------------------+
        (texto auxiliar sutil, opcional)
```

| Região | Obrigatório | Descrição |
|--------|-------------|-----------|
| Container externo | **REQUIRED** | Peça única arredondada; a borda/fundo pertence ao container, não ao input. |
| Área de texto | **REQUIRED** | Multiline, auto-grow com altura máxima; sem caixa interna pesada competindo com o container. |
| Ação de envio | **REQUIRED** | Botão primário integrado à direita. |
| Ações secundárias à esquerda | **OPTIONAL** | Somente com capability real e aprovada; posição reservada no layout. |
| Texto auxiliar | **OPTIONAL** | Aviso sutil abaixo do composer; sempre secundário. |

## 6. Layout

- Composer ancorado na base da área de conversa, mesma largura/alinhamento da coluna de mensagens.
- Espaçamento interno equilibrado: input respira, botão alinha à base do input quando multiline cresce.
- O container inteiro comunica o estado de foco (ex.: anel/borda no `:focus-within`), não o textarea isolado.
- Texto auxiliar (se presente) fica fora do container, tipografia reduzida e cor secundária.

## 7. Input de texto

- **REQUIRED:** multiline com crescimento automático e altura máxima (rolagem interna após o limite).
- **REQUIRED:** placeholder discreto — recomendado `"Digite sua pergunta…"` (ou equivalente contratado por conteúdo).
- **FORBIDDEN:** borda/fundo interno duplicando o container; `resize` manual deslocando o layout da conversa.
- **REQUIRED:** `label` acessível associada (visível ou visualmente oculta conforme o layout).

## 8. Botão de envio

- **REQUIRED:** integrado dentro do container, alinhado à direita.
- **REQUIRED:** ação primária, cantos arredondados, **ícone de envio obrigatório**.
- **OPTIONAL:** rótulo textual — pode ser suprimido em larguras reduzidas (dock compacto pode usar somente ícone).
- **REQUIRED:** `disabled` quando input vazio ou envio em andamento; foco visível; nome acessível estável.

## 9. Ações secundárias (à esquerda)

- **OPTIONAL — apenas com capability real e aprovada.**
- **FORBIDDEN** inventar ícones para preencher espaço; affordance sem comportamento real é violação visual e semântica.
- Opções futuras documentadas **somente como futuro/opcional** (não descrever como comportamento atual): anexo, ditado/voz, captura de imagem — todas dependentes de contrato próprio.

## 10. Estados

| Estado | REQUIRED | Descrição |
|--------|----------|-----------|
| Idle / vazio | **REQUIRED** | Placeholder visível; envio desabilitado. |
| Focus | **REQUIRED** | Foco visível no container/anel de foco; nunca apenas mudança de cor sem contraste. |
| Typing | **REQUIRED** | Conteúdo do usuário preservado; envio habilitado quando não vazio. |
| Sending | **REQUIRED** | Input e envio desabilitados; indicador honesto (`role="status"`) sem afirmar provider/etapa. |
| Disabled | **REQUIRED** | Estados de não-uso explícitos (ex.: envio em voo). |
| Error | **REQUIRED** | `role="alert"`; **o rascunho é preservado** — erro nunca apaga o que o usuário digitou. |

## 11. Comportamentos

- **REQUIRED:** `Enter` envia.
- **REQUIRED:** `Shift+Enter` insere quebra de linha.
- **REQUIRED:** seguro para IME — `Enter` durante composição (`isComposing`) não envia.
- **REQUIRED:** envio vazio bloqueado (botão e teclado).
- **REQUIRED:** rascunho preservado em falha; envio explícito apaga o draft apenas em sucesso.
- **REQUIRED:** navegação completa por teclado; sem atalhos não documentados.
- **REQUIRED:** um único caminho de submit (botão e Enter convergem para a mesma intenção).

## 12. Variante página completa

- Composer em largura da coluna de conversa (limite de leitura da página).
- Botão pode exibir ícone + rótulo.
- Texto auxiliar sutil permitido abaixo do container.

## 13. Variante dock

- **REQUIRED:** mesma linguagem visual — não virar produto diferente.
- Mais compacto: padding reduzido; rótulo do botão pode colapsar para ícone apenas.
- Recepção minimalista acima, timeline simples, composer na base — sem card de moldura.

## 14. Acessibilidade

- **REQUIRED:** `label`/nome acessível no input e no botão de envio.
- **REQUIRED:** foco visível; operável por teclado; navegação sem mouse.
- **REQUIRED:** estados de envio e erro anunciáveis (`role="status"` / `role="alert"`), com parcimônia.
- **REQUIRED:** contraste suficiente em light e dark; estados não dependem só de cor.
- **REQUIRED:** `prefers-reduced-motion` respeitado (sem animações persuasivas).
- **FORBIDDEN:** placeholder como substituto de label; área de toque abaixo do mínimo.

## 15. Regra de branding

- **FORBIDDEN:** logo DELPI/Minha DELPI dentro do composer — a marca DELPI pertence ao chrome do Portal.
- **FORBIDDEN:** wordmark DÉLIA dentro do campo de input.
- Identidade da DÉLIA fica no cabeçalho, na recepção e nos avatares da timeline — **não no campo de entrada**.

## 16. Texto auxiliar (helper copy)

- **OPTIONAL:** aviso sutil abaixo do composer.
- Exemplo aprovado de tom: `"A DÉLIA pode cometer erros. Confirme informações importantes."`
- **REQUIRED:** visualmente secundário (cor muted, tamanho reduzido); nunca prometer nem negar capabilities.

## 17. Anti-padrões

- Card pesado/moldura ao redor do composer destacando-o da conversa.
- Formulário com título "Nova mensagem", labels verticais pesados ou validação estilo formulário administrativo.
- Ícones de anexo/voz/ferramentas sem capability real.
- Dois botões competindo de envio ou "enviar para" alternativos.
- Logo/marca dentro do input ou do botão.
- Composer que rouba a metade inferior da tela em altura fixa.
- Apagar o draft em erro ou em remount visual transitório.

## 18. Critérios de aceite visual

- [ ] Composer é peça única arredondada, integrada à base da conversa.
- [ ] Nenhum logo/marca dentro do campo ou do envio.
- [ ] Enter envia; Shift+Enter quebra linha; IME não envia.
- [ ] Envio vazio impossível; draft sobrevive a erro.
- [ ] Ícone de envio sempre presente; rótulo opcional por largura.
- [ ] Dock usa a mesma peça compactada (possível ícone-only).
- [ ] Estados idle/focus/typing/sending/disabled/error distinguíveis sem cor única.
- [ ] Nenhum affordance de capability não contratada.
- [ ] `presentation.v1`, confirmação governada e contrato HTTP inalterados por esta spec.

## 19. Relação com decisões anteriores

- Refina o §"Composer" do doc 69 e a anatomia chat-first do doc 73, no nível de componente.
- Consistente com as decisões S2 (composer único página+dock, honesto, sem affordances falsas) e S3 (chat-first, sem cards pesados, identidade DÉLIA fora do campo).
- Imagens conceito produzidas na coordenação (chat moderno, input arredondado com envio integrado) são referência de direção, não contrato de pixels; em divergência, esta especificação textual vence.

## 20. Limites desta especificação

- Documento visual; não autoriza por si só implementação, nova capability, alteração de contrato ou avanço de fase.
- Ações secundárias (anexo, voz, captura) permanecem **futuro/opcional** até contrato próprio.
- Texto auxiliar é opcional e deve seguir a linha honesta da plataforma; não é promessa de qualidade.
