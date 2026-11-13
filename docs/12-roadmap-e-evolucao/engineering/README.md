# Portal de Engenharia — documentação mestra

> **FONTE CANÔNICA ATUAL — 2026-11-13:** [Regras de produto, inconsistências e plano central PRC-TRACK](./PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md). Este documento é referência histórica/setorial: em caso de divergência sobre no-op, V1, snapshot PRC, REOPEN, RESOLVED/REMOVED, flags durante solicitação, conclusão, permissões ou critérios de aceite, **o plano central prevalece**. Trechos legados contraditórios estão **SUPERSEDED**, não são perguntas abertas nem instruções para implementar. Regras UX não conflitantes continuam válidas. `G1_ARCHITECTURE_DECISION_REQUIRED / TEST_NOT_RUN`.


> **Status:** baseline documental completa para implementação — 2026-09-11  
> **Runtime alvo:** ainda não existe `plugins/engineering` nem `engineering-api` na `main`; os documentos desta pasta descrevem o produto e a arquitetura alvo.  
> **Execução:** somente após revalidação contra código/contratos/regras `.cursor` vigentes e autorização explícita do Product Owner.

## Objetivo

Criar o **Portal de Engenharia** como ponto central de trabalho do domínio Engenharia na Minha DELPI, reunindo visão gerencial, tarefas, colaboração, LMPs, consultas técnicas e ferramentas relacionadas sem duplicar ownership de outros bounded contexts.

O Portal deve seguir a maturidade dos Portais Comercial e Suprimentos: MFE federado, BFF próprio, RBAC central, `@delpi/plugin-ui` kit-first, rotas compartilháveis, Ajuda sincronizada, estados explícitos, experiência responsiva e rollout progressivo dos legados.

## Decisões de produto travadas

1. TopBar principal: **`Início → Visão geral → Sala de interação → Minhas tarefas → LMPs → Ajuda`**.
2. **Ajuda** é jornada principal e permanece na TopBar.
3. **Produtos** não fica na TopBar; é ferramenta do Portal.
4. **LMPs** é a jornada operacional principal e candidata a absorver `dashboard-lmps` após paridade.
5. **Sala de interação** é colaboração do Portal, não workflow engine.
6. **Controle de MP** integra o fluxo canônico `my-requests` + `requests-api`; não criar segundo MFE de MP.
7. **TRANSFORMA+** continua pertencendo ao Transformômetro; o Portal apenas compõe resumo e navegação.
8. FILESERVER nunca é acessado diretamente pelo browser; bibliotecas devem ser allowlisted e expostas por backend.
9. Alvo técnico: `plugins/engineering` + `engineering-api`; com API própria, o MFE não chama `api-delpi` diretamente.
10. Legados permanecem disponíveis até paridade, cutover e rollback estarem comprovados.

## Norte do produto

```text
Portal de Engenharia
├── Início
├── Visão geral
├── Sala de interação
├── Minhas tarefas
├── LMPs
├── Ajuda
└── Ferramentas
    ├── Produtos
    ├── Controle de MP
    ├── Biblioteca de desenhos
    ├── Documentos técnicos
    ├── Não conformidades
    ├── TRANSFORMA+
    └── futuras ferramentas autorizadas
```

## Pacote documental

