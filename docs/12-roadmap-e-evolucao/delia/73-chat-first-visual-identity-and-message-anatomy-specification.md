# DÉLIA — Especificação visual Chat-First: identidade, mensagens, recepção e dock

**Status:** `APPROVED_PRODUCT_UX_DIRECTION` — decisão visual expressa pelo Product Master em 2026-10-09; documento de design, não evidência de implementação nem aceite de runtime.  
**Escopo:** refinamento visual do MFE standalone `plugins/delia` na página `/apps/delia` e no dock global existente do Portal.  
**Referência Git de elaboração:** `d3f1693a0e4006228cadf9ae194350fff0d669e8` — revalidar HEAD na execução.  
**Implementação:** tarefa `DELIA-UX-S3-CHAT-FIRST-VISUAL-REFINEMENT-01` já encaminhada separadamente ao Devin; esta documentação **não substitui nem reescreve o prompt em execução**.

## 1. Autoridade, precedência e limites

Reancorar antes de implementar: Project Instructions / `.cursor` → [16 — Plano Mestre](./16-execution-master-plan.md) → [50 — Standalone](./50-standalone-copilot-application-architecture.md) → [17 — Componentes e contratos](./17-component-and-contract-map.md) → [49 — Padrões](./49-architecture-and-design-patterns-standard.md) → [51 — Integração](./51-platform-integration-baseline.md) → [52 — Bootstrap](./52-standalone-repository-and-bootstrap-plan.md) → [21 — Estado](./21-data-and-state-model.md) → [20 — Aceite](./20-testing-and-acceptance-matrix.md) → [25 — Rastreabilidade](./25-requirements-traceability.md) → arquitetura técnica → product spec → [09 — UX](./09-ux-copilot.md) → [38 — Evidence UX](./38-evidence-provenance-and-epistemic-ux.md) → [69 — Experiência conversacional](./69-conversation-experience-ux-wireframes-and-activity-plan.md) → [70 — Atividade e fontes](./70-tool-activity-and-source-transparency-ux-specification.md) → [71 — Fila e Meus Trabalhos](./71-conversation-queue-and-my-work-ux-specification.md) → [72 — Revisão de UX](./72-ui-ux-documentation-review-2026-10-09.md) → ledger.

Esta decisão **refina a direção visual da S2**, sem alterar autoria de contracts, políticas, fase, CP/RQ ou ordem do Plano Mestre. Em conflito com autoridade superior: STOP → `ARCHITECTURE_DECISION_REQUIRED`. Implementação em andamento exige comparação com o HEAD e com as mudanças concorrentes antes de integração.

## 2. Decisões visuais expressas pelo Product Master

1. **Ícone da DÉLIA, não logo DELPI.** A recepção e as respostas da DÉLIA devem usar sua identidade gráfica própria. O logo Minha DELPI permanece somente onde o Portal é owner (por exemplo, navegação global); não é avatar nem marca central da experiência DÉLIA.
2. **Chat-first, não dashboard.** Eliminar o grande card de recepção e o card-moldura de toda a conversa, além de caixas aninhadas desnecessárias. O canvas é o conteúdo da conversa.
3. **Usuário com avatar e mensagem própria.** Cada pergunta aparece numa superfície discreta de mensagem, acompanhada pelo avatar do usuário quando uma fonte legítima de identidade visual estiver disponível.
4. **DÉLIA com ícone e resposta na página.** Cada resposta aparece na sequência, identificada pelo ícone DÉLIA, com texto fluido, sem cartão de painel pesado. Preservar estados, fontes, limitações e confirmações.
5. **Mesmo padrão em página completa e dock.** O dock é adaptação compacta do mesmo MFE, não segunda implementação.
6. **Referência de experiência:** fluidez de um chat conversacional moderno, semelhante ao ChatGPT como padrão de interação, **sem copiar código, assets ou runtime** de outro produto.

## 3. Branding e fontes legítimas de identidade

