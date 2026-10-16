# 97 — DÉLIA | ConversationSearch — Especificação futura de pesquisa no histórico

**Data:** 2026-10-16  
**Status:** `DOCUMENTED_FUTURE_TARGET / BACKEND_FIRST / IMPLEMENTATION_DEFERRED`  
**Decisão do Product Master:** **não implementar busca local de conversa como solução provisória**. A pesquisa pretendida depende de histórico conversacional persistido e contratos backend legítimos, ainda não comprovados/implementados no escopo atual. Registrar UX e funcionalidades para execução futura.  
**Natureza:** somente documentação; nenhum frontend/backend/schema/migration/teste de runtime/deploy/fase alterado.  
**Owner da UI compartilhada:** `plugins/plugin-ui`; **consumer:** `plugins/delia`; **owner de persistência/pesquisa:** a definir no boundary DÉLIA segundo authorities e contratos, sem nova autoridade paralela.  
**Reancoragem futura:** HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → specs de conversa/persistência → ledger. Divergência = sinalizar `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED`, nunca reconciliar silenciosamente.  
**HEAD consultado na elaboração:** `33748ae41159f764762a73f07f914eacc158e191` (não é HEAD futuro de implementação).

## 1. Objetivo e escopo

Entregar, futuramente, pesquisa textual nas **conversas persistidas da própria DÉLIA que o usuário esteja autorizado a consultar**, com busca por termos/frases, realce visual de ocorrências, navegação entre resultados e abertura do turno original com contexto. A interface deve indicar claramente escopo, filtros, limitações e disponibilidade do histórico. A pesquisa não é busca de dados operacionais/Domain API nem busca web.

**Decisão de produto:** pesquisa **backend-first**. O componente visual será construído em `plugin-ui` e consumido pela DÉLIA somente quando houver fonte de histórico e contrato de consulta válidos. Não usar busca apenas no array `turns` do React como entrega parcial, nem introduzir persistence local para justificá-la.

## 2. Estado factual e dependências

**PROVEN no código consultado:**
- `plugins/delia/src/App.tsx` mantém `turns` em estado React transitório e declara expressamente ausência de browser storage e persistência backend; recarregar a tela reinicia a conversa.
- `plugins/delia/src/ui/ConversationTimeline.tsx` ordena turnos de exibição com IDs locais e descreve `ConversationDisplayTurn` como estado temporário de UI, não histórico durável nem memória.
- O `plugin-ui` possui superfícies conversacionais compartilhadas (`ConversationWorkspace`, `ConversationHeader`, `ConversationScrollNavigator`, etc.), mas essa constatação **não comprova** existência de componente de busca/endpoint de histórico no âmbito DÉLIA.

**TO_INVENTORY / não comprovado:** persistência durável própria de conversas DÉLIA, índices de pesquisa, IDs estáveis de sessões/turnos persistidos, contrato de busca, retenção, permissão por conversa/turno, fonte de texto pesquisável, paginação, result navigation para mensagens não carregadas, mecanismo de auditoria, política de exclusão e lifecycle de dados. Documentação de arquitetura sobre persistência não significa runtime implementado.

`EXISTING_EQUIVALENT = YES` para primitives visuais, shell e navegação da conversa; `EXISTING_EQUIVALENT = TO_INVENTORY` para serviço/indexação/contrato de pesquisa no histórico. `REUSE_DECISION = REUSE` para primitives aprovados; a decisão para uma composição de busca será `EXTEND` ou `NEW` **após gate de inventário/owner**. Não criar search engine, registry, index ou tabela por conveniência.

## 3. Aparência esperada

```text
[DÉLIA]                                  [Buscar na conversa 🔍]

             +-----------------------------------------+
             | 🔍 Pesquisar nas minhas conversas     X |
             | [Termo ou frase...]             [Buscar] |
             | Escopo: [Conversa atual ▾]               |
             | 1–10 de 28 resultados                   |
             |    [Anterior ↑]   [Próximo ↓]            |
             +-----------------------------------------+

  Resultado (exemplo ilustrativo; não é dado real)
  [Conversa • data/hora se houver contrato]
  ... encontrei três [indicadores] relevantes ...
  [Abrir mensagem original]
```

