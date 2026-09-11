# Portal de Engenharia — roadmap de implementação

> **Status:** planejamento oficial.  
> **Data:** 2026-09-11.  
> **Implementação:** não autorizada por este documento. Cada etapa deve ser revalidada pelo Cursor contra regras, código, contratos e testes vigentes antes de execução.

## 1. Overview

Criar um novo Portal de Engenharia na Minha DELPI, com bounded context próprio, experiência alinhada aos portais Comercial/Suprimentos e navegação principal travada em:

```text
Início → Visão geral → Sala de interação → Minhas tarefas → LMPs → Ajuda
```

Produtos, Controle de MP, Documentos técnicos, Biblioteca de desenhos, Não conformidades, TRANSFORMA+ e futuras capacidades aparecem como ferramentas/aplicações dentro do portal, sem duplicar ownership dos sistemas já existentes.

## 2. Leitura do pedido

### Objetivo principal

Centralizar dados, tarefas, ferramentas e colaboração da Engenharia em uma experiência única, preservando boundaries da Minha DELPI.

### Subobjetivos

- criar módulo-shell próprio de Engenharia;
- manter TopBar enxuta e consistente;
- absorver a experiência dos dashboards atuais sem cutover prematuro;
- criar ferramenta Produtos;
- integrar Controle de MP pelo `my-requests`;
- integrar TRANSFORMA+ sem duplicar Transformômetro;
- criar Sala de interação contextual;
- consolidar Minhas tarefas;
- permitir consulta segura de desenhos e documentos autorizados do FILESERVER;
- oferecer Ajuda na TopBar;
- garantir RBAC, deep links, responsividade, temas e acessibilidade;
- documentar rollout/rollback e depreciação progressiva dos legados.

## 3. Ledger de requisitos

| ID | Requisito | Estado no plano |
|---|---|---|
| RQ-01 | Portal de Engenharia como módulo central do domínio | ATENDIDO_NO_PLANO |
| RQ-02 | TopBar: Início, Visão geral, Sala de interação, Minhas tarefas, LMPs, Ajuda | ATENDIDO_NO_PLANO |
| RQ-03 | Produtos como ferramenta do Portal, fora da TopBar | ATENDIDO_NO_PLANO |
| RQ-04 | LMPs como jornada principal após Minhas tarefas | ATENDIDO_NO_PLANO |
| RQ-05 | Sala de interação geral e contextual | ATENDIDO_NO_PLANO |
| RQ-06 | Minhas tarefas como worklist agregada | ATENDIDO_NO_PLANO |
| RQ-07 | Controle de MP integrado sem segundo MFE | HERDADO_POR_SOLUCAO_TRANSVERSAL (`my-requests`) |
| RQ-08 | TRANSFORMA+ integrado sem duplicar owner | HERDADO_POR_SOLUCAO_TRANSVERSAL (`transformometro-api`) |
| RQ-09 | Consulta de desenhos do FILESERVER | ATENDIDO_NO_PLANO |
| RQ-10 | Consulta segura de outros documentos do FILESERVER | ATENDIDO_NO_PLANO |
| RQ-11 | Visão geral com indicadores oficiais | ATENDIDO_NO_PLANO |
| RQ-12 | Ajuda na TopBar + ajuda contextual | ATENDIDO_NO_PLANO |
| RQ-13 | Kit-first com `@delpi/plugin-ui` | ATENDIDO_NO_PLANO |
| RQ-14 | API própria e sem bypass MFE→api-delpi | ATENDIDO_NO_PLANO |
| RQ-15 | RBAC efetivo no backend | ATENDIDO_NO_PLANO |
| RQ-16 | URL/deep links/F5/back-forward | ATENDIDO_NO_PLANO |
| RQ-17 | claro/escuro, mobile, teclado e acessibilidade | ATENDIDO_NO_PLANO |
| RQ-18 | cutover gradual de `dashboard-engineering` e `dashboard-lmps` | ATENDIDO_NO_PLANO |
| RQ-19 | documentação completa e rastreável | ATENDIDO_NO_PLANO |
| RQ-20 | não transformar FILESERVER em Explorer web irrestrito | ATENDIDO_NO_PLANO |

## 4. Evidências e inventário

Confirmado no repositório:

- `plugins/dashboard-engineering` já cobre visão de Engenharia;
- `plugins/dashboard-lmps` já cobre LMPs, detalhe, BOM, histórico, Gantt e NC;
- `api-delpi` possui `/engineering/*` e `/products/*`;
- biblioteca de desenhos já existe com mount read-only do FILESERVER;
- `transformometro-api` é owner do TRANSFORMA+;
- roadmap `controle-mp` determina migração para `my-requests`;
- Portal Comercial possui Sala de interação e TopBar maduras que servem de referência de experiência;
- regras `.cursor` exigem API própria/BFF, kit-first, ledger, wireframes, testes e revalidação por evidência.

## 5. Arquitetura atual × alvo

### Atual

```text
Minha DELPI
├── dashboard-engineering
├── dashboard-lmps
├── controle-mp iframe
├── Transformômetro
├── my-requests
└── api-delpi
```

### Alvo

```text
Minha DELPI
└── Portal de Engenharia (plugins/engineering)
      │
      ├── TopBar principal
      ├── ferramentas integradas
      └── engineering-api
            ├── api-delpi
            ├── requests-api
            ├── transformometro-api
            ├── Strategic Indicators
            └── adapters FILESERVER/documentos
```

## 6. Decisões travadas

### D-01 — TopBar

Ordem única:

```text
Início | Visão geral | Sala de interação | Minhas tarefas | LMPs | Ajuda
```

### D-02 — Produtos

Produtos é ferramenta do Portal e entra na vitrine de ferramentas, não na TopBar.

### D-03 — API própria

Criar `engineering-api` como BFF/contexto do Portal. `plugins/engineering` não chama `api-delpi` diretamente.

### D-04 — LMPs

Nasce dentro do Portal com paridade progressiva; `dashboard-lmps` não é removido antes do cutover.

### D-05 — Sala

Sala de interação é owner de colaboração, não de workflow. Conversa não muda status oficial de LMP/MP/NC.

### D-06 — Minhas tarefas

Worklist agrega referências de outros owners; não duplica workflow engines.

### D-07 — Controle MP

A experiência canônica futura continua em `my-requests`; Portal só integra/deep-linka/resume.

### D-08 — TRANSFORMA+

Transformômetro continua owner.

### D-09 — FILESERVER

Somente bibliotecas allowlisted, read-only no MVP, sem paths físicos no browser e sem navegação arbitrária.

### D-10 — Design system

`@delpi/plugin-ui` primeiro; façade `engineeringUi.ts`; CSS apenas de layout próprio do MFE.

## 7. Estado antes × depois

| Caso | Antes | Depois esperado | Muda? |
|---|---|---|---|
| Navegação Engenharia | apps/dashboards separados | Portal único | sim |
| LMPs | `dashboard-lmps` isolado | rota principal no Portal | sim, após paridade |
| Produtos | consultas dispersas | ferramenta 360° | sim |
| Controle MP | iframe/roadmap my-requests | acesso integrado ao fluxo canônico | sim via roadmap próprio |
| TRANSFORMA+ | app próprio + resumo | app continua owner + Portal integra | parcialmente |
| Desenhos | API/chat | biblioteca visível no Portal | sim |
| FILESERVER geral | scripts/acessos pontuais | biblioteca técnica controlada | sim |
| SI | fonte estratégica | continua fonte estratégica | não |
| RBAC Core | canônico | continua canônico | não |

## 8. Matriz de fluxos transversais

| Fluxo | Superfície | Classificação |
|---|---|---|
| abrir Portal | shell/manifest/RBAC | P0 |
| navegar TopBar | todas as páginas | P0 |
| produto → desenho/BOM/parents | Produtos | P0 |
| LMP → produto | LMP/Produtos | P0 |
| tarefa → owner | Minhas tarefas | P0 |
| sala → objeto vinculado | Sala | P0 |
| Controle MP | Portal → my-requests | HERANÇA |
| TRANSFORMA+ | Portal → Transformômetro | HERANÇA |
| F5/back-forward | listas/detalhes | P0 |
| loading/empty/error/forbidden | todas | P0 |
| ajuda contextual | todas user-facing | P0 |
| dark/light/mobile | todas | P0 |
| depreciação legados | rollout | P0 |

## 9. Riscos materiais

- drift entre dashboard legado e novo Portal;
- acoplamento indevido a payload da `api-delpi`;
- worklist inventar estado fora do owner;
- bypass de RBAC por agregação;
- FILESERVER indisponível/lento;
- exposição de paths físicos;
- excesso de fan-out na home;
- perda de filtros/deep links na migração;
- duplicação de componentes que já existem no kit;
- quebra de tema/MFE por CSS global;
- cutover antes da paridade.

