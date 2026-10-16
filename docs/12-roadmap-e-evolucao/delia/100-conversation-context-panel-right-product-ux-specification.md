# 100 — DÉLIA | ConversationContextPanel — Painel contextual direito

**Data:** 2026-10-16  
**Natureza:** especificação de produto, UX e contrato visual **somente documental**. Não autoriza runtime, migração, backend, deploy, CP ou avanço de fase.  
**Produto:** DÉLIA standalone (não é Minha DELPI Chat).  
**Base factual:** `main` no SHA `395bd45012f8b45899f07e226b6525df9e0a0c66`. Revalidar HEAD antes de implementar.  
**Autoridade:** HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs temáticas → ledger. Conflito = `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`; não reconciliar silenciosamente.  
**Propriedade:** `plugin-ui` hospeda componentes visuais reutilizáveis; `plugins/delia` compõe produto, decide estados de interface e integra contratos autorizados. Portal hospeda/navega; Core valida AuthZ; Domain APIs têm autoridade de regras/dados; DÉLIA não cria autoridade paralela.


**Posicionamento:** região **direita** opcional do layout completo [doc 98](./98-delia-full-page-three-region-layout-product-ux-specification.md). **Navegação de conversas:** exclusiva da [sidebar esquerda, doc 99](./99-conversation-sidebar-left-product-ux-specification.md).

## 1. Objetivo e princípios

`ConversationContextPanel` apresenta **informações complementares relativas ao contexto selecionado** da conversa, sem substituir a resposta principal e sem ser um segundo planner, mecanismo de autorização ou fonte de verdade. A região direita pode mostrar detalhes, evidências, atividades e funcionalidades contextuais futuras, sempre por projeções explícitas e contratos legítimos.

**Não** criar um “dashboard lateral” com dados fabricados, insights de modelo tratados como fatos, histórico de conversa duplicado, catálogo de ferramentas MCP invocáveis ou botões write sem governança.

## 2. Hierarquia e wireframe

```text
+-------------------------------------------------+
| Contexto                                    [×]  |
| [Conversa] [Mensagem]* [Atividade]*              |
|-------------------------------------------------|
| Detalhes                                        |
|  Escopo / fonte / limitações                    |
|-------------------------------------------------|
| Evidências (quando houver dados legítimos)     |
|  [fonte declarada pelo contrato]                |
|  [referência / estado epistêmico]               |
|-------------------------------------------------|
| Atividades e resultados (quando relevantes)    |
|  [steps / estado real / limitações]             |
|-------------------------------------------------|
| Ações contextuais permitidas, se contratadas   |
+-------------------------------------------------+
* tabs/sections são propostas; somente estados/sources existentes
```

- Painel aberto ocupa largura alvo ~300–380px em desktop; largura proporcional e drawer em container estreito/dock. Não sobrepor composer nem empurrar centro abaixo do mínimo legível.
- Header fixo com “Contexto”, botão fechar e, opcionalmente, etiqueta de escopo (“Nesta conversa”, “Nesta resposta”) **somente quando seleção real é conhecida**.
- Área interna de leitura tem scroll próprio; conteúdo organizado por seções com títulos pequenos, ícones discretos e divisórias sutis; não repetir lateralmente toda a resposta Markdown.
- Abas são opcionais: preferir seções verticais inicialmente; tab navigation só se volume e necessidades reais justificarem.
- Estado vazio curto e honesto; não exibir “sem evidência” como prova de inexistência global, apenas “Não há detalhes adicionais disponíveis para esta seleção”.
- Cores e surface tokens do `plugin-ui`, fontes e ícones existentes, suportando light/dark/reduced motion, sem bordas pesadas nem visual de console técnico.
- Callouts de risco/limitação, caso reais, devem ter semântica além da cor; informações internas como tokens, segredos, handles, policy internals e chain-of-thought não devem ser mostradas.