| Documento | Papel |
|---|---|
| [README.md](./README.md) | índice e decisões mestre |
| [ENG-REALTIME-01](./ENG-REALTIME-01-websocket-transversal-prc-plano.md) | **Implementado:** WebSocket transversal Engineering API (`/v1/realtime/ws`), PRC primeiro consumidor, invalidação + refetch nos MFEs Engineering e My Requests, AuthZ por objeto com revogação ativa — ver seção 11 do plano |
| [INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md) | ativos atuais, owners, destino e evidências |
| [SCOPE-OWNERSHIP.md](./SCOPE-OWNERSHIP.md) | escopo funcional e fronteiras de ownership |
| [PLAYBOOK-MODULO-ENGENHARIA.md](./PLAYBOOK-MODULO-ENGENHARIA.md) | regras de produto/arquitetura e invariantes de implementação |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | arquitetura current/target, camadas, fluxos, realtime e segurança |
| [WIREFRAMES.md](./WIREFRAMES.md) | navegação e contratos de experiência por página |
| [DESIGN-IA-ENGENHARIA.md](./DESIGN-IA-ENGENHARIA.md) | arquitetura de informação, shell, ferramentas e padrões UX |
| [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) | RBAC mínimo, resource scope e coexistência com permissions legadas |
| [MANIFEST-DRAFT.md](./MANIFEST-DRAFT.md) | contrato lógico do plugin e rotas do Core |
| [API-ROUTES.md](./API-ROUTES.md) | contratos alvo do `engineering-api` e deep links |
| [DATA-MODEL.md](./DATA-MODEL.md) | persistência própria, Sala e documentos técnicos |
| [INTEGRACOES.md](./INTEGRACOES.md) | gateways, downstreams, falhas, timeouts, auth e realtime |
| [KPI-FICHAS.md](./KPI-FICHAS.md) | indicadores estratégicos/operacionais e ownership de cálculo |
| [HELP-AND-ONBOARDING.md](./HELP-AND-ONBOARDING.md) | Manual, Quero→onde, FAQ, glossário e help contextual |
| [ROADMAP.md](./ROADMAP.md) | roadmap macro, ledger RQ-* e etapas E*.S* |
| [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md) | protocolo executável, gates e promoção página-a-página |
| [HOMOLOGACAO-PARIDADE.md](./HOMOLOGACAO-PARIDADE.md) | matriz de paridade, personas e evidências de homologação |
| [CUTOVER-RUNBOOK.md](./CUTOVER-RUNBOOK.md) | coexistência, soft cutover, hard cutover e rollback |
| [DECISOES-FUNCIONAIS-PENDENTES.md](./DECISOES-FUNCIONAIS-PENDENTES.md) | decisões `NOT_READY` que não podem ser improvisadas pelo executor |

### ADRs

| ADR | Decisão |
|---|---|
| [ADR-001](./adr/ADR-001-engineering-bounded-context.md) | `plugins/engineering` + `engineering-api` como bounded context/BFF do Portal |
| [ADR-002](./adr/ADR-002-fileserver-boundary.md) | FILESERVER somente por bibliotecas allowlisted/backend, read-only no MVP |
| [ADR-003](./adr/ADR-003-legacy-cutover.md) | coexistência e cutover target-first dos dashboards legados |
| [ADR-004](./adr/ADR-004-interaction-rooms.md) | Sala de interação pertence ao `engineering-api`, sem acoplamento ao Comercial |

## Evidências já confirmadas no repositório

- `plugins/dashboard-engineering` existe e publica `dashboard-engineering.view`.
- `plugins/dashboard-lmps` existe e publica `dashboard-lmps.view` e `dashboard-lmps.nc.write`.
- `api-delpi` possui contratos de Engenharia/LMP e Produtos.
- Strategic Indicators possui os IDs canônicos `engineering-projects-on-time` e `engineering-transforma-plus` e trata Engenharia como departamento consolidado.
- `docs/12-roadmap-e-evolucao/controle-mp/EVOLUCAO.md` direciona Controle de MP para `my-requests`/`requests-api`.
- Portal Comercial possui Sala de interação madura e serve como referência de UX/realtime, sem ser dependência runtime do Portal Engenharia.
- A biblioteca de desenhos já é exposta read-only por backend; não deve haver path físico no frontend.

## Arquitetura resumida

```text
Browser
  → Gateway
    → Portal Minha DELPI
      → plugins/engineering
        → engineering-api
          ├── Core API              identidade/autorização efetiva/plataforma
          ├── api-delpi             Engenharia, LMPs, Produtos, desenhos/TOTVS
          ├── strategic-indicators  metas, realizado e IDD oficial
          ├── requests-api          Controle de MP / solicitações
          ├── transformometro-api   TRANSFORMA+
          └── storage allowlisted   documentos técnicos autorizados
```

## Definition of Done transversal

Toda página user-facing deve provar: contrato/BFF no owner correto; AuthZ backend-first; kit-first; loading/empty/error/forbidden/partial quando aplicável; URL/F5/back-forward; Ajuda sincronizada; testes positive/sibling/negative; desktop/mobile; claro/escuro; teclado/foco; observabilidade; docs atualizados; smoke federado quando material.

## Regra de execução