**DÉLIA:** inventariar o asset/ícone já usado pelo launcher/dock da DÉLIA; `EXISTING_EQUIVALENT=TO_INVENTORY` até validação no HEAD. Prioridade: reutilizar asset institucional correto por API/asset já publicado. Não substituir por `DelpiLogoMark`, não gerar marca paralela, não adivinhar caminho de asset ou usar ícone genérico não aprovado como se fosse oficial. Se o asset legítimo não for recuperável, STOP para decisão de identidade; fallback textual “DÉLIA” pode preservar acessibilidade sem fingir branding validado.

**Usuário:** avatar somente via contexto publicado legítimo pelo Portal ou componente compartilhado autorizado. `EXISTING_EQUIVALENT=TO_INVENTORY` até descoberta do contrato. Avatar **nunca** autoriza, autentica, prova biometria ou personaliza direitos. Se imagem não estiver disponível, utilizar monograma/ícone neutro acessível e rotulado “Você”; não inferir nome, imagem ou identidade do JWT. Não acessar API de perfil inventada.

**Reuso:** inspecionar `plugins/plugin-ui`, `plugins/delia` e Portal antes de criar componentes. `REUSE_DECISION=REUSE|EXTEND|NEW` por item com owner e consumer; novos componentes só locais à DÉLIA quando realmente necessários.

## 4. Arquitetura visual do layout

### Página completa

- O Portal mantém sidebar, navegação, host e contexto; a DÉLIA ocupa o espaço útil remanescente.
- Cabeçalho discreto com ícone DÉLIA + nome, sem repetir slogans ou textos longos em cada estado.
- Área central de leitura com largura confortável, preferencialmente faixa de 680–860px como **referência a validar visualmente**, fluida em janelas menores; não restringir o canvas inteiro a um card contornado de 760px.
- Timeline scrollável ocupa o espaço entre cabeçalho e composer, sem deslocar o input ao crescerem as mensagens.
- Composer ancorado no rodapé da **área DÉLIA**, respeitando safe-area e layout do Portal; não um posicionamento fixo que sobreponha menus ou outras MFEs.
- Separadores apenas quando cumprem função; superfícies e espaçamentos criam hierarquia, não bordas pesadas.

### Dock

- Preservar moldura e controles que pertencem ao Portal; a DÉLIA não duplica fechar/expandir.
- Dentro do dock: header compacto → recepção ou timeline flexível → composer compacto ancorado.
- Zero overflow horizontal; textos e ações adaptam-se à largura real do host.
- Scroll independente da timeline; composer e confirmações permanecem visíveis e acionáveis.
- Sem duplicar o texto institucional do Portal e sem exibir “Contexto de host” como destaque de conversa; metadado técnico apenas se já houver motivo/contrato de debug autorizado.

### Wireframe indicativo — recepção (sem card externo)

```text
PORTAL (host) |      DÉLIA
              |
              |                [ícone DÉLIA]
              |        Como posso ajudar você hoje?
              |   Fontes e permissões determinam o que está disponível.
              |
              |     [ Escreva sua pergunta…         (Enviar) ]
```

### Wireframe indicativo — conversa

```text
PORTAL | DÉLIA
       |
       |                          [avatar usuário]  [pergunta discreta]
       |
       | [ícone DÉLIA]  DÉLIA
       |                Resposta fluida com parágrafos legíveis;
       |                sem card de dashboard envolvendo a resposta
       |                Estado / proveniência / limitações quando reais
       |                [revisar alteração] [confirmar] [rejeitar]*
       |
       |                   [ Composer multiline           Enviar ]
       |
       | * Somente se confirmation_request/allowed_interactions reais
```

## 5. Anatomia das mensagens

| Parte | Pergunta do usuário | Resposta DÉLIA |
|---|---|---|
| Alinhamento | Ao lado do avatar, próxima da borda direita do eixo de leitura; no dock, ajuste fluido | Alinhamento esquerdo no eixo de leitura |
| Identificação | Avatar real publicado ou fallback neutro + texto acessível “Você” | Ícone oficial DÉLIA + rótulo “DÉLIA” |
| Superfície | Bolha leve, discreta, com contraste; sem moldura aninhada | Preferencialmente resposta aberta no canvas, com separação por ritmo tipográfico; não exigir bolha ou card de fundo |
| Conteúdo | Pergunta literal, quebra de linha e wrapping | Texto contratual renderizado com quebra de linha, sem interpretar payload arbitrário como HTML |
| Metadados | Somente dados reais disponíveis | Estados semânticos, grounding, provenance, limitations, owner_hint conforme `presentation.v1` |
| Ações | Somente se existentes e autorizadas | Confirmação/rejeição estritamente por contrato governado existente |

