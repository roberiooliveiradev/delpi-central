# Portal Suprimentos — Plano de refatoração do componente Atenção (Home)
**Data:** 2026-10-23 · **Estado:** `EXECUTED` — ver [HOME-ATTENTION-REAL-DATA-RESULT-20261023.md](./HOME-ATTENTION-REAL-DATA-RESULT-20261023.md) · **Implementação/deploy:** `AUTHORIZED_BY_PO`, condicionada aos gates técnicos e de segurança  
**Escopo estrito:** componente **Atenção** da página `/apps/supplies` (Home). **Não alterar** hero, caminhos/funcionalidades, favoritos, últimos acessos, barra de navegação, indicadores da Visão geral ou outras páginas.

## 1. Problema observado e decisão de produto
As capturas fornecidas pelo PO mostram sete atalhos genéricos sob a aparência de alertas: **Minhas tarefas, Solicitações de compras, Pedidos de compra, Entregas, Estoque de segurança, Visão geral e Administração**. Esses itens não provam, por si, que existem pendências: faltam critério de atenção, quantidade real, eventual prévia e link para o conjunto de registros correspondente.

**Objetivo:** a seção exibe **somente situações operacionais comprovadas que exigem acompanhamento**, com contagem real, significado claro, eventual prévia (até 3 itens quando permitido) e acesso à lista apropriada. Sem pendências confirmadas, mostrar estado positivo compacto; com falha de fonte, comunicar indisponibilidade sem tratar falha como zero. Não inventar números, prioridades, prazos, exemplos ou regras de negócio.

**Separar alertas de navegação:** atalhos continuam em `Caminhos e funcionalidades`, fora do escopo desta mudança. Não mostrar `Visão geral` ou `Administração` como alerta pelo simples fato de existirem.

## 2. Inventário inicial verificado no GitHub (não é prova de runtime)
- `plugins/supplies/src/pages/HomePage.tsx`: consome `loadHomeAttention()`, renderiza `SuppliesEventsSection` quando há `cards`, exibe `count` quando não nulo, botão Atualizar, estados `loading/error/partial`, e `queue-ok` se não houver cards. Link usa `viewId` e `navigatePluginView` (navegação genérica; filtro correspondente não comprovado).
- `plugins/supplies/src/api/homeAttention.ts`: `GET /home/attention` via BFF; `HomeAttentionCard` possui `id,viewId,title,description,requiredCap,count:number|null,status:'available'|'unavailable'`; contrato com `cards[]` e `partialFailures[]`. Não há preview, filtro ou timestamp no DTO atual.
- `plugins/supplies/src/app/homeAttentionStore.ts`: loading, abort/sequence, error, partial failures e refresh já existem.
- `docs/12-roadmap-e-evolucao/supplies/API-ROUTES.md`: documenta `GET /home/attention` como implementado, fonte 'composição autorizada'. **O produtor, as queries reais, os critérios e a AuthZ por origem ainda precisam ser abertos no HEAD.**
- Imagens PO: lista estática aparentando sete pendências e hero com contador `Atenção 7`. Não concluir que 7 representa registros operacionais reais.

Classificação: `MFE_CONTRACT=PROVEN (código)`; `BFF_ROUTE=DOCUMENTED`; `SOURCE_CALCULATIONS=TO_INVENTORY`; `COUNT_CORRECTNESS=TO_INVENTORY`; `REAL_ALERT_RULES=PLANNED`.

## 3. Requisitos funcionais (para contract freeze em A1)
| ID | Critério |
|---|---|
| RQ-01 | Só apresentar categoria quando a fonte autorizada confirmar `count>0` segundo regra de negócio congelada |
| RQ-02 | Contagem deve indicar unidade e população do cálculo; não somar categorias com conjuntos sobrepostos como se fossem itens únicos |
| RQ-03 | Título da categoria descreve a ocorrência (p.ex. 'Entregas atrasadas'), não apenas o módulo ('Entregas') |
| RQ-04 | Se existir endpoint seguro de prévia, expor até 3 exemplos relevantes; caso contrário mostrar só contagem/descrição sem inventar detalhe |
| RQ-05 | Ação Abrir leva ao recorte correspondente com filtros URL/F5 quando a rota destino suportar; se não suportar, declarar residual e não prometer filtro |
| RQ-06 | Sem pendências e todas fontes autorizadas verificadas: estado compacto 'Nenhuma situação exige atenção no momento' |
| RQ-07 | Erro/parcial/timeout: distinguir indisponibilidade, zero e dado desatualizado; falha de AuthZ = fail-closed, não partial success |
| RQ-08 | Nenhuma categoria sem permissão/escopo efetivo do usuário; aplicar capability + unit/resource/ownership + business rule no BFF |
| RQ-09 | Exibir atualização temporal somente se houver timestamp confiável; sem números/stale inventados |
| RQ-10 | Atualizar preserva estados adequados, evita requisições duplicadas e comunica progresso; sem efeito nas demais partes da Home |
| RQ-11 | UI kit-first (`@delpi/plugin-ui`), responsiva, tema claro/escuro, teclado/foco, loading/empty/partial/error/403 |
| RQ-12 | Ajuda e documentação sincronizadas; nenhuma permission nova por card nem espelhamento de dados TOTVS no Postgres supplies |