## 10. Roadmap E*.S*

# E0 — Baseline e fundação documental

## E0.S1 — Revalidar inventário real

**Objetivo:** congelar baseline técnico antes de criar código.

**Requisitos cobertos:** RQ-01, RQ-18, RQ-19.

**Fazer:**
- reler regras `.cursor` aplicáveis;
- inventariar manifests, rotas, APIs e testes de `dashboard-engineering`, `dashboard-lmps`, `commercial`, `supplies`, `my-requests`, Transformômetro;
- mapear consumers dos contratos LMP/produtos/desenhos;
- registrar drifts entre docs e runtime.

**Não fazer:** implementar portal.

**Teste/evidência:** checklist de inventário com paths reais e estados `CONFIRMADO_*`.

**Pronto quando:** nenhuma decisão P0 depende de hipótese material não registrada.

**Commit sugerido:** `docs: consolidar baseline do Portal de Engenharia`

## E0.S2 — Travar ADR de bounded context

**Objetivo:** formalizar `plugins/engineering` + `engineering-api` e boundaries.

**Requisitos:** RQ-01, RQ-14, RQ-15.

**Fazer:** criar ADR com owner, dependências, APIs externas, persistence e proibições.

**Não fazer:** compartilhar domain/use case entre APIs.

**Teste:** revisão arquitetural + grep conceitual dos boundaries propostos.

**Pronto quando:** owner e dependency direction estiverem inequívocos.

**Commit:** `docs: definir bounded context do Portal de Engenharia`

# E1 — Fundação do módulo

## E1.S1 — Criar `engineering-api`

**Objetivo:** serviço de domínio/BFF com health, auth, composição e estrutura Clean Architecture.

**Requisitos:** RQ-14, RQ-15.

**Fazer:** estrutura domain/application/interface/infrastructure, auth compartilhada, erros, logs, testes base.

**Não fazer:** endpoints de negócio especulativos nem regra no controller.

**Teste:** unit + integração health/auth + lint.

**Pronto quando:** serviço roda isolado e rejeita JWT/permissão inválidos.

**Commit:** `feat: criar fundação da API de Engenharia`

## E1.S2 — Criar `plugins/engineering`

**Objetivo:** MFE federado com shell e rotas vazias tipadas.

**Requisitos:** RQ-01, RQ-02, RQ-13, RQ-17.

**Fazer:** Module Federation canônico, façade `engineeringUi.ts`, TopBar na ordem travada, page shell, theme/responsive.

**Não fazer:** CSS do kit no MFE; fetch direto `api-delpi`.

**Teste:** build, tsc, smoke standalone e federado, claro/escuro/mobile.

**Pronto quando:** Portal carrega o MFE e navega pelas seis rotas principais.

**Commit:** `feat: criar shell do Portal de Engenharia`

## E1.S3 — Manifesto, gateway e RBAC base

**Objetivo:** integrar o app à plataforma.

**Requisitos:** RQ-01, RQ-15.

**Fazer:** manifesto v2, permissões mínimas, routes, Compose/gateway/scripts conforme padrão sequencial.

**Teste:** manifest validation, remoteEntry 200, `/me/apps`, acesso permitido/negado.

**Pronto quando:** app aparece somente para usuário autorizado.

**Commit:** `feat: integrar Portal de Engenharia à Minha DELPI`

# E2 — Início e catálogo de ferramentas

## E2.S1 — Home BFF

**Objetivo:** criar composição `/home` com degradação parcial.

**Requisitos:** RQ-01, RQ-06, RQ-11.

**Fazer:** DTO interno, adapters por fonte, timeout/partial_sources, testes positive/sibling/negative.

**Pronto quando:** uma fonte indisponível não derruba toda a home quando a semântica permitir.

**Commit:** `feat: compor início do Portal de Engenharia`

## E2.S2 — Home UI

**Objetivo:** prioridades + ferramentas + atividade recente.

**Requisitos:** RQ-03, RQ-07, RQ-08, RQ-09, RQ-12, RQ-13.

**Fazer:** cards pelo kit; Produtos/Controle MP/Documentos/Desenhos/NC/TRANSFORMA+; permission visibility.

**Teste:** loading/empty/partial/error/forbidden + mobile/theme.

**Pronto quando:** ferramentas aparecem conforme RBAC e CTAs abrem rotas corretas.