**Regra de distinção visual:** o usuário pode usar uma bolha suave; a resposta da DÉLIA não precisa ser outra caixa. Evitar “card dentro de card”, grandes contornos, sombras pesadas ou repetição de rótulos em excesso. Texto e ícones devem permanecer legíveis em alto contraste e modo escuro.

**Conteúdo longo:** respeitar parágrafos, listas e quebras sem transformar texto não confiável em Markdown executável, scripts, iframes ou ações. Texto técnico/proveniência deve ter hierarquia secundária e expansão somente se houver contrato real. Truncamento visual não pode ocultar alertas críticos nem substituir o tratamento de dados sensíveis pelo backend.

## 6. Recepção, transições e empty state

- Recepção somente enquanto a sessão em memória não tiver turnos; após o primeiro envio, substituí-la pela timeline **sem card-moldura**.
- Ícone DÉLIA no centro, título curto “Como posso ajudar você hoje?” e uma única descrição honesta.
- Texto sobre persistência (“a conversa permanece nesta tela e não é salva”) em posição discreta, sem duplicar no header e na recepção. Não prometer histórico, memória ou sincronização.
- Não apresentar sugestões ou chips de capabilities se sua disponibilidade e permissão não estiverem comprovadas.
- Motion discreto opcional; respeitar `prefers-reduced-motion`; nunca impedir o envio.

## 7. Composer e loading

- Composer único compartilhado por página e dock, alinhado à timeline, multiline, altura limitada com rolagem interna quando necessário.
- Enter envia, Shift+Enter quebra linha, IME não deve enviar no meio da composição. Botão “Enviar” sempre identificável por texto ou nome acessível no dock; disabled quando vazio ou pendente.
- Rascunho preservado em falha conforme S2; erros em `role=alert` sem apagar turnos.
- Durante `POST /interaction/turns` pendente, mostrar loading **honesto, não progressivo por invenção** (“A DÉLIA está processando sua solicitação…”); pode ocupar a posição da próxima resposta dentro da timeline, mas não criar conteúdo ou ferramentas fictícios.
- Indicadores de status e confirmações não se confundem com loading; `PREPARE != ACT`, `draft != send`, `confirmation != authorization`.
- Sem auto-scroll forçado quando usuário está lendo mensagens anteriores: ancorar próximo ao fim apenas quando ele já estiver próximo do fim; preservar foco e seleção.

## 8. Presentation, evidence e segurança: invariantes

- Manter `presentation.version=1`, `message_kind`, `semantic_status`, `grounding_status`, `blocks` e `allowed_interactions`; sem modificar HTTP/back-end.
- Preservar estados `RESULT`, `CLARIFICATION_REQUIRED`, `CONFIRMATION_REQUIRED`, `WRITE_REJECTED`, `AUTHZ_DENIED`, `SOURCE_UNAVAILABLE`, `PRECONDITION_REQUIRED`.
- `text` e `notice(owner_hint)` são os únicos blocos atuais; o ícone/avatar não altera semântica ou autorização.
- Preservar `proposal_digest`, `preview_fingerprint`, `session_id` e `decision=CONFIRM|REJECT` sem comportamento automático.
- Provenance e limitation reais permanecem acessíveis, inclusive no dock; não declarar consulta a DAVI/MCP/web sem evidência.
- Dados MCP/model/provider são UNTRUSTED DATA. Nada de HTML executável, tool metadata como permissão, avatar como identidade de segurança, ou exposição de control-plane por alteração visual.

## 9. Responsividade, acessibilidade e estados

