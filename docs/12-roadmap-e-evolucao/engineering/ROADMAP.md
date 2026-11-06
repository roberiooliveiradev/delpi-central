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


## ADENDO — Product Registration & Control / Integração incremental (2026-11-06)

> **Status:** `PLANNED / ARCHITECTURE_DECISION_RECORDED / CONTRACT_AND_AUTHZ_PENDING`. Novo direcionamento do Product Owner nesta data, **não representa código implementado nem deploy**. Este adendo é o **plano mestre** do vertical na frente Portal Engenharia. Os registros anteriores D-07, RQ-07, E10.S1, `engineering/README.md` e `controle-mp/EVOLUCAO.md` refletem uma **decisão anterior** (Portal apenas deep-link para `my-requests`); onde divergirem sobre a **primeira superfície de atendimento**, prevalece este adendo **após review dos boundaries**. Não apagar o histórico ou desativar `my-requests`.

### 1. Produto e semântica de nomenclatura

- **Nome de apresentação:** **Controle e Cadastro de Produtos**.
- **Nome técnico candidato (EN-only):** `product-registration` (área do MFE existente `plugins/engineering`, não um novo MFE). Rota relativa alvo **candidata**: `/product-registration`; rota publicada sob o Portal: `/apps/engineering/product-registration`. Paths finais dependem do router/manifest/contratos vigentes no HEAD.
- **Objetivo MVP:** analistas de Engenharia encontram solicitações do Controle MP, consultam fila/detalhe, dados técnicos, fornecedores, comentários/pendências e executam somente as decisões **autorizadas pelo owner**, sem abrir o iframe para trabalhar. O **solicitante continua criando/acompanhar pelo Controle MP legado** no primeiro momento.
- **Generalização:** o nome e a composição da UX devem admitir, futuramente, diferentes tipos de cadastro de produtos. Não criar `ProductRegistrationEngine`, schemas genéricos ou outros tipos de produto sem consumer, contrato, dados e owner reais. O fluxo de matéria-prima é **um caso concreto do vertical** (`raw-material`); novos tipos só via contracts e RQ/AC próprios.
- **Idioma:** identificadores de código, routes, contracts, operationIds e novos nomes técnicos em **inglês**; textos, labels, ajuda e mensagens visíveis ao usuário em **pt-BR**. Preservar nomes legados de endpoints existentes quando consumidos; não renomear API externa para cumprir nomenclatura.

### 2. Fronteiras e arquitetura de transição

```text
Requester (phase 1)  --> Existing Control MP frontend --> Control MP API --> legacy-owned DB/workflow
Analyst (phase 1)    --> Portal Engenharia / product-registration
                       --> engineering-api (BFF / anti-corruption adapter)
                       --> Control MP API (official contract, backend-to-backend)
                       --> SAME legacy-owned request/workflow
Future governed cutover --> approved owner requests-api / my-requests (separate decision)
```

**Crítico:** a expressão do Product Owner "BFF entre duas APIs" é interpretada aqui como **adapter/BFF na `engineering-api` entre o MFE e a API legada**, com eventual migração de source para `requests-api` em fase futura; **não** uma chamada direta, circular ou sincronização bidirecional de bancos/workflows entre APIs. Não criar fluxo `Control MP API → Engineering API` como dependência de runtime sem use case oficial e contrato explícito.

**Ownership de fase 1:** Controle MP API/DB seguem owners de solicitações e suas transições; `engineering-api` é façade/consumer de contracts, nunca source of truth, workflow engine ou aprovação final. Keycloak identidade; Core apps/rotas/RBAC; Portal Engenharia UX; responsável de Engenharia decide tecnicamente conforme política validada. Os campos `allowed_actions` da fonte e autorização **live** do Core/domain (quando writes) determinam ações; papel de frontend/claim JWT/iframe SSO não habilita decisão.

**O que não fazer:** ler Postgres do Controle MP; importar internals da API Flask; duplicar workflow/status/histórico em `engineering-api`; criar mirror local authoritative; chamada direta do MFE ao Flask/TOTVS; dual-write permanente com `requests-api`; expor tokens de integração ou local JWT no browser; migração/ativação de RequestType existente sem prova de paridade.

### 3. Descobertas comprovadas / restrições de coexistência

- Repositório `roberiooliveiradev/controle_mp`: Flask/PostgreSQL/Socket.IO + React/Vite, solicitações `CRIAR/ALTERAR`, papéis `ADMIN/ANALYST/USER`, status `CRIADO / EM PROCESSO / DEVOLVIDO / FINALIZADO / REJEITADO / FRACASSADO`, chat/anexos, read-only de TOTVS; SSO embedded existente é prova de autenticação, **não** contrato BFF ou delegação de write.
- `controle-mp/EVOLUCAO.md` (2026-09-11) já planejava migração nativa para `my-requests` e descrevia paridade, `raw-material-creation/update`, ETL e cutover; essa **continua sendo a direção futura a reconciliar**, mas não a superfície inicial de analista escolhida agora.
- `plugins/my-requests` e `requests-api` possuem motor transversal, mas seed `V007 raw-material-creation` tem só `description/unit/notes` e `destination_config.adapter=none`; **não equivale ao processo real**. Não trocar a fonte prematuramente.
- `plugins/engineering/engineering.manifest.json` existe no Git (v0.2.0); inventariar seu router e os endpoints reais da `engineering-api` antes de implementar. A documentação histórica que os declara inexistentes está **STALE_EVIDENCE**.
- TÉO `PROC-0078` confirma processo de negócio Solicitação, Análise e Cadastro de Matérias-Primas, ainda com owner formal de Engenharia pendente. GLPI #1272 registra necessidade de comentários de solicitante após correção; validar paridade na nova experiência.