## 4. Fontes candidatas — não promover sem evidência
| Candidato | Regra possível a validar com owner | Prévia/rota | Estado |
|---|---|---|---|
| Minhas tarefas | Tarefas pendentes **atribuídas ao usuário**, não qualquer tarefa | prazo/prioridade; `my_tasks` se owner confirmar | `TO_INVENTORY` |
| Solicitações de compras | SCs com situação que demande acompanhamento/ação definida | quantidade por status; `purchase_requests` | `TO_INVENTORY` |
| Pedidos de compra | Pedidos vencidos/pendentes conforme critério canônico | pedido, fornecedor, prazo; `purchase_orders` | `TO_INVENTORY` |
| Entregas | Entregas atrasadas ou sem confirmação com data confiável | contagem/atraso; `deliveries` | `TO_INVENTORY` |
| Estoque de segurança | Materiais abaixo da cobertura definida no contexto owner | material, déficit; `safety_stock` | `TO_INVENTORY` |
| Administração | Apenas exceções operacionais realmente atribuídas ao perfil, se existir fonte | `administration` | `TO_INVENTORY` |
| Visão geral | Não é alerta por si; não incluir sem ocorrência formal específica | `overview` segue acessível fora da Atenção | `EXCLUDE_BY_DEFAULT` |

**Prioridade de inventário proposta:** Entregas, Pedidos e Estoque de segurança, depois SC e Tarefas; não equivale a prontidão contratual. Para cada candidato, verificar se produtor existente já oferece lista, aggregate count, filtros, ordenação, escopo e preview. `Search miss != ausência`.

## 5. Proposta de contrato (TARGET, não implementar nesta fase)
Manter compatibilidade do `GET /home/attention` atual. Avaliar evolução **aditiva** do card com `preview?: [...] `, `filters?: ...`, `updatedAt?: ...`, estado parcial/falha por origem e `countSource/definition` documentados. Não padronizar filtros arbitrários para todos os módulos; o BFF deve fornecer alvo/URL autorizado e construído a partir dos contratos das rotas, nunca URL não validada do upstream.

Semântica:
- `count=0` com fonte consultada com sucesso: não renderizar alerta.
- `count=null` / source failure: **não** confundir com zero nem incrementar total.
- `status='unavailable'`: aviso/partial, não ação indevida.
- `count>0`: card com título de situação + quantidade; eventual preview autorizada.
- `aggregate total`: somente se demonstrado universo não sobreposto; caso contrário usar 'áreas com atenção' e contadores por categoria.
- Falha de Core/AuthZ invalida a origem/solicitação, não é 'zero pendências'.

**A Home deve ficar limpa:** no estado de várias ocorrências, usar cards compactos e, se autorizado, lista curta de até 3 registros; no estado sem ocorrências, evitar 7 cards vazios.

## 6. Arquitetura/ownership
```text
Portal shell → plugins/supplies (somente apresentação)
             → supplies-api (composição e AuthZ Core fail-closed)
             → api-delpi / purchase-requests-api / contextos autorizados (regras/dados)
```
- Keycloak identidade; Core permission efetiva e unidades; BFF Flask mantém AuthZ.
- Não duplicar cálculo TOTVS no MFE/BFF se regra pertence `api-delpi` ou outro contexto.
- Sem chamadas MFE→api-delpi, sem imports de domain/application de outro contexto, sem DB vizinho, sem nova permission por card, sem espelhar TOTVS no Postgres supplies.
- Datas/volumes devem ter corte e timezone definidos no contrato.
- Quaisquer indicadores gerenciais continuam na Visão geral; Atenção é fila operacional, não dashboard novo.