## 3. Modelo de contexto e seleção

O painel pode acompanhar:
- **Contexto da conversa atual:** visão leve de metadados *permitidos* da interação, sem inferir persistência ou identificador de sessão real.
- **Mensagem selecionada:** evidências e detalhes relativos a um turno concreto do usuário/DÉLIA, se seu contrato de projeção tiver ID e conteúdo autorizado.
- **Atividade atual:** passos/progressão de uma interação em andamento, com status observado e limites epistêmicos, sem fabricar `business outcome`.
- **Resultado específico:** bloco de evidência ou detalhe navegável apenas quando o owner publicar referência/rotas autorizadas.

A seleção deve ser **controlada pela DÉLIA** e transitória (ex.: `scope=conversation|turn|activity|none`, com `selectedTurnId` opaco quando disponível). `plugin-ui` renderiza props/projeções, sem escolher owner, derivar capabilities, chamar Domain APIs ou MCP.

Trocar seleção atualiza o conteúdo e a acessibilidade, **não** dispara ACT, não altera conversa nem apaga mensagens. Em falta de seleção/contrato, mostrar empty state neutro ou permanecer fechado.

## 4. Seções e funcionalidades previstas

### 4.1 Detalhes

- Título contextual, origem publicada, referência externa/interior segura, horário com timezone quando autorizado; sem copiar identificadores de provider diretamente na UI.
- Estado `GROUNDED|NON_GROUNDED` e limitações apenas quando dados contratuais existentes tiverem sido admitidos; nunca inferir `FACT` com base no estilo do texto.
- Evidências/ações pendentes, quando legítimas, devem permanecer visíveis no próprio turno também; o painel direito **complementa**, não move confirmação crítica para fora da conversa.

### 4.2 Evidências

- Reaproveitar a semântica existente `EvidenceDetails` do `plugin-ui`; permitir uma **projeção resumida contextual**, não uma nova engine de evidence.
- Origem/provenance, status, timestamp e referências somente de projections reais e permitidas. Links aplicam allowlist/URI seguro, auth e navigation pelo owner/host.
- Nenhuma evidência “gerada” a partir de saída do modelo, prompt, memórias ou tool metadata sem contrato/validação.
- Quando não houver evidência disponível, comunicação neutra; quando houver `UNAVAILABLE` ou `REDACTED`, respeitar semântica e autorização.

### 4.3 Atividade e resultado

- Reutilizar projeções existentes do `ActivityViewer` para passos e estados de operação visíveis ao usuário; evitar ActivityViewer paralelo ou log técnico.
- Diferenciar `running`, `completed`, `failed`, `unknown` com base na fonte, e **separar sucesso técnico de postcondition de negócio**.
- Não apresentar deltas/estatísticas/ETA inventados. Operação PREPARE/ACT e confirmações governadas devem continuar com gates no fluxo principal.
- Integrar detalhamento expandido/colapsado somente quando houver um vínculo semântico real com o turno e projeção autorizada.

### 4.4 Funcionalidades futuras

- Contexto de página/aplicação Portal publicado e minimizado, como **hint não autoritativo**, nunca AuthZ.
- Detalhes de entidade/indicador, comparação, observações e arquivos apenas com source Domain API/owner, contrato, privacy/safety e fase apropriados.
- O painel **não** é um painel de busca/histórico de conversas (sidebar esquerda), nem “Control Tower” que replana ações, nem permission broker de providers.

## 5. Interações e estados visuais

| Estado | Comportamento |
|---|---|
| `closed` | Sem coluna reservada; botão para abrir apenas quando há superfície contextual legítima |
| `open` | Painel de leitura com título e seções admitidas |
| `drawer` | Em dock/mobile, overlay acessível com foco gerido e fechamento/restauração |
| `no_selection` | Copy neutra e sem conteúdo fictício |
| `loading` | Estado loading somente para consulta realmente em curso; sem loader ornamental |
| `partial` | Conteúdo parcial identificado como tal, sem confirmação final prematura |
| `error` | Falha com mensagem/recuperação adequadas, sem vazar secrets |
| `restricted` | Superfície omitida ou redacted por fonte, sem revelar dados de terceiros |
| `stale` | Seleção já não corresponde ao turno/owner; limpar projeção e não exibir dado antigo como atual |