### 4. BFF: contratos mínimos candidatos (não tratar paths como PROVEN)

Sobre `/apps/engineering-api/v1`, prefixo de **planejamento** `/product-registration`:

| Método | Rota proposta | Responsabilidade |
|---|---|---|
| GET | `/product-registration/requests` | Fila paginada, escopo, filtros, source/status/type, total e links autorizados |
| GET | `/product-registration/requests/{requestId}` | Detalhe com itens/campos, revisões relevantes, responsáveis, comentários/anexos e ações disponíveis **quando fonte expuser** |
| GET | `/product-registration/reference-data` | Metadados/tipos/campos/fornecedores via endpoints existentes autorizados; sem conexão direta UI→ERP |
| POST/PATCH | `/product-registration/requests/{requestId}/actions` | **TARGET ONLY**: iniciar, devolver, rejeitar, finalizar; contrato explícito por ação, live AuthZ, proteção de concorrência/idempotência, audit, read-back; **não implementar na fase de leitura** |
| GET | `/product-registration/requests/{requestId}/attachments/{attachmentId}` | **TARGET ONLY**: download seguro e auditado com IDs opacos, somente se fonte oferecer autorização de anexo |

**Contract gate por operação:** owner/consumer, request/response, source IDs, map de status sem perda, casos de paginação/filtro, 401/403/404/409/422/429/502/504, timeout/retry read-only, downstream auth, Core+domain AuthZ, escopo por usuário, audit/redaction, observabilidade, idempotência (writes), optimistic concurrency e authoritative postcondition. **Verificar se Control MP oferece delegação backend-to-backend preservando identidade/autorização do usuário.** SSO local (`sso-login`) não prova essa delegação; não substituir por token de admin nem permitir que a BFF contorne autorização. Sem contrato de auth seguro: **reads/writes remotos bloqueados**, usar navegação legítima ao legado até solução aprovada. Não assumir APIs `GET /requests` ou `GET /requests/items` satisfazem filtro/autorização sem inspecionar o backend.

### 5. UX inicial, usando o MFE engineering existente

- Página/área **Controle e Cadastro de Produtos**, com **fila de solicitações**, filtros (pendência, tipo, status e busca), indicadores só quando deriváveis de fontes autorizadas, detalhe técnico, fornecedores, comunicação e evidências.
- Vistas separadas para solicitante e analista **por contexto e permissão**, mas fase 1 **não** retira solicitação do app Controle MP; oferecer caminho ao legado para solicitações novas e link ao item quando apropriado.
- Ações de decisão somente onde contrato de escrita e autorização de domínio estiverem **PROVEN**; enquanto isso, detalhe read-only e caminho à ação oficial no legado (não simular botões funcionais).
- Reaproveitar shell, composição, loading/error/empty/forbidden, breadcrumbs, tema, responsividade, deep-link/F5, `@delpi/plugin-ui` e localização PT-BR do Portal. Não criar outra TopBar/host/MFE.
- Nome técnico não determina schema/fonte; a experiência será preparada para múltiplos tipos por composição de metadados, sem abstração especulativa.

### 6. Sequência bounded e AC (sujeita a aceite de contrato antes de implementação)

| Fase | Trabalho | Gate / evidência de saída |
|---|---|---|
| PRC-0 Inventory | Verificar `origin/main`/HEAD/status/owners, router/manifests, Engineering API, Control MP API (routes+auth+AuthZ+DTO), Core e rotas, concorrência de agentes | Mapa owner→source→consumer→contract; arquivo/endpoint inventory `PROVEN`; nenhum write |
| PRC-1 Contract | Definir DTO provider-neutral, BFF read-only, estratégia de identidade/filtro e erros; confirmar owners e `RQ-PRC-*` / `AC-PRC-*` antes do diff | Contract review, AuthZ read fail-closed, risk/idempotency decision, paths revisados |
| PRC-2 Read MVP | BFF de leituras autorizadas e página do Portal com fila e detalhe (sem status-changing), link ao Controle MP | Testes de contrato, isolamento por usuário, paginação, 401/403/timeout/partial, UX PT-BR |
| PRC-3 Governed actions | Somente após prova de delegação/permissions: iniciar, devolver/retrabalhar, rejeitar, finalizar com validação oficial de código TOTVS e read-back | Live AuthZ, domain owner signoff, concurrency/idempotency, audit, testes negativos; nunca criar produto diretamente na engineering-api |
| PRC-4 Generalize | Validar contrato e navegação com categoria futura real **somente após owner e use case**, mantendo matéria-prima como baseline | Sem nomes/acoplamentos hardcoded na capa horizontal, sem categorias fictícias |
| PRC-5 Migration decision | Comparar paridade e aprovar cutover futuro para `requests-api`, ETL/dry-run, contratos, retenção e rollback; manter legacy source até decisão | Não migrar dados nem ativar dual-write nesta frente inicial |