## 7. Sequência de trabalho e gates (execução contínua autorizada pelo PO)
### A0 — Inventário `TO_INVENTORY`
Reancorar HEAD, git status, authorities, `.cursor`, roadmap/plano/ADRs. Abrir produtor real BFF `/home/attention`, adapters, contratos, chamadas downstream, testes; classificar cada card presente: `REAL_ISSUE_COUNT | NAVIGATION_SHORTCUT | UNKNOWN | UNAVAILABLE`. Buscar contagens e recortes já existentes nas rotas correspondentes. Verificar AuthZ, unidade, resource/ownership, erros parciais, evidência SQL/HTTP sem escrita. **Entrega A0:** matriz campo/origem, exemplo sanitizado de payload, regra, count, preview, rota/filtro, status e lacunas; nenhum diff funcional.

### A1 — Product contract freeze
Com evidência A0, congelar quais categorias realmente entram, fórmula/count, janela temporal, unidade de contagem, deduplicação, ranking, limite de preview, política de zero/partial/stale, disponibilidade das rotas filtradas e critérios de proteção. Se faltar owner ou semântica: `EXECUTION_DRIFT` ou `TO_INVENTORY` conforme caso; não promover a código.

### A2 — BFF/contratos
Planejar menor diff `supplies-api`, consumindo fontes proprietárias por HTTP autorizado, timeout/budget/falha parcial segura, authz, count real e preview minimal. Testes + BFF contract snapshot. Criar endpoints no owner de dados apenas quando evidência de gap real justificar, com autorização adicional.

### A3 — MFE localized
Refatorar exclusivamente bloco Atenção em `HomePage.tsx` + DTO/store/Help correlatos. Preferir `SuppliesEventsSection` e kit existente; se inadequado, justificar variante pequena. Exibir situações reais `count>0`, prévia opcional, navegação, empty OK, loading, partial/error. Não mexer em hero, caminhos, favoritos, recents, outras páginas ou CSS global.

### A4 — QA/acceptance
Positive+sibling+negative, user com/sem unidade, 0 real, 1/N alertas, contagens e dedup, falha parcial, core indisponível, API timeout, preview minimizada, rota/filtro/F5, concorrência/refresh, theme/mobile/keyboard, build/lint/tests e smoke federado autenticado. Smoke ausente = `INCONCLUSIVE`, não PASS inferido. Atualizar Help e docs após aceite, preservando SHAs/evidências.

## 8. Critérios de aceite (futuro DoD do componente)
AC-01 7 atalhos genéricos não aparecem como 'pendências' por configuração; AC-02 contadores derivados de fonte real; AC-03 apenas `count>0` rende alerta; AC-04 estado zero confirmado sem alarmismo; AC-05 falhas parciais/403 tratadas; AC-06 recortes e navegação coerentes; AC-07 preview autorizado ou ausente honestamente; AC-08 unidade/resource/ownership fail-closed; AC-09 sem contagem duplicada enganadora; AC-10 card e descrições úteis; AC-11 componente acessível/responsivo/tema; AC-12 resto da home sem diff visual/funcional; AC-13 regressão e smoke evidenciados; AC-14 Help/docs sincronizados.

## 9. STOP CONDITIONS
- Fonte retorna apenas atalho, sem critério/count real; não chamar 'atenção'.
- Contrato de negócio de atraso/déficit/status não é comprovado; parar a categoria afetada.
- Necessidade de permissões por card, espelhamento TOTVS ou acesso direto MFE a serviço externo.
- Rota filtrada não existe: não inventar filtro.
- Falha de AuthZ não pode ser convertida em `partialFailures` ou contagem zero.
- Exigir alteração de páginas não autorizadas/owners alheios; fazer novo gate.
- Teste federado não executado não pode ser PASS.
- Drift material nos planos/autoridades: registrar `EXECUTION_DRIFT`, não adaptar silenciosamente.

## 10. Execução pelo Devin — do inventário ao deploy, sem checkpoints de aprovação intermediários
**Autorização explícita do PO (2026-10-23):** o Devin deve executar **A0 → A1 → A2 → A3 → A4 → commit/push → deploy canônico → smoke/testes e relatório**, de ponta a ponta, sem parar para solicitar autorização entre as etapas. Inventário e contract freeze são gates internos que o Devin fecha por evidência; não são entregáveis finais isolados. A execução não deve esperar nova autorização para o deploy **desta mudança estritamente delimitada** quando testes, preflight e critérios de segurança estiverem PASS. Essa autorização não inclui outras páginas, expansão irrestrita de serviços, troca de ambiente REST de fornecedores, write ERP ou novas permissões.