- Fechar painel **não cancela** a conversa, request, processamento de evidence ou operação técnica. Apenas oculta apresentação.
- Botão de abrir/fechar no `ConversationHeader.actions` ou ação contextual de mensagem devidamente autorizada. Interação não deve reexecutar tool.
- Resizer futuro opcional depende de equivalente no kit, QA e limites de largura; não criar resizable engine por conveniência.
- Persistir preferência de abertura somente por owner de settings existente/autorizado; nada de `localStorage` paralelo.
- Ao selecionar outro turno, destacar/atualizar scope de modo previsível; não anunciar conteúdo inteiro repetidamente ao leitor de tela.

## 6. Arquitetura, propriedade e reuse gate

**PROVEN:** `EvidenceDetails`, `ActivityViewer`, `ConversationStatus`, `ConversationWorkspace` e `ConversationHeader.actions` existem no `plugin-ui`. `App.tsx` já recebe projeções e mantém `turns` transientes. Isso **não prova** API de contexto ampliado nem vinculação de seleção a painel direito.

`EXISTING_EQUIVALENT=YES` para visualização de activity/evidence e chrome; `EXISTING_EQUIVALENT=TO_INVENTORY` para componente de painel direito, drawer/resizer e contratos de contexto por seleção. `REUSE_DECISION=REUSE` conteúdo projetado existente + `EXTEND/NEW_PENDING_GATE` a superfície de composição.

- **`plugin-ui`:** layout do painel, sections, badges/empty states e toggles genéricos quando necessários, render-only, event callbacks controlados.
- **`plugins/delia`:** seleciona escopo/turno, consome projeções autorizadas, decide abrir/fechar e faz binding a funções permitidas. Nunca mover política de negócio ao kit.
- **Portal/Core/Keycloak/Domain APIs:** preservam ownership de contexto, identidade, RBAC e dados; painel não infere autorização a partir de UI state ou JWT.
- **Providers/MCP/A2A:** recursos e evidência não são autoridade; metadata/result são untrusted data. Planner/decisão de DÉLIA não migram para visualização.

## 7. Acessibilidade e responsividade

- Landmark `complementary` nomeado “Contexto da conversa” apenas quando aberto; header com label claro e botão fechar.
- Keyboard para toggles, seções, controles e links; foco visível; restore focus ao disparador ao fechar drawer; trap apenas quando modal.
- Múltiplas regiões com o mesmo nome/cópia devem ser evitadas. Tab order não pode esconder controles críticos por trás do backdrop.
- Em mobile/dock o painel é drawer, não coluna estreita. Quando abrir a direita, fechar a drawer esquerda se estiver ativa, salvo justificativa UX/QA.
- 320/375/420px, zoom 200%, contraste, light/dark e reduced motion. Conteúdo textual deve quebrar linha adequadamente sem forçar horizontal overflow na conversa.

## 8. Casos de validação futura

1. Abrir/fechar painel não altera draft, turnos, scroll indevidamente, requisição nem estado de confirmação.
2. Contexto de turnos/atividades muda sem leakage de seleção anterior, inclusive quando uma mensagem foi removida/redacted.
3. Empty/loading/error/restricted/stale representam condições reais, não dados fictícios.
4. Reuso de `EvidenceDetails` e `ActivityViewer` sem duplicar lógica epistêmica/autoridade.
5. Links autorizados apenas; unknown destination é inerte; nenhum metadata de provider vira ação.
6. Acesso ao painel não dispara MCP/ACT/POST nem eleva permissões de usuário.
7. Teclado, mobile drawer, full-page/dock, temas, zoom, reduced motion e browser QA.
8. Testes unitários, integração, security negatives, build/plugin-ui + DÉLIA e Module Federation no SHA efetivo.
9. Revisão de payload/privacy, autorizações Core/Domain quando integrar dados, e aceite independente.