**RQ propostos:** `RQ-PRC-01` área em Portal Engineering; `02` ingestão de solicitações legadas por BFF; `03` neutralidade da UI por tipo de cadastro; `04` contratos/segurança e não duplicação de owner; `05` fluxo de análise e decisões governadas; `06` coexistência/cutover; `07` isolamento de desenvolvimento paralelo.
**AC propostos:** `AC-PRC-01` usuário sem autorização recebe 403 no backend; `02` analista autorizado vê somente seus registros autorizados e detalhe consistente; `03` UI não busca API legado diretamente; `04` filtros/página/error states/deep links; `05` nenhum write na leitura inicial; `06` source IDs e provenance preservados; `07` tentativa de ação sem delegação validada fail-closed; `08` testes contract+integration+E2E no mesmo SHA; `09` sem regressão EVA; `10` disponibilidade/rollback e owner acceptance.

### 7. Protocolo de colaboração paralela: PRC vs VAL-01

**Agente VAL-01 em execução:** percepção tabular, SLANet/PaddleOCR, desenho×BOM na `engineering-api`. **Agente PRC:** inicialmente somente inventário/documentação; na implementação, `plugins/engineering` em diretório novo isolado da feature + adapters/rotas novas e não invasivas da `engineering-api` **depois de confirmar paths exclusivos**. A API é recurso compartilhado, não autorização para alterações concorrentes.

- Antes de cada diff: ver `origin/main`, `HEAD`, `git status`, commits posteriores e arquivos editados pelo outro agente; criar **worktree/branch isolada** para PRC. Não commitar, cherry-pick, resetar, stashear nem formatar arquivos do VAL-01.
- Reservar ownership de arquivos: PRC não toca OCR, `drawing_*`, `understanding.py`, comparador, `AnalysisJobStore`, SLANet, jobs, contratos `structure_validation.v1`; VAL-01 não toca `product-registration` e contratos Control MP.
- **Shared-touch gate:** router principal, composition root, app manifest, `engineering-api` bootstrap, auth middleware, Core permissions, plugin host, CI/deploy e documentação topo devem ter **um integrador designado**; se ambos precisarem do mesmo arquivo, registrar colisão, serializar merge e revalidar testes depois. Não editar simultaneamente.
- Deploy: build de um SHA fixo e conferido, diff de todos os commits incluídos, regressão EVA e PRC, AuthZ, rollback da versão anterior, autorização Ops; nunca promover `origin/main` mutável que contenha código de outro agente não validado.
- Evidência final: `BASE_SHA / FINAL_SHA / FILES_CHANGED / FOREIGN_COMMITS / TESTS / CONTRACT_IMPACT / OUTCOME / EXECUTION_DRIFT`.

### 8. Decisão arquitetural e bloqueios

Este direcionamento **altera D-07 e o plano Controle MP anterior** (antes: analista somente em `my-requests`; agora: analista em `plugins/engineering` com façade `engineering-api` consultando a API Controle MP). Coordination reconhece o novo objetivo do usuário; **a mudança de consumer/authority operacional exige `ARCHITECTURE_DECISION_REQUIRED` para os contratos de ação, delegação de identidade e futuro cutover**. **Nenhum novo owner nem source of truth é criado nesta fase.**

Decisões pendentes: owner funcional do cadastro, política de grupos `create/process`, como o backend legado autoriza o BFF em nome do usuário, ACL por item/conversa, semântica de `FRACASSADO`, comentários pós-devolução, campos de ficha e validação de fornecedores, coexistência com `my-requests`, critérios de cutover e escala de rollout. Resolver no menor boundary antes de writes.

**Status factual:** `PLAN_UPDATED` (quando registrado no GitHub); `CODE_IMPLEMENTATION=NOT_STARTED`; `API_CONTRACT_REVIEW=PENDING`; `AUTHZ_DELEGATION=TO_INVENTORY`; `LEGACY_RUNTIME=PENDING_VERIFICATION`; `PRC_E2E=TEST_NOT_RUN`. VAL-01 continua com seu agente e seu plano independente; não alterar os seus critérios.

Inventário de código (2026-11-06), sem reescrever as decisões deste adendo: [PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md](./PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md). Esse documento substitui `AUTHZ_DELEGATION=TO_INVENTORY` e `LEGACY_RUNTIME=PENDING_VERIFICATION` pela evidência das rotas, do workflow e do bloqueio de delegação. A implementação continua não autorizada por este adendo.


## ADENDO — Native Product Registration / fluxo de criação e alteração por campo (2026-11-06)

