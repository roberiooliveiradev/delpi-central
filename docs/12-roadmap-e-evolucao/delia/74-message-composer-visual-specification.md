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


## 21. Conceito visual detalhado — composição em duas faixas

**Referência:** imagem conceitual aprovada na conversa de produto de 2026-10-09, intitulada *Compositor de pergunta da DÉLIA — modo escuro*. Ela representa o **estado-alvo de design**, não evidência de controles implementados ou liberados. A imagem é uma referência editorial: suas medidas e números não constituem contratos de runtime. Este refinamento **complementa os §§1–20**, sem habilitar automaticamente funções.

A estrutura-alvo preferida tem **uma única superfície externa com duas faixas internas**, evitando borda dupla do textarea:

```text
╭─────────────────────────────────────────────────────────────────────╮
│ Pergunte à DÉLIA…                                                │
│                                                                   │
│ (pergunta multiline; crescimento vertical controlado)       0/N   │
│                                                                   │
│ [Anexar]* [Voz]* [Ações]*   Enter envia · Shift+Enter quebra linha │
│                                                     [➤ Enviar]    │
╰─────────────────────────────────────────────────────────────────────╯
 A DÉLIA pode cometer erros. Confirme informações importantes.
```

O asterisco marca affordances **TARGET condicionados a capabilities reais**. No runtime atual, esses botões **não aparecem**, não são placeholders clicáveis e não são versões disabled para aparentar funcionalidade. Reservar *possibilidade de composição espacial* não exige reservar espaço vazio.

**Faixa superior — escrita:** campo ocupa a largura disponível, sem borda, sombra ou fundo interno competitivo; placeholder `Pergunte à DÉLIA…` recomendado como alternativa à redação anterior `Digite sua pergunta…`. Escolher uma microcopy canônica por decisão de conteúdo e aplicá-la igualmente ao dock. Quando o usuário digitar, preservar linhas e espaçamento de leitura. O contador discreto `0/N` visto na imagem é **TARGET condicionado** à comprovação de limite contratual real; `4000` na arte é ilustrativo, NÃO um limite aprovado.

**Faixa inferior — comandos:** ações secundárias ficam agrupadas à esquerda **somente quando habilitadas**, ajuda de teclado é discreta e responsiva, e envio primário à direita. A composição não deve forçar texto de ajuda a sobrepor controles. Se não houver espaço, retirar apenas a dica de teclado **visual** e preservar ajuda acessível, sem remover funções legítimas.

**Mensagem de confiança:** linha pequena abaixo, fora da superfície única; sempre honesta, com contraste e leitura acessíveis. Não duplicá-la na mesma região ou repetir texto institucional no cabeçalho e no composer.

### 21.1 Especificação de cada controle

| Controle | Elemento conceitual | Estado atual / gate | Comportamento esperado |
|---|---|---|---|
| Área de pergunta | `textarea` multiline, sem moldura interna | **REQUIRED / EXISTING** | Enter envia, Shift+Enter insere linha, IME seguro, auto-grow limitado, sem envio vazio |
| Botão enviar | Ícone paper-plane ou send; label no desktop, ícone-only com nome acessível no dock | **REQUIRED / EXISTING** | Submissão explícita pela operação já contratada; desabilitado quando vazio ou busy |
| Contador `0/N` | Canto inferior da área de texto, sem competir com conteúdo | **TARGET / TO_INVENTORY** | Exibir somente se houver limite real contratado; deve indicar o limite correto, nunca `4000` inventado |
| Anexar arquivo | Ícone de clipe no rodapé esquerdo | **TARGET / GATED** | Exige upload real, tipo/tamanho/retention/scan, autorização, consentimento, contrato e UI de erro/remover anexo |
| Entrada por voz | Ícone de microfone | **TARGET / GATED** | Exige STT contratado; ditado transcreve para rascunho editável e não envia automaticamente; Live é outro fluxo |
| Ações rápidas | Ícone DÉLIA/Sparkles com chevron | **TARGET / GATED** | Menu de ações reais/permitidas publicado por contrato; metadata/provider discovery não é permissão |
| Ajuda de teclado | Texto sutil, não controle | **OPTIONAL / DOCUMENTAL** | `Enter envia · Shift+Enter quebra linha`; ocultável visualmente em dock, sem alterar comportamento |
| Aviso de confiança | Texto secundário abaixo do container | **OPTIONAL / PRODUCT COPY** | Não exagerar certeza; informar que informações importantes precisam de verificação |
| Indicador de carregamento | Substitui ação de envio/mostra status durante request | **REQUIRED / EXISTING** | Progresso indeterminado fiel; não alegar provider, etapa ou porcentagem inexistentes |
| Erro de envio | Mensagem fora do campo | **REQUIRED / EXISTING** | `role=alert`, rascunho preservado e ação legítima de retentativa; nenhuma submissão automática |

### 21.2 Proporção e acabamento (tokens e heurísticas, não pixels congelados)