## 9. Estado e implementação futura

A entrega documental não cria componente, não ativa painel vazio em produção, não consome novos dados e não altera fases. Primeiro implementar **shell estrutural** sob autorização posterior, reaproveitando kit; depois seções por contratos existentes e evidência verificada, sem inventar endpoint de contexto.

```text
SPEC_STATUS = DOCUMENTED_PRODUCT_TARGET
RIGHT_CONTEXT_PANEL = NOT_IMPLEMENTED
PANEL_CONTENT_SOURCE = EXISTING_EVIDENCE_ACTIVITY_PROJECTIONS_WHEN_VALID
EXPANDED_CONTEXT_CONTRACTS = TO_INVENTORY
RIGHT_PANEL_BUSINESS_ACTIONS = NOT_AUTHORIZED
REUSE_DECISION = REUSE_PROJECTIONS + FUTURE_GATE_FOR_SHELL
TESTS = TEST_NOT_RUN
PHASE_PROGRESSION = NONE
```

## Registro de implementação visual bounded — 2026-10-16

`ConversationContextPanel` foi criado em `plugin-ui` e importado por `DeliaConversationPage` na região direita, com seções **Detalhes**, **Evidências** e **Atividades** e toggle de abertura/fechamento no shell. Os slots `details`, `evidence` e `activities` aceitam apenas projeções read-only publicadas pela DÉLIA. Na ausência de contrato/dados, renderizam estados neutros, sem inventar evidence nem activity; não há fetch, ACT, planner ou Domain authority na UI. `EXISTING_EQUIVALENT=YES` para primitives e presentations existentes; `REUSE_DECISION=EXTEND` para composição. Testes/build/browser `TEST_NOT_RUN`; aceite independente `PENDING`; fases inalteradas.

## 10. Revisão visual R1 — painel contextual clean e progressivo (2026-10-16)

**Evidência:** screenshot real e `ConversationContextPanel.tsx` no `plugin-ui`, HEAD `18583359972f22ff76041859740307f401628933`. O layout mostra corretamente as três seções, mas a apresentação atual empilha mensagens redundantes de ausência de dados, criando aparência de checklist administrativo. Esta especificação **substitui os alvos visuais conflitantes** acima e preserva os limites canônicos de evidência/atividades. Ver [98 §12](./98-delia-full-page-three-region-layout-product-ux-specification.md).

### 10.1 Estrutura moderna, clara e não redundante

```text
  Contexto                              [fechar ×]

  [i]  Detalhes               [expansão se aplicável]
       (conteúdo real quando selecionado)

  [documento] Evidências
       (projeções autorizadas reais)

  [pulso] Atividades
       (etapas e estados realmente observados)

  [se não houver NENHUMA projeção em todo o painel]
       Selecione uma mensagem para ver mais informações.
       (apenas UMA orientação geral, sem avisos por seção)
```