> **Status:** `TARGET / ARCHITECTURE_DECISION_REQUIRED` para ownership e fonte operacional; `PLANNED` para implementação; **não implementado, não implantado**. Direção funcional mais recente do Product Owner. **Este adendo substitui como target de produto o adendo anterior de BFF legado**; o inventário [PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md](./PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md) permanece evidência de paridade, **não** contrato a copiar. Preservar o registro das decisões anteriores para rastreabilidade, sem implementar as fases PRC-1a/PRC-2 anteriores automaticamente.

### 1. Decisão de produto e escopo

- Superfície: **Controle e Cadastro de Produtos**, dentro de `plugins/engineering` (`product-registration`; interface e ajuda em pt-BR; código, rotas, DTOs e IDs novos em inglês). **Primeiro tipo real:** `raw_material`. Outros tipos são `FUTURE`, sem generalizações hipotéticas que criem um segundo engine.
- Uma solicitação pode chegar do Controle MP, de uma futura porta do Portal ou de outra aplicação autorizada. **Origens abertas por contrato de intake**, sem aceitar writes anônimos ou payload arbitrário. No primeiro ciclo, o solicitante **continua no fluxo existente**, enquanto a plataforma nativa é construída e homologada. O mecanismo definitivo de ingestão/cutover exige owner e AuthZ explícitos.
- No Portal Engenharia, o analista encontra fila de **casos de cadastro**, examina ficha/proposta, trabalha nos campos, obtém pareceres opcionais da EVA, decide e registra o resultado. **Não portar chat ou Socket.IO como modelo de atendimento**. A comunicação de pendência pode usar campos de motivo, comentário/timeline e notificação governada.
- **Criação `create`:** solicitante informa **campos de entrada obrigatórios para solicitar**, que podem ser menos que os obrigatórios para o cadastro oficial (descrição inicial, fornecedores, `compart number` informado pelo PO e demais campos após validação do inventário e owner). A Engenharia completa/normaliza a ficha e valida antes de decidir. **Não inventar nome/mapeamento do `compart number`: `TO_CONFIRM_WITH_OWNER`.**
- **Alteração `update`:** solicitante localiza o cadastro vigente e escolhe **apenas os campos específicos** que quer modificar. Recebe a ficha de referência read-only, informa novos valores e justificativa. **Não exigir reenviar ou editar todos os campos**. O pedido carrega `baseRevision` e conjunto explícito de alterações; nenhum campo não selecionado sofre mutação. A Engenharia revisa os efeitos correlatos antes de aprovar.
- **Busca de cadastros semelhantes e sugestões para o solicitante** = `FUTURE`, **fora do MVP**. EVA no atendimento do analista pode sugerir revisão de descrição/campos com `DRAFT/CANDIDATE`, fonte, incerteza e aceite humano; indisponibilidade da EVA não bloqueia fluxo humano se política de validação permitir.

### 2. Modelo e fluxo alvo (contratos conceituais, não schema aprovado)

```text
origin(s) -> governed intake -> registration request -> engineering case/queue
  -> technical draft -> optional EVA candidate -> authorized technical decision
  -> confirmed official registration/change (owner ERP/domain)
  -> immutable technical record revision + field-change ledger + audit
```

Separar entidades e authorities:
- `ProductRegistrationRequest`: request id opaco, `externalSource`, `externalRequestId` + `sourceItemId`, `requestType`, `productId` quando update, `requesterSubject` (Keycloak sub ou identidade de origem mapeada), timestamp, payload recebido, evidência e idempotency key.
- `ProductRegistrationCase`: fila, responsável, estado, decisões, justificativas, eventos, referências de aprovações e controlos de concorrência. **Owner do workflow a decidir comparando `requests-api` vs necessidade específica de Engenharia; não duplicar Request Engine por padrão.**
- `TechnicalProductRecord`: projeção/catálogo técnico versionado, **não substitui TOTVS como autoridade do cadastro oficial**.
- `TechnicalProductRevision`: snapshot JSONB completo imutável por revisão, autor, motivo, data, request/case de origem, `baseRevision`, `sourceRevision`, `officialProductCode` se confirmado, status `draft|approved|published` conforme authority; diferenças por caminho do campo (`fieldPath`, `before`, `after`, autoria e decisão) com auditoria append-only.
- Persistir colunas tipadas para ids, status, actor, timestamps, constraints e chaves de busca; `JSONB` para ficha variável e propostas; validar schemas versionados conforme tipo. Impedir path arbitrário, alteração de campos proibidos, mass assignment e substituição cega do JSON completo.
- **Criação e update não se confundem**: update usa change set contra revisão conhecida, com `compare-and-set`/ETag; campos não solicitados permanecem iguais; concorrência retorna conflito `409` com rebase explícito; nunca last-write-wins silencioso.
- **Aprovação técnica ≠ criação oficial no ERP**: somente marcar `completed`/publicar revisão quando o owner confirmar a operação ou código oficial exigido pela política. Se há etapa externa pendente, registrar estado de integração e não inventar êxito. MVP pode limitar integração a validação/confirmação de cadastro oficial, se escrita ERP não autorizada.
- Estados candidatos: `submitted` → `in_progress` → `under_review` → `completed`; `needs_information` com correção/retorno e `rejected`. Definir transições, `allowedActions`, autorização e audit no backend antes da implementação. Idempotência do intake por `(externalSource,externalRequestId,sourceItemId)` ou equivalente governado, sem inventar formato de identificador.

