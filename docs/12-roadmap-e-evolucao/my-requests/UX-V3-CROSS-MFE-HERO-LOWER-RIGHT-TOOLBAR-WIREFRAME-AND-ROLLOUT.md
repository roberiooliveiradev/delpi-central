# UX V3 — Wireframes aprovados: Hero com toolbar inferior direita, tabela com paginação

**TASK_ID:** `CROSS-MFE-LIST-HERO-LOWER-RIGHT-TOOLBAR-HML-PRD-01`  
**PO decision:** APROVADO VISUALMENTE em 15/11/2026. **Implementation:** TARGET; este registro não representa código implementado nem deploy.  
**Escopo:** `my-requests/mine`, `my-requests/work-queue`, `helpdesk`; owner dos componentes visuais compartilhados: `@delpi/plugin-ui`.  
**Superfícies:** `/apps/my-requests/mine`, `/apps/my-requests/work-queue`, `/apps/helpdesk`.  
**Fontes:** prints do PO e revisão visual nesta conversa; [My Requests wireframes](./WIREFRAMES.md), [paridade executada](./UX-V2-HERO-TOOLBAR-EXECUTION-EVIDENCE.md), [Helpdesk wireframes](../helpdesk/WIREFRAMES.md), [listagem Helpdesk](../helpdesk/13-listagem-de-chamados.md), [Plugin UI](../../../plugins/plugin-ui/docs/README.md).

## 1. Decisão de layout — imutável para este pacote

Hierarquia da página:
1. Topbar e PagePath canônicos, conforme o MFE, **fora do Hero**. Manter as quatro abas do My Requests.
2. **Hero único e compacto**, faixa superior: título, subtítulo, contador quando aplicável e ações principais (Atualizar, Nova solicitação/Helpdesk/Abrir chamado conforme contexto e autorização).
3. Faixa do Hero: busca dominante, largura útil inteira, label acessível.
4. Faixa seguinte: chips de status/escopo, com navegação por teclado.
5. **Última linha do Hero: bloco único alinhado ao canto inferior direito, mesma linha desktop, ordem fixa**: `[Filtros] [Ordenar] [Colunas] [Tabela | Cards]`. Nada desses controles ao lado da busca ou acima dos chips. Separação visual curta entre Hero e tabela.
6. **Tabela/lista abaixo do Hero**: acima da grade, **Itens por página**; corpo tabela/cards; no rodapé resumo `x–y de N · Página p de q` e navegação. Sem toolbar duplicada e sem card externo visual redundante. O container de tabela pode existir semanticamente para scroll, borda e footer: evitar remover sua funcionalidade ao reduzir chrome.
7. **Remover ícones `?` redundantes**, especialmente junto à busca, itens/página, paginação; usar label e affordance do controle canônico. Ajuda essencial continua acessível pelo próprio controle (label/tooltip/descrição), não suprimir informações de acessibilidade nem ajuda necessária.
8. **Não adicionar nova funcionalidade**: filtros, ordenação, colunas e Tabela/Cards preservam os contratos implementados. Se um MFE não suporta visualização Cards, não exibir toggle decorativo; neste escopo ambos a possuem.
9. **Mobile:** preservar ordem lógica `Filtros → Ordenar → Colunas → Tabela/Cards`. O grupo pode quebrar em linhas ou ocupar scroll horizontal contido sem overflow da página, com controles acessíveis; alinhamento inferior do Hero (direita quando houver espaço) e não sobreposição.
10. **Não introduzir CSS duplicado nos MFEs**: posicionamento, spacing, density, theme e primitives em `plugin-ui`. Os MFEs compõem dados, contratos e ações. Verificar `toolbarPortalTarget`, `toolbarLayout=hero`, `embedded` e opções de slots/regions existentes; Abstraction Gate antes de novo componente.

## 2. Wireframe aprovado — Minhas Solicitações

```text
TOPBAR [Minhas solicitações] [Fila de trabalho] [Nova solicitação] [Administração]
PagePath Início / Minhas solicitações
┌ HERO ─────────────────────────────────────────────────────────────────┐
│ Minhas solicitações         [16 solicitações] [Atualizar] [+ Nova]     │
│ Acompanhe as solicitações que você abriu.                             │
│ Buscar                                                                │
│ [ Número, código, nome ou assunto...                                ] │
│ Status [Todas] [Enviada] [Em andamento] [Aguardando...] [...]         │
│                  [Filtros] [Ordenar: Data ↓] [Colunas] [Tabela|Cards]  │
└───────────────────────────────────────────────────────────────────────┘
┌ TABELA/LISTA ─────────────────────────────────────────────────────────┐
│                                              Itens por página [20 ▾] │
│ Número | Tipo | Assunto | Status | Filial | Data (sort onde suportado)  │
│ ... linhas autorizadas ...                                           │
│ Mostrando 1–20 de N · Página 1 de q         [Anterior] [Próximo]     │
└───────────────────────────────────────────────────────────────────────┘
```