- **Entry point:** ícone de lupa no header conversacional ou ação equivalente reutilizável; acessível, discreto, não competir com título, estado crítico e composer.
- **Superfície:** painel compacto de pesquisa acima/ao lado da timeline, ancorado no `ConversationWorkspace`; não cobrir ações governadas ou evidências materiais.
- **Campo:** texto controlado, label acessível, botão limpar, estados focus/hover/disabled/loading, atalho opcional documentado sem interceptar o composer ou atalhos do Portal.
- **Resultados:** itens com trecho contextual delimitado e ocorrência destacada, origem/título apenas quando provados, timestamp formatado com fuso correto quando publicado, e ação “Abrir mensagem original”.
- **Realce:** visual com alto contraste (light/dark), sem depender somente de cor; a marcação não altera o texto-fonte nem o status epistêmico.
- **Navegação:** anterior/próximo pelas ocorrências retornadas, índice de posição honesto (ex.: “3 de 28”), scroll/foco para mensagem original quando carregada ou navegação contratual quando arquivada.
- **Responsividade:** desktop em barra/painel leve, dock estreito com layout vertical, largura 320/420px e zoom 200%, sem scroll horizontal global.
- **Acessibilidade:** controles button/input reais, keyboard/Enter/Escape conforme contrato, focus restore ao fechar, `aria-label`, estado de resultados anunciado de maneira não repetitiva, leitura de snippet preservada e `prefers-reduced-motion`.
- **Conteúdo não renderizado como HTML arbitrário:** snippets são strings inertes, com destaque por fragmentos React controlados e delimitados, sem `dangerouslySetInnerHTML`.

## 4. Funcionalidades futuras — UX completa

1. **Buscar por palavra ou frase:** query bounded, trim/normalização definida em contrato, case/acento/idioma de modo explícito; não inferir semântica de busca de modelo sem contrato.
2. **Escopo de pesquisa:** inicialmente “conversa atual” *persistida*; “todas as minhas conversas” somente se houver contratos de listagem, retenção e autorização abrangente. Não oferecer opção de escopo que ainda não exista.
3. **Consulta backend:** envio de query/filtros à API oficial da DÉLIA, sem indexar no browser como source of truth; debounce/throttle conforme contrato e cancelamento seguro de buscas obsoletas.
4. **Resultado contextualizado:** snippet bounded, identificador opaco e estável de mensagem/conversa, posição de match validada ou highlight derivado com segurança; indicação de fonte e timestamp somente publicados pela autoridade.
5. **Navegação por matches:** anterior/próximo e abertura/posicionamento do resultado, inclusive quando a mensagem não estiver atualmente carregada. Necessita endpoint/contrato de recuperação de turno/contexto.
6. **Histórico paginado:** cursores estáveis, ordenação, limites, total exato ou estimado explicitado, comportamento em novos turnos/updates/exclusões e casos de resultado obsoleto.
7. **Filtros opcionais:** período, role, conversa, e futuramente proveniência, somente após contrato tipado/autorizado e utilidade demonstrada; não criar filtros de fachada.
8. **Estados:** initial, typing, searching, results, no-results, unavailable, permission-denied, expired/stale-result, error/retry, canceled-query; erros e loading honestos sem resultado inventado.
9. **Privacidade:** pesquisar somente dados retidos e autorizados do próprio contexto; exclusão/revogação deve afetar pesquisa conforme postcondition definida. Não vazar snippets de sessões proibidas.
10. **Não substitui Evidence:** localizar uma mensagem não comprova FACT; links/evidências mantêm suas regras e owner próprios.
11. **Sem efeitos materiais:** consulta READ; não aciona MCP/Domain writes/Automation Hub nem comandos PREPARE/ACT.

## 5. Contrato backend necessário ANTES de implementar

**Owner/consumers:** DÉLIA bounded context legítimo de histórico/persistência + API para o MFE; verificar mecanismos planejados/existentes antes de propor tabelas/serviços.

Definir e congelar, antes do frontend funcional:
- Modelo de persistência de conversas/turnos: ownership, identidade canônica, IDs, lifecycle, retention, exclusão/revogação, privacidade e compatibilidade.
- OpenAPI/operationId estável para pesquisa read-only e recuperação/abertura de turnos, request/response versionados.
- Query, filtros, limites de tamanho, paginação/cursor, ordenação, total/hasMore, idiomas/acento/case e regras de indexação.
- Autenticação/identidade: Keycloak autentica; Core resolve live AuthZ; Domain/DÉLIA aplicam regra e ACL efetivas no servidor. JWT identifica contexto, não autoriza acessar histórico de terceiros.
- Erros tipados: invalid query, unauthenticated/forbidden, not found, expired, retention, rate limit, unavailable, timeout e compatibilidade.
- Segurança multi-tenant, isolamento de usuário/conversa, minimização de snippets, logging sem conteúdo sensível, criptografia/segredos, auditoria, observabilidade, proteção de enumeration.
- Consistência de índice com inclusão/alteração/exclusão e prova de postcondition; `HTTP 200 != authorized business outcome`.
- Capacidade de abrir mensagem não carregada, com navigation/focus e preservação de estado da conversa atual.
- Testes negativos de ACL, injeção, snippet adversarial, paginação, stale cursor, deleted messages, concorrência e escalabilidade.