- **Container:** raio visual alto (aprox. 20–28px no desktop conceitual), superfície ligeiramente distinta do canvas, borda sutil de 1px, sem gradientes pesados; dimensões ajustadas à biblioteca/tokens reais.
- **Padding:** referência de 12–16px no dock e 16–20px na página; usar tokens disponíveis, não valores hardcoded sem justificativa.
- **Input:** altura inicial confortável (em torno de 1–2 linhas), limite de crescimento conforme S2 existente e viewport; jamais permitir que o composer consuma toda a altura disponível no dock.
- **Ações:** alvos de toque confortáveis e espaçamento consistente, sem ícones minúsculos; prioridade visual clara no envio.
- **Botão primário:** azul institucional derivado de `--primary` e contrastes de tema; preenchimento sólido, raio próprio, estado disabled honesto.
- **Foco:** contorno/ring no **container externo** por `:focus-within`, com foco individual discernível nos botões; sem contorno duplo chamativo no textarea.
- **Tema claro/escuro:** mesma anatomia. Cor e contraste sempre provenientes dos tokens do Portal ou mapeamento `--delia-*`; evitar fundos pintados com cores específicas do mockup.
- **Motion:** transições pequenas de foco/hover/estado; `prefers-reduced-motion` respeitado.

## 22. Estados detalhados da arte conceitual

| Estado | Visual obrigatório | Transição / impedimentos |
|---|---|---|
| **Idle** | Placeholder, área de escrita limpa, envio desabilitado | Não exibir ações secundárias ainda não contratadas |
| **Focus** | Contorno discreto do container; cursor no texto | Não aumentar layout abruptamente; manter foco acessível |
| **Typing** | Texto visível, botão ativo, auto-grow suave | Não perder cursor, seleção ou rascunho |
| **Multiline** | Área cresce até teto, depois rola internamente | Dock mantém timeline utilizável; Enter/Shift+Enter/IME continuam corretos |
| **Sending** | Botão busy/disabled, `role=status`, conteúdo preservado durante request | Não prometer cancelamento, não mostrar progresso fictício, não duplicar POST |
| **Error** | Erro não invasivo abaixo/adjacente, rascunho editável e reenviável | Não apagar rascunho; não exibir erro apenas por cor |
| **Unavailable/disabled** | Motivo correto e affordance inativa | Não equiparar AuthZ negada a erro de rede ou indisponibilidade geral |

**Nota de fidelidade:** a imagem mostra botões de anexo, microfone e ações rápidas em todos os estados. Essa presença gráfica **não altera o gate de produto**: enquanto os contratos forem ausentes, a UI real apresenta somente o textarea e o envio, mais affordances já legitimamente suportadas.

## 23. Página completa versus dock — matriz de composição

| Aspecto | Página completa | Dock lateral |
|---|---|---|
| Largura | acompanha o eixo da timeline e limita leitura | 100% da largura interna útil, descontados padding e chrome do Portal |
| Escrita | faixa superior ampla; pode expandir conforme conteúdo | multiline compacto com altura limitada ao espaço útil |
| Rodapé | controles secundários válidos à esquerda; envio à direita | ações secundárias reais priorizadas por espaço; envio sempre descobrível |
| Rótulo de envio | `Enviar` pode acompanhar ícone | ícone-only permitido com `aria-label="Enviar mensagem"` |
| Dica de teclado | discreta, quando há espaço | ocultável visualmente |
| Aviso auxiliar | fora do container, alinhado ao eixo | fora do container, sem ocupar área crítica |
| Altura disponível | composer ancorado dentro da área DÉLIA | composer ancorado dentro do dock; timeline preserva scroll independente |
| Safe area | respeitar viewport e estrutura do Portal | respeitar limites, rodapé e controles do Portal; não sobrepor fechar/expandir |

## 24. Gates de habilitação progressiva

A versão visual pode **prever** a posição de controles futuros, mas a implementação deve seguir a sequência obrigatória:

1. `RESPONSIBILITY → OWNER → SOURCE → CONSUMERS → CONTRACT → IMPLEMENTATION → TEST → OUTCOME`.
2. Inventariar primeiro API/capability existente, `plugin-ui`, Domain APIs, MCP/A2A, Automation Hub, ports/adapters DÉLIA e projeção do Portal.
3. Registrar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`.
4. Confirmar segurança, AuthZ live, política de dados, erros, limites, consentimento e lifecycle quando aplicável.
5. Apenas então renderizar botão **ativo**; não apresentar controle decorativo nem conectado a stub.
6. Separar `PREPARE` de `ACT`; ditado **não** envia automaticamente; upload não dá permissão de leitura; ações rápidas nunca derivam autorização de tool metadata.

**Priorização visual, não compromisso de fase:** o primeiro nível é texto + envio real; anexo, voz, atalhos/contexto e contador condicionado são oportunidades de evolução com aprovação individual.

## 25. Relação com a imagem gerada, rastreabilidade e aceite

**Conceito referenciado:** prancha “Compositor de pergunta da DÉLIA”, gerada nesta conversa em 2026-10-09, que mostra um composer escuro em duas faixas e quatro exemplos de estado (padrão, foco, digitando e enviando). A prancha não foi inserida como asset do repositório nesta atualização: documento textual representa a decisão, sem alegar publicação do PNG.

**Precedência em conflito:** autoridades canônicas > contratos existentes > decisão textual de produto documentada > arte conceitual. Uma imagem não autoriza recurso, limite, persistência, provider ou comportamento. Em contradição material: STOP, sinalizar `ARCHITECTURE_DECISION_REQUIRED`.

**Aceite adicional à seção 18:**
- [ ] Composer possui duas faixas visuais **dentro da mesma superfície**, sem textarea em card interno.
- [ ] A área principal de digitação domina visualmente; nenhum logo ocupa o campo.
- [ ] A linha de comandos reserva hierarquia para envio; ícones futuros só aparecem se tiverem operações aprovadas.
- [ ] O contador não exibe limite fictício; sua ausência é correta enquanto o limite não estiver provado.
- [ ] Botão envia somente conteúdo real, por um caminho de submit; busy evita POST duplicado.
- [ ] Idle/focus/typing/multiline/sending/error são visual e semanticamente testáveis.
- [ ] Layout não sobrepõe dock, timeline nem Chrome do Portal; zoom 200%, mobile e modo escuro são testados.
- [ ] Não há upload, STT, Live, menu de ações, histórico ou status de execução simulados.
- [ ] Unit/integration tests, typecheck, build e evidência em navegador real são atribuídos ao SHA/config testados.
- [ ] Docs não são `PASS` de runtime e não mudam fase; implementar requer task bounded autorizada.

**Status desta extensão:** `DESIGN_DOCUMENTED`; implementação dos elementos adicionais `PLANNED/TARGET` conforme contrato, sem presunção de disponibilidade.

## 26. Registro de implementação (v1)

**Task:** `DELIA-UX-MESSAGE-COMPOSER-PLUGIN-UI-FULL-IMPLEMENTATION-01`
**Commit:** `5eb401f696e38c21b69fa8666d72c5d1cbc34b3f`
**Status:** `IMPLEMENTADO` (v1) — código publicado na `main`; evidência visual em navegador real pendente de deploy (`TEST_NOT_RUN`).

### Componentes criados em `@delpi/plugin-ui` (`src/components/composer/`)

| Componente | Responsabilidade |
|---|---|
| `MessageComposer` | Composição pública: superfície única, faixa de escrita, toolbar, helper/erro fora da superfície, auto-grow, Enter/Shift+Enter/IME, bloqueio de envio vazio |
| `ComposerSendButton` | Envio primário (wrapper fino sobre `ActionButton` `variant="primary"`): label acessível honesto no sending, sem duplo submit |
| `ComposerCharacterCounter` | `n/limite` discreto — renderiza somente com `characterLimit` real informado |

### Componentes reutilizados

- `NativeTextAreaControl` — textarea nativa (borda/sombra neutralizadas pela CSS do composer).
- `ActionButton` (`variant="primary"`) — base do envio (azul institucional via tokens).
- `IconButton` — primitive oficial para futuras ações secundárias (anexo/voz/ações), quando houver contrato.
- `MentionComposer` **não** é equivalente: editor rich-text/markdown das salas de interação; `EXISTING_EQUIVALENT=NO`.

### API pública

```ts
type MessageComposerProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  inputId?: string;
  inputLabel?: string;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  loadingLabel?: string;
  helperText?: ReactNode;
  error?: string | null;
  secondaryActions?: ReactNode;
  keyboardHint?: string | null;
  characterLimit?: number;
  maxInputHeight?: number;
  sendLabel?: string;
  className?: string;
};
```

Sem tipos de negócio DÉLIA, sem permissões, sem provider ID, sem persistência própria.

### Integração DÉLIA

`plugins/delia/src/ui/DeliaComposer.tsx` virou wrapper fino: placeholder `Pergunte à DÉLIA…`, `inputLabel="Pergunte à DÉLIA"`, `helperText` de confiança, `characterLimit={INTERACTION_INPUT_CHAR_LIMIT}` (= 16384, espelho do bound real `MAX_INPUT_CHARS` imposto pelo delia-api sobre `input` — backend continua autoridade) e `className="delia-composer"` para ancoragem. Erro de envio permanece na região de alerta do `App` (anterior ao composer), não duplicado.

### Diferenças reais frente ao conceito

- **Contador:** habilitado com limite real `16384` (provado no backend); posição no canto inferior direito da faixa de escrita.
- **Toolbar:** regiões previstas (ações secundárias à esquerda via `secondaryActions`, hint central, envio à direita). Sem botões de anexo/voz/ações — nenhum contrato existe; nenhum placeholder renderizado.
- **Dock:** mesma composição; hint e rótulo do botão colapsam via CSS responsivo (`@container` + fallback de viewport), sem componente separado.
- **Temas:** mesma anatomia claro/escuro via tokens do Portal (`--delpi-ui-*` com fallback `--surface`/`--text`/`--border`/`--primary`).

### Gates preservados

Anexo, voz e ações rápidas permanecem `TARGET — CONTRACT_REQUIRED`; o contador depende de `characterLimit` explícito; nenhuma capability é inferida de provider/metadata.