### 3. Portas de entrada e distribuição de responsabilidades

| Capacidade | Decisão de direção | Gate necessário |
|---|---|---|
| Solicitação por aplicações diversas | Endpoint/intake versionado com source provenance e idempotência | AuthN/AuthZ de cada source, ownership das filas, contrato e anti-replay |
| Fila e análise técnica | Portal Engenharia; domínio/serviço autorizado | Ownership de caso/workflow face à `requests-api` |
| Ficha técnica e revisão JSONB | Capacidade nativa de Engenharia **se aprovada como owner** | Modelo/schemas, retenção, integridade, política de publicação |
| Validação EVA | Assistência sob demanda, `DRAFT/CANDIDATE` | permissões de leitura, grounding, audit, ausência de publicação pela IA |
| Produto oficial | TOTVS / Domain API oficial | adapter aprovado, verificação pós-condição e decisão de owner |
| Migração histórico legado | ETL controlado, dry-run/apply idempotente e cutover | paridade, identidade `sub`, anexos, revisões, hashes, retenção, rollback |
| Solicitações corporativas transversais | `requests-api` já existente | **Abstraction Gate**: demonstrar por que sua extensão não atende; decisão explícita antes de criar workflow alternativo |

### 4. Primeira entrega funcional (MVP) e fora de escopo

**MVP:** intake governado de `raw_material` `create/update` (ou piloto com origem controlada), fila, detalhe, campos de criação obrigatórios de entrada, seleção de campos na alteração, ficha técnica em draft, edição/validação por analista, histórico de caso, assistência EVA opcional (sem dependência bloqueante), decisão humana e snapshots/revisões JSONB com diffs por campo, confirmação governada do resultado oficial e auditoria.

**Não-MVP:** busca preventiva de matérias-primas semelhantes para solicitante; sugestões automáticas de preenchimento ao usuário; novos tipos de produtos; substituição imediata do Controle MP; migração de produção sem paridade; write direto no ERP; chatbot; novos serviços/frameworks sem Abstraction Gate.

### 5. RQ e critérios de aceite específicos (a refinar antes de código)

- `RQ-PRC-08`: `create` exige apenas intake mandatory fields aprovados por tipo; separá-los de mandatory fields de cadastro/publicação.
- `RQ-PRC-09`: `update` por campo(s) selecionado(s), sem reenvio da ficha integral; base revision e before/after rastreáveis.
- `RQ-PRC-10`: revisão JSONB imutável + diff por campo + ator, timestamp, motivo, origem e link à solicitação.
- `RQ-PRC-11`: workflow mínimo de análise e decisão governadas; `allowedActions` server-side, idempotência e controle de concorrência.
- `RQ-PRC-12`: EVA fornece sugestões opcionais, nunca aprova/publica; validade da fonte e incerteza legíveis.
- `RQ-PRC-13`: sistema de origem substituível por intake e migração futura governada; sem dual-write permanente.
- `AC-PRC-11`: create com campos obrigatórios de solicitação passa; falta de obrigatório falha; publicação exige critérios oficiais separados.
- `AC-PRC-12`: update de um campo altera exatamente o caminho autorizado, mantém todos os demais bytes/valores semanticamente idênticos e gera um único conjunto de diferenças auditável; tentativa em campo proibido falha.
- `AC-PRC-13`: update em `baseRevision` obsoleta retorna conflito e nenhuma escrita; re-submissão idempotente não cria solicitação duplicada.
- `AC-PRC-14`: revisão `N` e `N+1` podem ser recuperadas, comparadas e auditadas; a rejeição não modifica a versão vigente.
- `AC-PRC-15`: usuário sem permissão não lê/edita/aprova; backend fail-closed, inclusive por origem.
- `AC-PRC-16`: EVA desligada/indisponível não gera aprovação e não impede fluxo humano autorizado.
- `AC-PRC-17`: nenhum `completed` falsamente indica produto oficial criado; exige read-back/evidência do owner.
- `AC-PRC-18`: dados legados e anexos preservados com reconciliação de IDs/contagens/checksums antes do cutover; rollback testado.

### 6. Sequência de desenvolvimento revisada e gates de execução

1. **PRC-N0 — Architecture Gate:** revisar evidências de `requests-api` já inventariadas e escolher owner real de intake/workflow/caso vs ficha técnica; resolver `ARCHITECTURE_DECISION_REQUIRED` sem criar novo source of truth por vontade do frontend. Verificar código/HEAD/runtime, owners, status de outra worktree.
2. **PRC-N1 — Contract & Schema:** fechar contratos canônicos `create/update`, proposta de patch campo-a-campo, campo `compart number`, schemas versionados, estados, AuthZ, RQ/AC e envelope de erros. Separar `request`, `draft`, `revision` e `officialPublished`.
3. **PRC-N2 — Domain/Persistence:** implementar somente no owner aprovado tabelas/migrations JSONB, histórico append-only, diffs, CAS, idempotência e testes; nenhum acesso ao DB legado em runtime.
4. **PRC-N3 — API/Intake:** criar ports/adapters oficiais para sources e ERP; ingestão idempotente e fila com AuthZ; testes de contrato e segurança.
5. **PRC-N4 — UI do Portal:** fila e detalhe técnico, criação/alteração por campos e histórico, kit-first, EN code/PT-BR UI, deep-links, responsividade, estados e permission gate.
6. **PRC-N5 — Validation/Official Outcome:** integração assistiva EVA candidate e validação técnica governada, confirmação do registro oficial sem inventar sucesso, audit e read-back.
7. **PRC-N6 — Legacy Parity & Migration:** comparar corpus de registros reais, fazer ETL dry-run, preservar ids legados e `sub`, anexos, contagens/revisões/hashes, dual-run controlado, soft/hard cutover e retenção do legado **somente com aceite funcional e Ops**.