- **Cabeçalho:** “Contexto” como heading de painel, **não** repetir “da conversa” por extenso quando o espaço for pequeno; texto acessível da região pode continuar “Contexto da conversa”. À direita, **um** botão de fechar; nenhum segundo `Fechar contexto` no header central quando o painel estiver aberto.
- **Seções:** Detalhes, Evidências e Atividades são itens de navegação/agrupamento elegantes, com ícones `Info`, `FileText` e `Activity`, texto compacto e alinhado; evitar grandes divisórias obrigatórias entre três caixas vazias. Em expansão com conteúdo, cada seção é painel semântico legível com respiro adequado.
- **Zero projeções em todo painel:** preferir **um empty state único**, neutro e de baixo peso visual (ex.: “Selecione uma mensagem para ver mais informações.”); não exibir repetidamente “Nenhum detalhe... / Nenhuma evidência... / Nenhuma atividade...” por padrão. Não dar a entender que algo foi consultado ou que ausência é global.
- **Se algumas seções têm dados:** renderizar apenas as seções disponíveis, ou mostrar rótulos das restantes em estado discreto/indisponível conforme UX acordada. Não duplicar `EvidenceDetails` e `ActivityViewer` completos: apresentar uma projeção resumida e affordance para abrir detalhes somente se vinculados a turno/seleção legítimos.
- **Profundidade visual:** mesma família de surfaces que o centro com separação hairline e baixa diferença tonal; header compacto alinhado ao da sidebar e do centro. Não utilizar painel azul destacado como quadro independente, bordas pesadas, cards encavalados ou estados de loading ornamentais.
- **Typography / scale:** headline 13–14px, ícone 16–18px, texto secundário 12–13px, espaçamentos 12–16px entre grupos, padding 16–20px. Valores propostos para serem harmonizados aos tokens realmente existentes em `plugin-ui`.
- **Conteúdo:** textos podem quebrar linha, snippets/IDs nunca vazam secrets/handles; overflow vertical próprio; sem horizontal scrolling da página; links apenas se publicados/autorizados.
- **Cores:** semantic tokens do Portal e `plugin-ui`, contraste e foco conforme kit; selected/expanded não dependem só da cor.

### 10.2 Comportamento dos grupos

- **Detalhes:** informação contextual de conversa/turno **somente quando real e admitida**; não apresentar fictícios escopo, IDs de sessão, datas ou persona/profissional.
- **Evidências:** projection resumida usando a semântica existente de `EvidenceDetails`; explicitar epistemic class/provenance apenas quando o owner fornecer; nunca converter saída de modelo/MCP em FACT.
- **Atividades:** resumir passos reais do `ActivityViewer`, distinguindo pending/complete/error e o limite de business outcome; não gerar timeline paralela.
- **Controles expande/colapsa das seções:** opcionais e subordinados; ao usar disclosure, `aria-expanded`/keyboard/tab order corretos; não dar aparência de botão clicável sem conteúdo/ação.
- **Seleção:** uma mensagem/entidade só se torna contexto ativo quando o consumer tiver contrato/projeção; caso contrário o painel é um container vazio honesto e elegante.
- **Abertura:** painel fechado por default; botão **Abrir contexto** no header central somente enquanto fechado e quando a superfície estiver disponibilizada; ao abrir, somente botão de fechar no cabeçalho direito.
- **Fechamento:** apenas oculta UI; **não** aborta interação nem cancela ACT/Automation Hub, não altera `turns`, draft ou posição de scroll.
- **Dock/mobile:** drawer sobreposto sob demanda com backdrop, foco e Escape controlados, somente uma drawer aberta; contexto não fica como coluna comprimida.

### 10.3 Reuse e aceite

`EXISTING_EQUIVALENT=YES` para `ActivityViewer`, `EvidenceDetails`, `ConversationHeader`, `RoomSidePanel` e primitives; `REUSE_DECISION=REUSE` para projeções visuais e `EXTEND` para composição de painel direito. `TO_INVENTORY` para seleção governada de turno/contrato de contexto aprofundado. UI de painel não vira provider, engine, planner nem authority.

**Critérios:** único botão de contexto por estado; exatamente um empty state quando tudo vazio; seções com dados reais não degradam a leitura principal; nenhuma promessa falsa; aparência uniforme nas três regiões; screenshot desktop e Dock; keyboard/ARIA, light/dark, zoom 200%, contrast, overflow e reduced motion; testes/federação/browser QA executados antes de aceite. `UX_REVIEW=REWORK`, `RUNTIME_CHANGE=NONE` nesta atualização.
