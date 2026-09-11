# Portal de Engenharia — documentação mestra

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