Escopo `mine` combina Requests corporativas + PRC conforme contratos vigentes (merge bounded). A matriz de ordenabilidade permanece honesta: colunas apenas quando sort é suportado por todas as fontes da consulta; não fingir ordenação no browser.

## 3. Wireframe aprovado — Fila de Trabalho

```text
TOPBAR [Minhas solicitações] [Fila de trabalho] [Nova solicitação] [Administração]
PagePath Início / Minhas solicitações / Fila de trabalho
┌ HERO ─────────────────────────────────────────────────────────────────┐
│ Fila de trabalho                      [4 pendências] [Atualizar]      │
│ Solicitações abertas aos processadores.                              │
│ Buscar                                                                │
│ [ Número, código, nome ou assunto...                                ] │
│ Status [Todas] [Enviada] [Em andamento] [Aguardando...] [...]         │
│                  [Filtros] [Ordenar: Data ↓] [Colunas] [Tabela|Cards]  │
└───────────────────────────────────────────────────────────────────────┘
┌ TABELA/LISTA ─────────────────────────────────────────────────────────┐
│                                              Itens por página [20 ▾] │
│ Número|Tipo|Assunto|Solicitante|Status|Filial|Concluída por|Data       │
│ ... linhas autorizadas ...                                           │
│ Mostrando 1–4 de 4 · Página 1 de 1           [Anterior] [Próximo]    │
└───────────────────────────────────────────────────────────────────────┘
```

Manter `mineScope`, escopo de processadores e autorização. Sem CTA Nova duplicado no Hero da Fila.

## 4. Wireframe aprovado — Meus Chamados de TI

```text
┌ HERO ─────────────────────────────────────────────────────────────────┐
│ Meus Chamados de TI                  [Helpdesk] [Atualizar] [+ Abrir]  │
│ Acompanhe suas solicitações e atendimentos de TI.                    │
│ Buscar                                                                │
│ [ Número, título, conteúdo, categoria, técnico...                  ] │
│ [Meus chamados] [Todos] [Abertos] [Em atendimento] [...]              │
│             [Filtros] [Ordenar: Atualizado ↓] [Colunas] [Tabela|Cards] │
└───────────────────────────────────────────────────────────────────────┘
┌ TABELA/LISTA ─────────────────────────────────────────────────────────┐
│                                              Itens por página [20 ▾] │
│ Chamado | Título | Status | Categoria | Técnico | Atualizado | ...    │
│ ... linhas autorizadas ...                                           │
│ Mostrando 1–20 de 21 · Página 1 de 2            [1] [2] [Próximo]    │
└───────────────────────────────────────────────────────────────────────┘
```

Migrar a composição atual do Helpdesk para o mesmo contrato de posicionamento canônico; filtros/sort multi-nível GLPI e seus campos autorizados permanecem próprios do domínio Helpdesk. Não modificar rotas, autenticação nem writes GLPI.

## 5. Ownership / design system

- `plugin-ui`: PageHero, DataTableSection/DataTable, toolbar host/slots, sort/filter popover, column menu, SegmentToggle, pagination, layout responsivo, tokens e acessibilidade. Evolução aditiva com compatibilidade de consumidores.
- `my-requests`: composição `RequestListShell`, `MinePage` e `WorkQueuePage`, adapters e estado de URL, fetch/escopo de dados; não copiar primitivas Helpdesk.
- `helpdesk`: composição `HelpdeskPage` / `TicketListToolbar`, adapters GLPI, estado e paginação; consumir kit, não importar internals de My Requests.
- `requests-api` e `helpdesk-api`: autoridade de dados, ordenação, filtros, AuthZ. **Não alterar backend por reposicionamento**; somente alterar se prova de necessidade/defeito e contrato governado aprovado.
- `Core/Keycloak`: SSO/RBAC permanecem autoridades; `MFE` não autoriza escrita.

## 6. Gates para implementação, verificação e rollout