**Não decidir agora** schema, endpoints, nomes de tabela, engine de busca, UX de “todas as conversas”, prazo de retenção ou modelo de indexação. Requer inventário, owner e freeze documental canônico.

## 6. Separação de responsabilidades

- **`plugins/plugin-ui`:** aparência, input e painel de pesquisa, highlight seguro, resultados, navegação e estados acessíveis; apenas props/callbacks, sem fetch/Core/Keycloak/backend, persistência ou índice local.
- **`plugins/delia`:** importa componente completo de `@delpi/plugin-ui/index`, mantém UI state transitório (query/resultado atual), chama cliente autorizado do backend quando houver contrato e resolve navegação para contexto carregado.
- **Backend DÉLIA / owner de histórico:** persistência e consulta autoritativas; policies e data lifecycle definidos por authorities. Não converter resultados de memória/modelo/MCP em histórico persistido.
- **Portal:** host/contexto e navegação aprovada; sem busca ou storage paralelo.
- **Core/Keycloak/Domain:** identidade e autorização conforme ownership, sem permissões inferidas por estado frontend.

## 7. Critérios de aceite futuros

1. Histórico persistido realmente disponível e contrato read-only congelado, com owners e authorization provados.
2. Search restrita ao escopo de autorização do usuário, com testes negativos e revogação/retention efetivas.
3. Busca em mensagens que não estão no array React atual, comprovando que não é apenas search frontend.
4. Query, paginação, snippet, navegação, erros e consistência do índice passam em testes de integração.
5. Highlight inerte sem HTML arbitrário, sem alterar fatos/evidência, com adversarial tests.
6. `plugin-ui` reutiliza primitives e DÉLIA importa um componente composto público; federation verificada.
7. Full-page + dock, 320/420px, zoom 200%, light/dark, keyboard/screen reader, reduced motion, QA real.
8. Build, testes, backend ACL/security, observabilidade e task outcome verificados no SHA/config; review independente.
9. Sem nova authority, sem import interno de bounded context, sem runtime Minha DELPI Chat.
10. Sem CP/fase promovidos por documentação; atualização factual de ledger somente após execução aprovada.

## 8. Decisão formal de postergação

Esta task **somente documenta** a aparência e funcionalidades futuras. Explicitamente proibido:
- Criar search local sobre `turns` como substituto da busca backend.
- Persistir conversas em `localStorage`, `IndexedDB` ou caches não governados.
- Introduzir endpoints, migrations, indexes, serviços, frontend components ou feature flags neste momento.
- Dar aparência de histórico persistente a sessões que se perdem no reload.
- Promover requisito/fase/CP ou registrar runtime PASS.

```text
SPEC_STATUS = DOCUMENTED_FUTURE_TARGET
SEARCH_PRODUCT_DIRECTION = BACKEND_FIRST
FRONTEND_ONLY_SEARCH = NOT_AUTHORIZED
CONVERSATION_PERSISTENCE = NOT_IMPLEMENTED_IN_CURRENT_OBSERVED_RUNTIME
BACKEND_SEARCH_CONTRACT = TO_INVENTORY
PLUGIN_UI_SEARCH_COMPONENT = NOT_IMPLEMENTED
DELIA_SEARCH_INTEGRATION = NOT_IMPLEMENTED
EXISTING_EQUIVALENT_VISUAL = YES
EXISTING_EQUIVALENT_BACKEND_SEARCH = TO_INVENTORY
REUSE_DECISION_VISUAL = REUSE
REUSE_DECISION_SEARCH_COMPOSITION = PENDING_GATE
TESTS = TEST_NOT_RUN
DEPLOY = NONE
PHASE_PROGRESSION = NONE
NEXT = DEFERRED_UNTIL_PERSISTENCE_AND_SEARCH_CONTRACT_AUTHORIZED
```
