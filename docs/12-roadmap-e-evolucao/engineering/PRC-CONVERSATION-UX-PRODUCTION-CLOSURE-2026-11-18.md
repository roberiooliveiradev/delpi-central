# PRC — Fechamento consolidado de conversa e UX em produção (18/11/2026)

**Status:** `PO_FUNCTIONAL_ACCEPTANCE_REPORTED / PRD_DEPLOY_REPORTED / CODE_VERIFIED / PRD_AUTHENTICATED_AUTOMATED_SMOKE_NOT_RUN`  
**Escopo:** apenas conversa PRC compartilhada e apresentação do detalhe UPDATE nos MFEs Engineering e My Requests. **Não** declara encerramento do PRC-TRACK inteiro, produtos acompanhados, desenhos, TOTVS, flags ou demais frentes.  
**Owner:** Engineering API (dados, fluxo e AuthZ); `@delpi/plugin-ui` (UI compartilhada); MFEs Engineering/My Requests (consumidores); EVA via seis tools existentes.  
**Tracker:** [Issue #207](https://github.com/roberiooliveiradev/delpi-central/issues/207).  
**Precedência:** este fechamento prevalece **somente para o escopo acima** sobre estados `PLANNED`, `VISUAL_QA_NOT_RUN` ou `PRODUCTION_DEPLOY_SUSPENDED` registrados em especificações de 07–16/11. Os trechos antigos permanecem como baseline histórico, não como ordem executável atual.

## 1. Reancoragem e níveis de evidência

- **PROVEN_CODE (GitHub `main`, inspecionado em 18/11):** `PrcTechnicalSheetView.tsx` mantém card consolidado e não contém `Nenhuma alteração cadastral solicitada.`; `PrcDetailPage.tsx` não tem tab `history` e passa `refreshKey={conversationRefreshKey}`; `ConversationPanel.tsx` suporta `expandable`; `conversation-panel.css` contém `--delpi-ui-room-panel-max-height: none` no escopo expandido.
- **REPORTED_EXECUTION (relatórios devolvidos pelo executor):** commits, testes, snapshots e digests de HML/PRD descritos nas seções seguintes. Relatos de deploy/health não equivalem a nova inspeção operacional independente nesta revisão documental.
- **PO_CONFIRMED (18/11, conversa do projeto):** o PO confirmou expressamente que o problema textual foi resolvido e que as funcionalidades e a paridade desejadas foram alcançadas; autorizou passar para outro fluxo.
- **TEST_NOT_RUN:** automação de smoke autenticado em PRD, por indisponibilidade de credencial legitimamente provisionada nos relatórios. Não converter em `PASS` com base em gateway/bundle/health nem inferir concessão de acesso.

## 2. Matriz de entregas delimitadas

| Pacote | Commit de referência | Resultado e evidência |
| --- | --- | --- |
| Conversa inicial P1/P2/P3 | `372b69d118` (release) | Engineering API única, comentários/anexos, seis tools EVA; Doc 130 registra HML 21/21 e deploy PRD; smoke PRD autenticado `TEST_NOT_RUN` |
| F-01 realtime | `82561bf9ed` | `refreshKey` conectado nos dois MFEs; HML reportado com duas identidades, conversa aberta em ambos os sentidos |
| Detalhe com três abas | `00d07d59cd` | Ficha técnica, Verificação TOTVS, Revisões; conversa após documentos e histórico abaixo da conversa, ambos full-width; `?tab=history` legado resolve para ficha |
| Modal expansível | `b555c0b16b` | `ConversationPanel` opt-in nos dois MFEs; `createHostContainedModalShell` em `fill`, sidebar preservada |
| Fix de altura expandida | `32e0c4ff9c`; docs `c16050fe5f` | CSS vars removem clamp do RoomPanel apenas no modo expandido; HML reportou 252px → 20px de espaço sob o editor e 25/25 E2E |
| Resumo conjunto de alterações | `40d42a304a` | Campos + `supplierLinkChanges` no mesmo card; enumeração ADD/UPDATE/REMOVE, estado vazio só para zero+zero, sem afirmar efetivação TOTVS |
| Texto ambíguo removido | `784d7047a6fbf301a87ff27cc4705738aeec05bd` | Remove o ramo `Nenhuma alteração cadastral solicitada.` (supplier-only), mantém resumo e detalhes; HML autenticado e PRD bundle/health reportados |

**Último deploy PRD reportado neste recorte:** `plugin-ui` digest `eb5b631417c4`, checkout `784d7047a6`; `engineering` e `my-requests` mantidos nesse último deploy. Deploy consolidado anterior dos três serviços reportou `plugin-ui ac739389fa2b35b`, `engineering 770bd7c6efbba`, `my-requests d7c39d3c99ddb`. Digests são evidência histórica datada, **não garantias do estado live futuro**. Rollback deve revalidar imagens atuais antes de agir.

## 3. Contrato visual vigente

**Portal Engenharia, detalhe de solicitação PRC:** somente `Ficha técnica | Verificação TOTVS | Revisões`. A ficha conserva dados técnicos e documentos, depois **Conversa sobre a solicitação** e **Histórico da solicitação** em duas seções verticais de largura total. O histórico contém trocas formais estruturadas (`PrcInformationExchangePanel`) e timeline (`PrcTimelineSection`), sem mistura semântica com comentários. URL antiga `?tab=history` não deve gerar uma quarta aba.

**Conversa nos dois MFEs:** mesmo `requestId` e Engineering API, avatar autorizado/fallback, anexos e autorização backend-first. Modo compacto mantém altura anterior; botão expandir abre modal contido no host MFE com cabeçalho, área de mensagens flexível/rolável e editor no rodapé. Preservar draft, anexos pendentes, foco, estados terminais e realtime F-01. Sem clone no `requests-api`.

**UPDATE — Alterações solicitadas:** resumo e detalhes incluem campos escalares e vínculos de fornecedores. Supplier-only apresenta, por exemplo, `1 fornecedor a adicionar` e `Fornecedores` com código/loja/PN; **não** exibe `Nenhuma alteração cadastral solicitada.`. Somente zero alterações de ambas as classes admite `Nenhuma alteração solicitada.`. `requestStatus=completed` é contexto histórico: não afirmar que o vínculo já foi efetivado no TOTVS sem confirmação oficial.

## 4. Limites funcionais e segurança

Sem mudanças nessas rodadas de UX nos contratos REST, schema/migrations, auth, RBAC, Engine API, workflow ou catálogo de seis tools públicas da EVA. UI não é source of truth. Comentários livres não substituem `return_for_correction` / `save_returned_fields` / `resubmit_correction`, nem publicam revisão ou alteram fornecedores oficiais.

## 5. Evidências, pendências e encerramento

- O executor relatou regressões automatizadas verdes: correção final de texto `26/26` no arquivo PRC; suites anteriores mais amplas pertencem aos SHAs testados e não devem ser reatribuídas automaticamente ao último SHA.
- Último release PRD: bundle sem string ambígua, gateway 200 e container saudável **reportados**; smoke automatizado PRD autenticado `TEST_NOT_RUN`.
- O PO confirmou visualmente o resultado final em produção em 18/11/2026, encerrando a **pendência de aceite visual desse texto**. Isso não equivale a testes automatizados de negação por objeto em PRD.
- Residuais independentes: teste de reconexão WS controlada `TEST_NOT_RUN`, tema escuro `TEST_NOT_RUN`, edição pelo botão UI expandida `TEST_NOT_RUN` nos relatórios anteriores; verificador Devin `INCONCLUSIVE` por login indisponível. `requests-api` WS 404 em HML e antivírus `inspection: structural` são trilhas separadas e não bloqueios novos desta correção visual.
- **Condição para novo fluxo:** fazer G0 próprio, ler authorities/código/contratos no HEAD e não usar este fechamento como autorização ampla de novas writes/deploys ou mudança de owner.

**Veredito deste registro:** `PRC_CONVERSATION_AND_REQUESTED_CHANGES_UX_CLOSED_BY_PO / DEPLOY_PRD_REPORTED / DOCUMENTARY_RECONCILIATION_COMPLETE_FOR_DEFINED_SCOPE`. O tracker #207 pode ser atualizado pelo mantenedor com esse escopo, sem declarar testes `TEST_NOT_RUN` como concluídos.