**Commit:** `feat: criar início e ferramentas da Engenharia`

# E3 — Visão geral

## E3.S1 — Contrato agregado de overview

**Objetivo:** compor SI + LMP + TRANSFORMA+ sem recalcular owner.

**Requisitos:** RQ-11.

**Teste:** score SI preservado, downstream parcial, filtros.

**Commit:** `feat: compor visão geral da Engenharia`

## E3.S2 — Dashboard Visão geral

**Objetivo:** entregar KPIs, tendências e atenções.

**Teste:** payload real tipado, URL filtros, charts responsive, empty/error.

**Commit:** `feat: criar visão geral do Portal de Engenharia`

# E4 — Minhas tarefas

## E4.S1 — Agregador de worklist

**Objetivo:** unificar tarefas sem assumir workflow.

**Requisitos:** RQ-06, RQ-07, RQ-15.

**Fazer:** adapters por owner; `deep_link`; `allowed_actions` somente comprovadas.

**Teste:** tarefa LMP + tarefa MP + fonte sem acesso + owner indisponível.

**Commit:** `feat: agregar minhas tarefas de Engenharia`

## E4.S2 — Página Minhas tarefas

**Objetivo:** filtros, contadores, tabela/lista e deep links.

**Teste:** query↔estado, F5/back, mobile, forbidden, empty.

**Commit:** `feat: criar worklist pessoal de Engenharia`

# E5 — Sala de interação

## E5.S1 — Modelo/persistência da Sala

**Objetivo:** rooms/messages/participants/mentions/read-state/attachments com migrations imutáveis.

**Requisitos:** RQ-05, RQ-15.

**Não fazer:** usar Core DB para dados de colaboração de domínio.

**Teste:** repository/use cases + autorização membro/não membro.

**Commit:** `feat: modelar sala de interação da Engenharia`

## E5.S2 — API da Sala

**Objetivo:** CRUD controlado, mensagens, reações, participantes, anexos.

**Teste:** positivo, sibling contexto diferente, negativo acesso indevido, tamanho/extensão de anexo.

**Commit:** `feat: expor contratos da sala de interação`

## E5.S3 — Realtime e notificações

**Objetivo:** persistir primeiro, publicar depois do commit; notificar menções/mensagens conforme preferências.

**Teste:** commit→evento, rollback sem evento, reconnect, read/unread.

**Commit:** `feat: integrar realtime da sala de Engenharia`

## E5.S4 — UI da Sala

**Objetivo:** reproduzir padrão maduro do Portal Comercial via kit.

**Fazer:** inbox, thread, contexto “Neste chat”, composer, anexos, mentions, estados.

**Teste:** sem sala, sala aberta, mobile, keyboard, envio/erro/retry, F5 deep link.

**Commit:** `feat: criar sala de interação do Portal de Engenharia`

# E6 — LMPs

## E6.S1 — BFF LMP

**Objetivo:** encapsular `/engineering/lmps/*` atrás do `engineering-api`.

**Requisitos:** RQ-04, RQ-14, RQ-18.

**Teste:** contrato summary/list/detail/history/flow/NC; timeout/error mapping.

**Commit:** `feat: integrar contratos de LMP à API de Engenharia`

## E6.S2 — Lista/painel LMP

**Objetivo:** paridade funcional com listagem atual.

**Teste:** filtros URL, KPIs, charts, paginação, detalhe, F5.

**Commit:** `feat: migrar painel de LMPs para o Portal de Engenharia`

## E6.S3 — Detalhe LMP

**Objetivo:** resumo, produtos, histórico, Gantt e NCs.

**Fazer:** reutilizar comportamento comprovado do legado; produto tem CTA para ferramenta Produtos.

**Teste:** positive/sibling/negative, detalhe inexistente, history empty, Gantt.

**Commit:** `feat: migrar detalhe de LMP para o Portal de Engenharia`

# E7 — Produtos

## E7.S1 — BFF de produtos

**Objetivo:** adapter interno para pesquisa e dimensões do produto.

**Requisitos:** RQ-03, RQ-14, RQ-15.

**Teste:** busca código/descrição/part number; produto inexistente; custo sem permissão.

**Commit:** `feat: integrar dados de produtos à Engenharia`

## E7.S2 — Pesquisa de produtos

**Objetivo:** busca rápida e atalhos Estrutura/Onde é usado/Desenho/Estoque.

**Teste:** URL query, empty, erro, mobile, teclado.