**Priorização de decisões sem interromper o trabalho:** selecionar somente alertas cujas regras, contagens e owners estejam efetivamente comprovados; categorias não demonstradas devem ficar fora do componente como `TO_INVENTORY`, sem impedir que as fontes independentes prontas sejam entregues. Nunca forçar indicadores fictícios para preencher sete cards. Usar os contratos existentes; se uma nova integração legítima for necessária, limitar ao owner e escopo autorizados, com testes de consumidor/produtor.

**STOP CONDITION real:** interromper a implantação quando ocorrer risco de vazamento/violação de AuthZ, fonte cuja autorização não possa ser comprovada, regressão material, ambiente/destino incorreto, segredo exposto, contratos incompatíveis, rollback inviável ou impossibilidade de comprovar saúde. Se uma fonte opcional não estiver pronta, remover apenas essa categoria do escopo e entregar as demais. Nunca contornar os gates com contadores presumidos. Com dependência crítica não resolvida, reportar `INCONCLUSIVE/EXECUTION_DRIFT`, não declarar deploy PASS.

**Devin deverá devolver:**
```text
BASE HEAD / ORIGIN MAIN / GIT STATUS
AUTHORITIES AND OWNERS INSPECTED
BFF ROUTE / REAL CODE PATH / PRODUCER CALLS
EXISTING CARDS AND SOURCE OF EACH COUNT
REAL ISSUE RULES / CANDIDATE MATRIX
AUTHZ + UNITS + RESOURCE/OWNERSHIP
COUNT / PREVIEW / TARGET FILTER CAPABILITIES
PARTIAL/EMPTY/ERROR SEMANTICS
TESTS READ / READ-ONLY PROBES PERFORMED
FACTS PROVEN / TO_INVENTORY / EXECUTION_DRIFT
PROPOSED CONTRACT FREEZE A1
FILES INSPECTED
RESIDUAL / STOP CONDITIONS / NEXT STEP
```
A0 **autoriza prosseguir automaticamente** para A1–A4 e deploy **exclusivamente nesta frente autorizada**, desde que os gates técnicos/segurança estejam fechados. Realizar testes unitários, integração BFF, positivos/sibling/negativos de AuthZ, typecheck/lint/build, smoke federado real, estado vazio/parcial/erro, mobile/tema/teclado quando executáveis. Sem sessão autenticada, declarar a verificação visual `INCONCLUSIVE`, sem falsear PASS.

## 11. Referências
- `plugins/supplies/src/pages/HomePage.tsx`
- `plugins/supplies/src/api/homeAttention.ts`
- `plugins/supplies/src/app/homeAttentionStore.ts`
- [API-ROUTES](./API-ROUTES.md)
- [README](./README.md)
- [IMPLEMENTATION-PLAN](./IMPLEMENTATION-PLAN.md)

**Classificação após autorização PO:** `HOME-ATTENTION-REFACTOR = AUTHORIZED_FOR_EXECUTION`; `NEXT = DEVIN A0→A4→DEPLOY/SMOKE`; `CODE_DIFF = PENDING`; `DEPLOY = AUTHORIZED_IF_GATES_PASS`. Após execução reclassificar somente mediante testes e runtime reais.


## 12. Entrega final obrigatória / evidência de produção
- Ancorar HEAD/origin/main/git status, sources/consumers, authorities e ownership antes do diff.
- Implementar somente Atenção; nenhuma mudança de hero, caminhos, favoritos, recents ou outras páginas.
- Testes backend e MFE; critério `count>0`, zero real, falha parcial, 403/401, limites/unidades, preview, filtro e regressão.
- Commit/push escopado; seguir procedimento `AGENTS.md` e `infra/scripts/up-prod-sequential.sh` para **somente serviços afetados**; snapshot de SHA/imagens e rollback antes do deploy.
- Smoke real em `minhadelpi.com.br`: remoteEntry/bundle, `GET /home/attention` autenticado se sessão disponível, contagem versus fonte, UI quando possível, nenhuma chamada a dados proibidos; registrar falhas sem inferir PASS.
- Relatório: BASE HEAD, FINAL HEAD, arquivos, status, cards antes/depois, fórmulas/fontes, AuthZ/escopos, testes, build, commit, imagens, bundle, health, smoke, rollback, residuais, GATE-FEATURE e próximo passo. 
- **Produção de fornecedor permanece pausada aguardando Gabriel/TOTVS**; nunca tocar `URL_REST@1`, flags CREATE/UPDATE ou integrações C1 nesta tarefa.