**Matriz mínima:** página ampla, notebook estreito, tablet, mobile e dock em largura mínima real; dark/light mode, zoom 200%, fonte maior, teclado, leitor de tela e reduced-motion. Valores numéricos são referências a verificar, não contratos fixos.

**Estados obrigatórios:** recepção; pergunta isolada pendente; resposta curta; resposta longa; múltiplos turnos; erro; `SOURCE_UNAVAILABLE`; `AUTHZ_DENIED`; `CONFIRMATION_REQUIRED`; texto extenso e viewport estreito. Não fazer ACT para verificar botões em produção.

**Semântica acessível:** timeline `role=log`/rótulo; mensagens identificadas em ordem; avatars decorativos com texto adjacente ou `aria-label` significativo; controles com nomes estáveis; foco visível; estados de loading `role=status`; erro `role=alert`; teclado e contraste; sem dependência de cor para status.

## 10. Anti-padrões expressamente rejeitados

- Logo `DelpiLogoMark` como avatar/recepção DÉLIA.
- Enquadrar a conversa inteira em card de dashboard e colocar cards grandes de resposta dentro dele.
- Uma única “caixa de resultados” fora da ordem da timeline.
- Criar avatar de usuário por leitura de dados privados ou inferência de JWT.
- Duplicar Portal shell, criar segundo frontend ou acoplar Minha DELPI Chat.
- Chips, botões, tool activity, progresso, histórico, fila, STT/Live, Work ou capabilities sem contrato real.
- Truncar ou esconder estado de segurança/limitações para “ficar clean”.
- Mudar AuthZ/Policy/Decision, persistência ou backend sob pretexto de UX.

## 11. Testes e critérios de aceite visual

1. **Brand:** nenhum `DelpiLogoMark` na recepção ou mensagens DÉLIA; ícone oficial DÉLIA real, comprovado, ou bloqueio explícito para decisão de asset. O branding do Portal continua intacto.
2. **Recepção:** sem card externo pesado; conteúdo centrado no canvas; uma mensagem explicativa e composer funcional.
3. **Timeline:** pergunta real com avatar do usuário e bolha discreta; resposta real com ícone DÉLIA e texto aberto; ordenação de turnos intacta.
4. **Estados S1:** provenance, epistemic status, owner_hint e limitações continuam visíveis sem duplicação; confirmações governadas continuam funcionais.
5. **Dock:** não há overflow horizontal ou botão inacessível; composer ancorado, leitura e scroll independentes.
6. **Responsivo:** página completa, dock, viewport estreito e zoom alto verificados em navegador real, além de testes estruturais.
7. **Loading/erro:** mensagem honesta enquanto request pendente; rascunho preservado após falha.
8. **Segurança:** nenhuma nova chamada/backend/escopo ou mecanismo de autorização; sem controles de ACT inventados.
9. **Testes:** unit/integration, typecheck, build/federation, evidência visual real e regressão S1/S2 no SHA/config da entrega.
10. **Release:** implementation → testes → commit isolado → push fast-forward em main → verificação GitHub, sujeitos aos gates; deploy e aceite independente separados.

Classificar resultados como `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`, sem converter documentação em runtime `PASS`.

## 12. Handoff para implementação já em curso

O Devin deve tratar esta especificação como **detalhamento da decisão visual de produto**, sem usar sua criação para aumentar escopo, alterar arquivos já em conflito, simular contratos ou pular a reancoragem. Se houver diferença material entre o prompt S3 em execução e este documento, registrar `EXECUTION_DRIFT` e retornar à coordenação; não reconciliar silenciosamente.

**Status de execução desta documentação:** `DOCUMENTED`; implementação S3 `IN_PROGRESS_BY_USER_REPORT`; código/testes/deploy S3 **não atestados por este registro**. `C3_EXECUTED=NO`, `C4_AUTHORIZED=NO`, `C5_AUTHORIZED=NO`, `PRODUCTION_READINESS=NOT_PROVEN`. Próximo trabalho/aceite seguem Plano Mestre e ledger do HEAD real.


## 13. ConversationUserMessage — chrome compartilhado aceito (2026-10-16)