**Regra de execução paralela:** VAL-01 permanece dona da percepção documental; PRC não altera OCR/SLANet/drawing/AnalysisJobStore. Os pontos compartilhados `engineering-api/main.py`, `config.py`, router do MFE, Core/RBAC, CI e deploy só podem ser integrados serialmente por integrador designado e testados no SHA reunido, sem comitar diff alheio. Use diretórios de feature novos; evitar trabalhar no checkout sujo da EVA. Sem autorização para deploy neste adendo.

### 7. Estado e decisões pendentes

`PRODUCT_DIRECTION=CONFIRMED_BY_PO`; `ARCHITECTURE_OWNERSHIP=DECISION_REQUIRED`; `IMPLEMENTATION=NOT_STARTED`; `MIGRATION=PLANNED`; `EVA_ASSISTED_VALIDATION=TARGET`; `SIMILARITY_SEARCH_FOR_REQUESTER=FUTURE`.

Pendências objetivas: ownership de workflow frente a `requests-api`, autoridade de publicação ERP e forma de confirmação, `compart number` significado/tag, campos required por tipo e ator, schema JSONB versionado, semântica de status, política de retenção e reconciliação, IAM/ACL dos múltiplos canais, concorrência e MVP exato de integração EVA. Antes de implementar, registrar o contrato e obter o aceite dos owners técnicos competentes.


## ADENDO — Product Registration Engineering-first, sem Requests API na fase inicial (2026-11-06)

> **Direção atual do Product Owner / TARGET.** Este adendo tem precedência sobre indicações anteriores de integrar ou reutilizar `requests-api` durante PRC-N0–N5, e sobre o BFF para a API Flask do Controle MP. É uma definição de escopo, **não** evidência de implementação nem aprovação de mudança de authority. Preservar os adendos anteriores como histórico e não tratá-los como próximos passos executáveis.

### Escopo de primeira implementação

- Desenvolver `product-registration` **inteiramente no bounded context de Engenharia**, com UI no `plugins/engineering` e aplicação, domínio, HTTP, persistência e adapters próprios sob `engineering-api`. **Não conectar, consultar, importar, criar adapter para, nem depender da `requests-api` ou do MFE `my-requests` no MVP.** Também não construir BFF runtime para a API Flask do Controle MP.
- Duas interfaces externas explícitas do novo módulo: **porta de entrada** versionada para receber solicitações de criação/alteração, com identidade do solicitante e origem, autenticação/autorização, validação de schema, deduplicação/idempotência, source IDs e provenance; **porta de saída** versionada para disponibilizar/comunicar status, decisões e resultado a consumidores autorizados. Contratos de saída devem especificar se serão consulta, eventos/outbox ou callback; não presumir entrega a outro sistema sem consumidor e autorização identificados.
- Dentro da `engineering-api`, a Engenharia gerencia recebimento, fila, atendimento, montagem da ficha, validação humana, histórico e versões. A EVA só produz sugestões `DRAFT/CANDIDATE`, nunca decisão final. O TOTVS/Domain API segue a autoridade oficial para cadastro/alteração real do produto; a ficha versionada da Engenharia é registro técnico operacional e **não** substitui cadastro oficial.
- `create`: intake com apenas campos obrigatórios de solicitação (descrição inicial, fornecedores, "compart number" a confirmar, outros campos após definição de schema), posteriormente completados/validados pelo analista; distinguir required de intake e de publicação.
- `update`: selecionar apenas campos a mudar contra ficha vigente, `baseRevision`, change set explícito e justificativa; preservar demais campos, CAS/409 quando stale e diff por campo no histórico.
- Persistência no contexto da Engenharia: IDs/status/atores/códigos em colunas tipadas; payload técnico em JSONB com schema versionado; snapshots imutáveis por revisão, before/after, motivo, ator, source, tempo, auditoria append-only.
- O Controle MP legado permanece operante e sem migração automática enquanto o produto nativo é desenvolvido. A conexão futura à `requests-api` e a migração/ETL/cutover serão **programas posteriores, com decisão e contrato próprios**; não permitir dual-write.
- Busca de semelhantes durante a solicitação e ampliação para outros tipos de produtos são `FUTURE`.

### Arquitetura alvo da primeira etapa