| Gate | Requisito de saída |
|---|---|
| G0 | SHA/HEAD/origin/main, git status e concorrência, inventário contratos e equivalentes |
| G1 | Plugin UI implementa composição reutilizável e compatível; testes do kit |
| G2 | My Requests Mine + Work Queue exatamente no wireframe; sem regressões |
| G3 | Helpdesk exatamente no wireframe; contratos GLPI preservados |
| G4 | Testes unit/integration/typecheck/build dos três componentes; telas/estados |
| G5 | Chromium E2E **visual** desktop 1440/tablet768/mobile390/320/zoom200, tema claro/escuro, teclado e acessibilidade |
| G6 | Verificador independente lê diff+evidências, emite finding/OC; corrigir→retestar→reverificar até nenhum finding crítico |
| G7 | Deploy **HML** plugin-ui antes dos consumers; HEALTH/remotes/smoke/autenticação/rollback; comparar screenshots |
| G8 | Verificação independente **pós-HML** e aceite operacional do gate. Se Helpdesk gated em HML, criar acesso/provisionamento **somente por owner autorizado**, ou BLOCKED sem declarar full parity. |
| G9 | Pré-deploy **PRD**, diff de release, config, compat, RBAC, backup, rollback, ordem de rollout, janela, saúde de outros MFEs; sem drift não ratificado |
| G10 | **PRD** somente após G0–G9 PASS, autorização explícita de deploy do PO desta conversa válida **para esse escopo** e sem novas mudanças de autoridade, serviços ou contratos materiais; se surgir drift ou risco não aprovado, STOP e retornar Coordination. |
| G11 | Smoke PRD read-only com identidade legítima, regressão Helpdesk/MyRequests, 5xx, observabilidade, rollback se trigger; ledger + relatório |
 
**PRODUCTION AUTHORIZATION:** o PO solicitou execução até PRD **após** gates. Não é licença para deploy cego, mudanças de RBAC, provisioning de clients, dados de negócio, writes TOTVS/GLPI, bypass AuthZ ou inclusão de serviços extras. Se qualquer bloqueio relevante permanecer (especialmente E2E Helpdesk HML), **não publicar em PRD**. Nunca declarar teste `PASS` quando `TEST_NOT_RUN/INCONCLUSIVE`.

## 7. Acceptance criteria (bloqueantes)

| AC | Critério |
|---|---|
| AC01 | Hero de cada tela mostra título, ações e busca corretamente; topbar My Requests preservada |
| AC02 | Chips/status diretamente abaixo da busca, responsivos, filtros funcionais |
| AC03 | Ordem Filtros → Ordenar → Colunas → Tabela/Cards em uma linha **inferior direita** desktop |
| AC04 | Controles dentro do DOM/rect do Hero, **abaixo dos chips**; nenhuma cópia em toolbar separada |
| AC05 | Itens por página dentro de **card/região da tabela**, não no Hero, muda paginação real |
| AC06 | Remoção de `?` redundantes; label, help e acessibilidade essenciais preservados |
| AC07 | Tabela/lista sem duplicação de títulos/card, largura e densidade no padrão aprovado |
| AC08 | Popovers visíveis, ancorados, flip/clamp, sem recorte, e temas coerentes |
| AC09 | Sort header/back-end/filtros/columns/cards/URL/estados mantidos funcionalmente |
| AC10 | Preferências independentes MyRequests Mine/Fila e Helpdesk, persistem |
| AC11 | Desktop+tablet+mobile+zoom200 sem overflow; foco, teclado, contrast/ARIA |
| AC12 | Regressões My Requests PRC, Fila, Helpdesk GLPI, nav e api-read sem alteração de autorização |
| AC13 | Verificador independente em código e HML, findings corrigidos, evidence/screenshots versionados |
| AC14 | Deploy HML com rollback, health, remoteEntry, sem 5xx |
| AC15 | Pré-deploy PRD GO apenas com gates satisfeitos, backups/restaurabilidade, sem drift ou acesso faltante |
| AC16 | Deploy PRD controlado, health + smoke autenticado read-only + rollback pronto e ledger |
| AC17 | Todas as fases sem writes TOTVS, sem grants RBAC indevidos, sem descartes de WIP concorrente |
| AC18 | Sem PASS fabricado: limites, não executados e regressões preexistentes explicitados |

## 8. Evidências mínimas

Screenshots HML e PRD de Mine/Fila/Helpdesk (desktop e mobile); computed rects `Hero`, chips e toolbar (toolbar abaixo chips e dentro Hero; alinhada à direita); DataTable/card com pageSize; contraste light/dark; ações de sort/filter real; matrizes RQ/AC; resultados testes, verificador, SHAs de código e imagens, health, remoteEntry, Rollback. Testar Helpdesk em HML com identidade autorizada; não usar HML tester como prova de acesso se plugin não concedido.

**Estado de execução deste documento:** `PLANNED / PO_APPROVED_VISUAL`. Ao implementar, atualizar docs e ledger com resultado **sem sobrescrever a história da V2**.