**Commit:** `feat: criar pesquisa de produtos no Portal de Engenharia`

## E7.S3 — Ficha 360°

**Objetivo:** abas de dados, estrutura, parents, desenho, estoque, fornecedores e custos permitidos.

**Teste:** dimensões independentes com partial failure; deep links; RBAC sensível.

**Commit:** `feat: criar ficha técnica de produtos`

# E8 — Desenhos e documentos técnicos

## E8.S1 — Biblioteca de desenhos via BFF

**Objetivo:** expor catálogo/metadados/PDF sem path físico.

**Requisitos:** RQ-09, RQ-20.

**Teste:** código/revisão/variant, PDF 200, inexistente 404, traversal negativo.

**Commit:** `feat: integrar biblioteca de desenhos ao Portal de Engenharia`

## E8.S2 — UI Biblioteca de desenhos

**Objetivo:** catálogo + preview PDF.

**Teste:** filtros, paginação, inline preview, download autorizado, mobile.

**Commit:** `feat: criar biblioteca de desenhos da Engenharia`

## E8.S3 — Adapter de bibliotecas FILESERVER

**Objetivo:** criar abstração allowlisted read-only para documentos técnicos.

**Requisitos:** RQ-10, RQ-20.

**Fazer:** raízes configuradas server-side, IDs opacos, extensão/tamanho, resolve seguro, observabilidade.

**Não fazer:** aceitar path do cliente ou listar raiz arbitrária.

**Teste:** arquivo permitido, extensão proibida, traversal, share ausente, arquivo grande.

**Commit:** `feat: criar acesso seguro a documentos técnicos`

## E8.S4 — UI Documentos técnicos

**Objetivo:** biblioteca pesquisável por contexto.

**Teste:** filtros, download, preview suportado, unavailable state, RBAC.

**Commit:** `feat: criar biblioteca de documentos técnicos`

# E9 — Integrações de aplicações

## E9.S1 — Controle de MP

**Objetivo:** card/página-hub + resumo permitido + deep links para `my-requests`.

**Requisitos:** RQ-07.

**Não fazer:** duplicar formulário/fila/workflow.

**Teste:** create/update/mine/work-queue com usuário autorizado e sem permissão.

**Commit:** `feat: integrar Controle de MP ao Portal de Engenharia`

## E9.S2 — TRANSFORMA+

**Objetivo:** resumo e CTA para Transformômetro.

**Requisitos:** RQ-08.

**Teste:** contrato real, erro downstream, deep link.

**Commit:** `feat: integrar TRANSFORMA+ ao Portal de Engenharia`

# E10 — Ajuda e acabamento

## E10.S1 — Página Ajuda

**Objetivo:** entregar a sexta rota principal da TopBar.

**Requisitos:** RQ-02, RQ-12.

**Fazer:** busca/localização de conteúdo, categorias, glossário, FAQ, suporte.

**Não fazer:** expor detalhes técnicos de API/TOTVS ao usuário.

**Teste:** navegação TopBar, conteúdo, mobile, teclado, tema.

**Commit:** `feat: criar ajuda do Portal de Engenharia`

## E10.S2 — Help sync transversal

**Objetivo:** tooltips/helps de negócio em todas as features relevantes.

**Teste:** auditoria de páginas user-facing contra `feature-help-sync`.

**Commit:** `docs: sincronizar ajuda do Portal de Engenharia`

# E11 — Observabilidade, performance e segurança

## E11.S1 — Budgets de integração

**Objetivo:** impedir que home/overview/worklist degradem por fan-out.

**Fazer:** medir latência, cache onde seguro, timeout, métricas e partial sources.

**Teste:** downstream lento/falhando, cache hit/miss, sem retry indevido.

**Commit:** `perf: fortalecer integrações do Portal de Engenharia`

## E11.S2 — Security review

**Objetivo:** validar JWT, RBAC, downloads, uploads, FILESERVER e websocket.

**Teste:** 401/403, IDOR, traversal, MIME, upload limits, room membership.

**Commit:** `security: revisar boundaries do Portal de Engenharia`

# E12 — Cutover e depreciação

## E12.S1 — Paridade `dashboard-engineering`

**Objetivo:** provar que Visão geral substitui experiência antiga.

**Teste:** matriz campo/KPI/filtro/deep link + homologação usuária.

**Commit:** `test: validar paridade do dashboard de Engenharia`

## E12.S2 — Paridade `dashboard-lmps`