```text
Authorized source(s) -> Engineering API / product-registration intake (versioned)
  -> Engineering-owned request/case and queue (governed AuthZ)
  -> technical draft (JSONB) -> optional EVA candidate -> authorized analyst decision
  -> official ERP/domain verification/operation only via approved contract
  -> immutable revision + audit
  -> Engineering API / product-registration outbound contract (authorized consumers)
Portal Engenharia / product-registration UI -> Engineering API only
Requests API / My Requests -> NO RUNTIME INTEGRATION IN MVP
Legacy Controle MP -> NO RUNTIME INTEGRATION IN MVP
```

### Decisão, contrato e segurança

A escolha de concentrar intake/workflow/registro técnico na `engineering-api` muda os boundaries descritos nos planos anteriores e exige **`ARCHITECTURE_DECISION_REQUIRED` em Coordination** para formalizar ownership de solicitações de cadastro em Engenharia (sem alterar propriedade da verdade oficial do produto). O gate não é autorização para conectar a `requests-api` agora: a decisão deve avaliar e documentar o trade-off, mas o escopo autorizado é Engineering-only. Antes de implementar: definir contratos de entrada/saída (consumer, request/response, errors, AuthN/AuthZ, limits, observabilidade, idempotência, postcondition e compatibilidade), estados/transições, data model, aprovação técnica, política de publicação, rollback/revoke e RQ/AC verificáveis.

**Concorrência de agentes:** PRC não toca código da percepção documental/OCR/SLANet/VAL-01; shared files (`main.py`, `config.py`, router do Portal, manifests, Core/RBAC e deploy) serão integrados serialmente e testados num SHA conjunto. Nenhum deploy ou alteração de código é autorizado por este adendo.


## ADENDO — Contrato de conclusão com verificação TOTVS e Part Number (2026-11-06)

> **Decisão funcional do Product Owner / TARGET**, posterior ao adendo Engineering-only. Este texto prevalece no MVP onde houver divergências anteriores. **Implementação ainda não comprovada**. Nome correto: **Part Number**, não "compart number". Não confundir Part Number do fornecedor com código interno do produto.

### Fluxo confirmado

1. Uma origem autorizada envia à porta **intake** versionada da `engineering-api` uma solicitação `create` ou `update`, com identidade/origem, idempotência e valores do inventário. No primeiro MVP **não integrar** `requests-api`, `my-requests` ou API Controle MP, nem exigir um formulário produtivo do solicitante. Pode haver **harness/formulário de teste restrito** para chamadas autenticadas e homologação, sem canal público de cadastro não autorizado.
2. A Engenharia persiste solicitação, caso, dados propostos e proveniência no domínio Engineering-only; analista recebe em fila, atende e prepara ficha técnica `JSONB` versionada. Não portar chat do legado. `create` coleta os campos obrigatórios mapeados na **UI do legado**, mas não assumir que são obrigatórios na API atual: formalizar required de intake com base no catálogo de campos e validar no backend. `update` contém só campos selecionados, `baseRevision`, diferenças e motivo.
3. O analista cadastra ou altera a matéria-prima **manualmente no TOTVS**. A Engineering API **não escreve no TOTVS** no MVP. Uma ficha técnica persistida pela Engenharia é **cópia/projeção rastreável** dos atributos oficiais verificados, não fonte de verdade do produto no ERP.
4. Ao clicar **Concluir**, o backend consulta o TOTVS **via contrato de leitura oficial existente em `api-delpi` / Domain API**, nunca acesso SQL direto criado no novo módulo. Exigir confirmação **atual**: `create` requer código oficial encontrado e campos relevantes conferidos contra a ficha técnica aprovada; `update` requer código existente e **cada campo solicitado alterado** correspondendo ao valor aprovado no TOTVS, não apenas existência do código. Quando um atributo/fornecedor/Part Number não é exposto de forma verificável pela fonte, retornar `verification_unavailable` e **não concluir**; definir com owner a forma canônica de consulta, sem substituição por confiança no clique ou snapshot local.
5. Se o resultado oficial corresponder ao esperado, em transação governada registrar prova de verificação (campos conferidos, valores observados, origem, horário e correlation ID, sem segredos), decisão de analista, revisão JSONB imutável e estado `completed`. A conclusão **não cria produto no ERP**. Se ausente, divergente ou indisponível, manter solicitação aberta (`pending_erp_confirmation` ou estado aprovado no contrato), mostrar divergências por campo e permitir correção/reverificação; não publicar nova revisão como vigente.
6. **Porta outbound** versionada da Engineering API expõe status/resultado/revisão e proveniência aos consumers autorizados; opções futuras de eventos/outbox sem presumir outro sistema conectado. O fluxo permanece na Engenharia e pode integrar outras origens depois.

### Reuso do inventário e semântica de campos