**Task:** `DELIA-UX-CONVERSATION-USER-MESSAGE-FULL-IMPLEMENTATION-01`.  
**Estado factual:** `ACCEPT` no escopo visual corrente; implementação mergeada em `main` pelo PR #76. O componente público `ConversationUserMessage` vive em `plugins/plugin-ui` e é consumido por `plugins/delia`.

- **O que representa:** um turno produzido pelo usuário dentro da conversa.
- **Aparência:** alinhado à direita; bolha leve e discreta; rótulo fornecido pelo consumer (na DÉLIA, “Você”); avatar à direita; texto literal com quebras preservadas e wrapping seguro.
- **Quando aparece:** somente para turnos `role="user"` que já pertencem à timeline.
- **Quando não aparece:** não é placeholder, loading, estado semântico, confirmação, erro ou resposta da DÉLIA.
- **Owner visual:** `plugin-ui`. O componente possui apenas chrome, slots, densidade, responsividade e acessibilidade de apresentação.
- **Owner de identidade/conteúdo:** DÉLIA/Portal/Core nos contratos existentes. `ConversationTimeline` fornece o conteúdo original, “Você” e `UnifiedAvatar(kind="person")` com imagem/fallback já resolvidos.
- **Não representa:** autenticação, autorização, identidade de segurança, persistência, ordenação da conversa ou permissão de agir.
- **Acessibilidade:** `role="log"` permanece exclusivamente na timeline; o componente não cria live region ou wrapper focável. Com autor visível, o wrapper do avatar é decorativo para evitar anúncio duplicado.
- **Conteúdo:** React text permanece inerte; `white-space: pre-wrap` e `overflow-wrap: anywhere`; nenhum HTML/Markdown arbitrário é executado.
- **Reuse gate:** `UnifiedAvatar=REUSE`; `MessageThread=PARTIAL/DO_NOT_REUSE`; `EntityAvatarLabel=PARTIAL/DO_NOT_REUSE`; `ConversationUserMessage=NEW`.
- **Evidência atual:** testes direcionados e suíte DÉLIA passaram; build/federation passaram; browser QA real confirmou full page, light/dark, 320/420px, zoom 200%, múltiplos turnos e avatar real. Nenhum overflow visual material foi observado.

## 14. Inventário canônico dos componentes conversacionais já implementados

Esta seção registra **significado de produto + aparência + fronteira de responsabilidade** dos componentes atualmente usados na experiência conversacional. Ela não substitui o catálogo técnico do `plugin-ui`, os testes nem as specs temáticas detalhadas; serve como índice semântico para evitar que componentes visuais adquiram autoridade indevida.