A pasta é documentação permanente. Arquivos `.cursor/plans/*.plan.md` são estado temporário de execução e não substituem esta arquitetura. Antes de qualquer `E*.S*`, o Cursor deve reler `development-standards-index.mdc`, revalidar código/contratos atuais, classificar drifts e só executar decisões `READY_CONFIRMED` ou `READY_BOUNDED` com teste explícito.

**Primeiro próximo passo técnico quando a implementação for autorizada:** executar somente `E0.S1` de [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md), congelando o inventário real antes de criar qualquer scaffold.

## Reancoragem de estado — 12/11/2026

> Este README contém descrições históricas de arquitetura alvo (incluindo afirmações de que `engineering-api` e `plugins/engineering` ainda não existem e de que PRC seria de `requests-api`). **Esses trechos são baseline histórico, não retrato do runtime atual.** Para o PRC vigente, a **Engineering API é a autoridade do caso**, e os dois MFEs são consumidores. O [ENG-REALTIME-01](./ENG-REALTIME-01-websocket-transversal-prc-plano.md) documenta o planejamento atual do tempo real. Revisar as demais seções legadas em tarefa documental separada, sem sobrescrever decisões de ownership sem aprovação.

## Decisões funcionais PRC — acompanhamento versionado

- [PRC — Produtos acompanhados, versões confirmadas e flags transversais](./PRC-PRODUCT-TRACKING-VERSIONS-TRANSVERSAL-FLAGS-DECISIONS.md): regras de negócio consolidadas para criação/alteração, V1 em primeiro acompanhamento, snapshots oficiais após conclusão validada, flags persistentes por produto/alvo e histórico temporal. **Decisões funcionais registradas; arquitetura/persistência dependem de inventário e ratificação.**

## Especificação visual PRC — produtos acompanhados

- [PRC — Especificação visual e de interação](./PRC-PRODUCT-TRACKING-FRONTEND-VISUAL-SPEC.md): hero único com seletor Solicitações/Produtos acompanhados, tabela, ficha técnica em cards, fornecedores em tabela, flags nos campos e aba Versões com navegação/comparação. **UX TARGET; componentes, contratos e runtime ainda exigem inventário.**

- [PRC — Inventário Plugin UI e wireframes responsivos](./PRC-TRACKED-PRODUCTS-UI-COMPONENT-INVENTORY-RESPONSIVE-WIREFRAMES.md): 18 referências de componentes rastreadas ao GitHub, 7 wireframes textuais, medidas CSS PROVEN vs TARGET e matriz de QA desktop/tablet/mobile. **Documento de projeto; validação visual em browser pendente.**

## Pacote integrado de implementação — Produtos acompanhados

- [PRC-TRACK-IMPLEMENTATION-PACKAGE](./PRC-TRACKED-PRODUCTS-IMPLEMENTATION-PACKAGE-PLAN.md): plano em fases G0/G1/B1–B3/U1–U3/Q/D, matriz páginas→Plugin UI, contratos da Engineering API, gaps PROVEN (snapshot atualmente derivado de draft), dependências, 16 critérios de aceite, QA 320–1920px e gates de Coordination. **PLANNED / GATED; não autoriza implementação nem deploy.**

- [PRC-TRACK — G0 inventário e G1 decisões para Coordination](./PRC-TRACK-G0-INVENTORY-G1-COORDINATION-DECISION-PACKET.md): reancoragem no GitHub, drift do snapshot, gaps de flags por produto, 7 propostas de decisão e matriz de readiness. **G0_PARTIAL / G1_DECISION_REQUIRED; sem ratificação ou autorização de implementação.**

- [PRC-TRACK — Deliberações G1 do Product Owner (13/11/2026)](./PRC-TRACK-G1-PO-DECISIONS-2026-11-13.md): sete escolhas registradas, análise de conflitos (snapshot PRC, no-op, flags transversais e HML), 10 novos AC, pendências para ratificação da Coordination. **PO_DECISIONS_RECORDED / ARCHITECTURE_DECISION_REQUIRED**.

- [PRC-TRACK — Proposta G1 de ratificação de contratos](./PRC-TRACK-G1-CONTRACT-RATIFICATION-PROPOSAL.md): CR-01–CR-07 para Coordination, contratos B1/B2/B3, projeção RESOLVED na revisão do evento e REMOVED ausente imediatamente, cenários de HML, gates e rollback. **PROPOSED_FOR_COORDINATION / ARCHITECTURE_DECISION_REQUIRED; sem ratificação ou implementação.**