- Baseline de campos legado (seção 9 do [inventário](./PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md)): `codigo_atual`, `novo_codigo`, `grupo`, `descricao`, `tipo`, `armazem_padrao`, `unidade`, `produto_terceiro`, `cta_contabil`, `ref_cliente`, `fornecedores`. Para fornecedores: `supplier_code`, `store`, `supplier_name`, **`part_number`** e `catalog_number` (opcional segundo UI antiga).
- O inventário prova que na UI antiga `grupo`, `descricao`, `tipo`, `armazem_padrao`, `unidade`, `produto_terceiro`, `cta_contabil`, `ref_cliente` e linhas completas de `fornecedores` são requeridos para envio; `codigo_atual` é de ALTERAR, `novo_codigo` de finalização de CRIAR. **Isso não equivale a regras backend de entrada aprovadas para o MVP**; transcrever campos e validar a política exata em PRC-N1, sem inventar defaults.
- Mapear aliases entre campos técnicos da Engenharia e campos retornados pelo TOTVS. O inventário aponta SB1 (`B1_DESC`, `B1_UM`, `B1_GRUPO`, `B1_TIPO`, `B1_LOCPAD`, `B1_TPMAT`, `B1_REFEREN`, `B1_CONTA`) e fornecedores SA5 (`A5_FORNECE`, `A5_LOJA`, `A5_NOMEFOR`, `A5_CODPRF` para `part_number`, `A5_CODPRCA`). Conferir cobertura efetiva do contrato `api-delpi` antes de declarar verificabilidade por campo.
- Para `update`, não exigir preenchimento da ficha toda; validar estritamente os campos alterados mais invariantes necessários. Para `create`, o schema de intake pode exigir os campos legados de criação depois de transpostos à API nativa, mas **não exige código oficial no momento da solicitação**.

### RQ/AC e stop conditions

- `RQ-PRC-14`: conclusão depende de prova de cadastro/alteração manual no TOTVS, por leitura oficial atual e comparador tipado por campo.
- `RQ-PRC-15`: preservar os campos do legado; fornecedor inclui `part_number`; separar formulário de intake de aprovação/conclusão; garantir que os campos que condicionam conclusão sejam observáveis no contrato ERP.
- `RQ-PRC-16`: endpoint intake e outbound próprios e versionados; integração com outras APIs só depois, sem runtime com `requests-api` ou Flask.
- `AC-PRC-19`: create sem código encontrado **não conclui**; com código encontrado mas campos oficiais divergentes **não conclui**; conclui somente com resultado verificado conforme regras e assinatura do analista autorizado.
- `AC-PRC-20`: update de um campo consulta o valor oficial desse campo e exige correspondência com o aprovado; valor divergente, read-only omisso ou fonte indisponível não alteram revisão vigente nem finalizam.
- `AC-PRC-21`: múltiplos campos/fornecedores/Part Number são conferidos em granularidade adequada; campos sem leitura confiável bloqueiam confirmação e geram erro explícito rastreável.
- `AC-PRC-22`: registro de verificação contém snapshot ou evidência mínima oficial, timestamp, campo, antes/solicitado/observado, referência à solicitação e agente; redigir sem segredos.
- `AC-PRC-23`: harness de teste de intake não concede direitos de aprovação nem expõe cadastro público.
- `AC-PRC-24`: clique repetido em Concluir é idempotente/concorrente seguro e não cria duas revisões; não há escrita ERP nesta fase.

**Bloqueador técnico a resolver em PRC-N1:** provar se os dados de SB1/SA5 necessários estão realmente disponíveis no **contrato oficial de leitura** da `api-delpi` para a Engenharia, com autorização. O legado lê SQL diretamente, mas isso **não** autoriza a nova Engineering API a fazê-lo. Não aprovar `completed` enquanto houver campos de conclusão sem verificação oficial. `ARCHITECTURE_DECISION_REQUIRED` para a autoridade do fluxo de Engenharia; não para reintroduzir Requests API nesta fase.


## Referência executável do vertical Product Registration — 2026-11-06

A especificação de rotas, payloads, PostgreSQL/JSONB, regras de transição, verificação TOTVS e critérios de aceite do MVP Engineering-only está em [PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md](./PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md). **Para este vertical, o contrato mais recente prevalece sobre exemplos e premissas históricas de BFF legado, My Requests e proibições de persistir workflow do antigo Controle MP.** Não altera outros domínios; ownership ainda exige `ARCHITECTURE_DECISION_REQUIRED` e a escrita ERP continua fora do escopo. A fase atual é documentação, sem código ou deploy.


## Plano transversal de capacidades EVA — Product Registration (2026-11-06)

A paridade **Portal/REST/EVA** integra cada slice deste vertical: para cada capacidade legítima do usuário, conectar uma ação `(entity, action)` ao **mesmo caso de uso** nas **seis tools semânticas existentes**, sem nova tool nem bypass de Core/Domain AuthZ. Matriz das 18 rotas, ações `product_registration.*`, riscos `read/execute`, PREPARE/ACT, confirmação humana para rejeição/conclusão, testes e integração serializada com VAL-01 em [PRODUCT-REGISTRATION-EVA-SEMANTIC-INTEGRATION.md](./PRODUCT-REGISTRATION-EVA-SEMANTIC-INTEGRATION.md). O documento é `TARGET/PLANNED`, não evidência de runtime. EVA não aprova produto nem escreve no TOTVS e não pode contornar a verificação oficial na conclusão. A publicação de uma rota humana requer cobertura semântica testada ou `PARITY_GAP` explicitamente bloqueado/aceito em release governado.