**Objetivo:** provar lista/detalhe/Gantt/NC antes de redirecionar.

**Teste:** amostra real + positive/sibling/negative + F5/back.

**Commit:** `test: validar paridade de LMPs no novo Portal`

## E12.S3 — Soft cutover

**Objetivo:** Portal vira entrada preferencial, preservando rollback.

**Fazer:** menus/deep links/redirects compatíveis; não remover legado ainda.

**Commit:** `chore: direcionar Engenharia para o novo Portal`

## E12.S4 — Hard cutover

**Objetivo:** remover tiles/apps legados somente após janela de segurança e aprovação.

**Teste:** manifest/routes/RBAC/redirects/smoke produção.

**Commit:** `chore: concluir cutover do Portal de Engenharia`

# E13 — Verify-final

## E13.S1 — Validação técnica final

**Fazer:** builds, testes APIs, manifest, gateway, remoteEntry, smoke federado, light/dark/mobile, F5/back, RBAC, FILESERVER e integrações.

## E13.S2 — Validação do objetivo original

Tabela PASS/FAIL para RQ-01…RQ-20, com evidência. Nenhum requisito material pode terminar sem evidência ou justificativa explícita.

## E13.S3 — Revisão adversarial

Responder antes do fechamento:

- algum owner foi duplicado?
- algum MFE chama `api-delpi` diretamente?
- tarefa agregada inventa workflow?
- Sala substitui evento oficial?
- path físico do FILESERVER chega ao browser/log?
- algum componente do kit foi copiado?
- algum filtro/detalhe perde estado em F5?
- algum acesso indireto contorna RBAC do owner?
- legados foram removidos antes da paridade?
- Ajuda ficou sincronizada?

## 11. Rastreabilidade requisito → etapa → teste

| Requisito | Etapas principais | Prova |
|---|---|---|
| RQ-01 | E0-E2 | manifest + smoke + home |
| RQ-02 | E1, E10 | TopBar + route tests |
| RQ-03 | E2, E7 | catálogo + Produtos |
| RQ-04 | E6 | paridade LMP |
| RQ-05 | E5 | API + realtime + UI |
| RQ-06 | E4 | agregador + UI |
| RQ-07 | E9 | deep links my-requests |
| RQ-08 | E9 | integração Transformômetro |
| RQ-09 | E8 | catálogo/PDF |
| RQ-10 | E8 | biblioteca allowlisted |
| RQ-11 | E3 | SI preservado |
| RQ-12 | E10 | Ajuda + help audit |
| RQ-13 | E1-E10 | audit kit/CSS |
| RQ-14 | E0-E9 | grep bypass + contracts |
| RQ-15 | todas APIs | 401/403 + scope |
| RQ-16 | E4-E8 | URL/F5/back |
| RQ-17 | todas UI | theme/mobile/keyboard |
| RQ-18 | E12 | paridade + cutover |
| RQ-19 | E0, E10, E13 | docs + traceability |
| RQ-20 | E8, E11 | traversal/security |

## 12. Definition of Done do Portal

O Portal só pode ser considerado pronto quando:

- TopBar estiver exatamente na ordem aprovada;
- todas as rotas principais funcionarem por deep link;
- Produtos estiver no catálogo de ferramentas, não na TopBar;
- LMPs tiver paridade assinada;
- Sala persistir/realtime sem substituir workflow;
- Minhas tarefas apontar para owners reais;
- Controle MP usar `my-requests`;
- TRANSFORMA+ continuar no Transformômetro;
- desenhos e documentos não expuserem paths do FILESERVER;
- MFE tiver grep zero para `/apps/api-delpi`;
- RBAC backend estiver comprovado;
- loading/empty/error/forbidden estiverem cobertos;
- claro/escuro/mobile/teclado tiverem smoke;
- Ajuda estiver na TopBar e sincronizada;
- rollout e rollback estiverem testados;
- verify-final RQ-01…RQ-20 estiver PASS ou explicitamente bloqueado com evidência.

## 13. Fora do escopo até evidência real

- CAD/PDM/PLM específico não confirmado no repositório;
- edição direta de arquivo no FILESERVER;
- upload amplo para bibliotecas técnicas sem modelo de governança;
- workflow novo para Controle MP;
- reimplementação do Transformômetro;
- migração automática de legados sem homologação;
- permissões finais não comprovadas no Core;
- qualquer integração baseada somente em nome de pasta/hipótese.