| Componente | O que representa | Aparência / anatomia esperada | Quando aparece | O que NÃO representa | Owner visual / consumer | Estado |
| --- | --- | --- | --- | --- | --- | --- |
| `ConversationWorkspace` | Shell visual da conversa | header leve + body rolável com coluna de leitura + footer ancorado; sem card pesado | em toda superfície conversacional full-page/dock | sessão, runtime, auth, capability, decisão | `plugin-ui` / DÉLIA | `IMPLEMENTED` |
| `ConversationHeader` | Identificação leve da superfície | título curto, subtítulo opcional, leading/actions opcionais; hierarquia subordinada à conversa | topo do workspace | navegação global, model picker, status online, auth | `plugin-ui` / DÉLIA | `IMPLEMENTED` |
| `UnifiedAvatar` | Identidade visual de DÉLIA ou pessoa | DÉLIA: círculo azul + Sparkles; pessoa: foto publicada → iniciais → UserRound fallback; motion apenas em estado real | recepção, turnos, header/contextos permitidos | autenticação, autorização, biometria, emoção, confiança | `plugin-ui` / DÉLIA+Portal/Core publicam dados legítimos | `IMPLEMENTED` |
| `MessageComposer` | Entrada de linguagem natural do usuário | superfície única arredondada, textarea multiline, toolbar inferior, contador/ação somente quando reais | footer da conversa | API client, persistência, permissão, capability picker | `plugin-ui` / `DeliaComposer` | `IMPLEMENTED` |
| `ConversationUserMessage` | Turno do usuário | alinhado à direita, bolha suave, “Você”, avatar à direita, texto literal | turnos `role=user` | identidade lookup, ordenação, auth, estado semântico | `plugin-ui` / `ConversationTimeline` | `ACCEPT` |
| `DeliaAssistantMessage` | Turno de resposta da DÉLIA | alinhado à esquerda, avatar DÉLIA, resposta aberta no canvas; atividade/status/evidência/ações subordinadas | turnos `role=delia` | timeline, backend authority, autorização | DÉLIA; compõe primitives `plugin-ui` | `IMPLEMENTED` |
| `ConversationStatus` | Estado semântico estático da resposta | ícone decorativo + `StatusBadge` canônico, inline e proporcional | quando `presentation.message_kind` mapeia para estado não neutro | loading, atividade, erro HTTP, autorização, confirmação | `plugin-ui`; DÉLIA decide label/tone/exibição | `IMPLEMENTED` |
| `GovernedConfirmation` | Pedido explícito de decisão do usuário sobre proposta governada já existente | superfície inline com título/contexto/preview seguro + “Cancelar” e “Confirmar” | somente com `confirmationRequest` válido e ainda não respondido | permissão, AuthZ, ACT, sucesso, postcondition | `plugin-ui`; DÉLIA/backend possuem contrato e callbacks | `IMPLEMENTED` |
| `MessageActionBar` | Ações secundárias sobre mensagem já renderizada | barra discreta abaixo da mensagem; hover/focus no desktop, sempre acessível em touch | quando o consumer fornece ação real (hoje, copiar resposta) | ação de negócio, PREPARE/ACT, confirmação, autorização | `plugin-ui`; DÉLIA possui comportamento da ação | `IMPLEMENTED` |
| `ConversationError` | Falha real da interação e caminho de recuperação | aviso inline discreto no footer, acima do composer; ícone de alerta, título curto e descrição opcional; action é capability visual opcional, não habilitada genericamente na DÉLIA | falha de transporte/runtime/pré-requisito da interação que não produziu turno autoritativo | `SOURCE_UNAVAILABLE`, `AUTHZ_DENIED`, `WRITE_REJECTED`, loading, capability activity, autorização ou outcome | `plugin-ui` visual; DÉLIA owner do erro/draft e de qualquer política de replay | `IMPLEMENTED / ACCEPTED_CURRENT_SCOPE` |

### 14.1 Regras de aparência transversais

- **Chat-first:** usuário à direita em bolha leve; DÉLIA à esquerda com resposta aberta. Não espelhar os dois lados como cards equivalentes.
- **Hierarquia:** conteúdo conversacional é primário; atividade, estado, evidência, confirmação e ações são subordinados.
- **Página e dock:** mesma composição e mesmos componentes; o dock reduz densidade, não cria segunda implementação.
- **Tema:** usar tokens `--delpi-ui-*`/Portal; light e dark preservam forma e significado.
- **Responsividade:** sem largura fixa de viewport, sem overflow horizontal, wrapping seguro e zoom alto utilizável.
- **Acessibilidade:** um `role="log"` pertence à timeline; estados/erros/ações usam semântica própria apenas quando necessária; não criar live regions redundantes.
- **Motion:** decorativo e factual, sempre reduzível; animação nunca significa “autorizado”, “executando ACT” ou “pensando”.
- **Segurança:** frontend apresenta estado; não cria permissão. `confirmation != authorization`, `PREPARE != ACT`, avatar != identidade de segurança, sucesso técnico != outcome.

### 14.2 Regra documental para próximos componentes

Nenhum novo componente conversacional é considerado documentalmente fechado sem registrar, no mínimo:

1. o que representa;
2. quando aparece e quando não aparece;
3. anatomia/aparência;
4. estados e variantes;
5. full-page/dock e light/dark;
6. acessibilidade;
7. owner e consumer;
8. o que o componente explicitamente **não** decide;
9. entrada no catálogo `plugin-ui`, quando compartilhado;
10. status de implementação e evidência de teste/Browser QA.

Documentação descreve intenção e estado factual; não cria capability, permissionamento ou avanço de fase.
