# Portal Controladoria & Finanças — Fonte de navegação e estado

> **Consolidação documental: 19/10/2026.** Primeira funcionalidade: **Central de Fechamento**, processo **PROC-0072**. Documentação `TARGET`, sem implementação de runtime. Este README é o **único painel de estado vigente**; relatórios antigos de A12/A14/A15/A16 são evidências datadas, não gates atuais.

## 1. Identidade e boundaries congelados

| Contrato | Valor |
|---|---|
| Plugin / produto | `controllership-finance` |
| MFE | `plugins/controllership-finance` |
| basePath MFE | `/apps/controllership-finance` |
| BFF | `controllership-finance-api` |
| baseUrl BFF | `/apps/controllership-finance-api` |
| Permissões, **somente** | `controllership-finance.access` e `controllership-finance.manage` |

**Core API** é owner de identidade, usuários, grupos/RBAC e permissões efetivas; **Portal CF não administra permissões**. A BFF autoriza operações de negócio por capability efetiva **AND** vínculo/ownership **AND** escopo do recurso **AND** regra de negócio; fail-closed. JWT não é authority de permissions. Filial/unidade é dimensão de dado, não permission code. MFE consome sua BFF, nunca chama `api-delpi` do browser. `api-delpi` mantém regras canônicas TOTVS/Protheus e `strategic-indicators-api` mantém indicadores/metas. Integrações por ports/adapters e contratos, sem imports ou bancos de domínios alheios.

Seguir [instruções oficiais do GPT Arquiteto](../../11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md), regras `.cursor` aplicáveis e [padrão visual da plataforma](../../11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md). **`@delpi/plugin-ui` first.**

## 2. Estado **vigente** e gates

| Controle | Estado em 19/10/2026 |
|---|---|
| AS-IS PROC-0072 | `PROVEN / TÉO CLOSED_ACCEPTED` |
| Decisões de produto C2, P5-A..J, DEC-01..04, D-FINAL-02 | `TARGET / PO_APPROVED` |
| Roadmap V1 documentado | `PASS` **somente documental** |
| A12 / A14 / A15 / A16 | `INCONCLUSIVE` — revalidar com evidência de HEAD |
| `PORTAL_DESIGN_FREEZE` / `PRODUCT_CONTRACT_FREEZE` | `PENDING` para gate transversal |
| `SECURITY_MODEL_FREEZE` / `TEST_STRATEGY_FREEZE` | `PENDING` para bindings/testes |
| `FASTAPI_ARCHITECTURAL_EXCEPTION` | `REGISTERED` — [doc 45](./45-g0-excecao-fastapi-e-fechamento-gates.md); validação Arquitetura pendente |
| `DOCUMENTATION_CLOSURE_COMPLETE` | **`NO`** |
| `IMPLEMENTATION_AUTHORIZED` | **`NO`** |
| Portal runtime, smoke, integração live | `NOT_IMPLEMENTED / TEST_NOT_RUN` |

**Regra humana aprovada (D-FINAL-02):** somente pessoas aprovam. Sem revisores elegíveis ou áreas configuradas, **não** criar trava artificial de finalização, envio ou publicação. O pacote pode entrar em revisão, mas **sem evento humano real de aceite não há conclusão mensal** — o processo permanece pendente. C2 também exige aceite de cada área obrigatória existente na versão vigente, todos os pacotes aplicáveis submetidos, nenhuma clarification aberta e ausência de rejeição terminal. Veja **somente** o [contrato canônico P5 — doc 37](./37-p5-submissao-e-revisao-no-portal.md) para todas as decisões P5.

**Residuais de implementação / inventário:** Core T05 e contrato S2S da informação corporativa usada para elegibilidade de revisor; vínculo do coordenador por competência; snapshots P6, DTO/estados/eventos/OCC P5; fonte canônica ERP T03 para P3; testes de integração, UX e Help. Não são autorização para criar nova permission, CRUD/Core shadow, tabelas ou endpoints sem owner. **Busca sem resultado não prova ausência.**

## 3. Mapa curto de fontes canônicas

| Assunto | Fonte a ler |
|---|---|
| Autoridades, escopo, AS-IS e provenance | [00 — Governança](./00-governanca-e-authorities.md) · [01 — Produto/naming](./01-visao-produto-naming-e-escopo.md) · [02 — PROC-0072 AS-IS](./02-proc-0072-as-is-e-baseline.md) · [03 — Evidências](./03-evidencias-proveniencia-e-rastreabilidade.md) · [19 — TÉO](./19-rastreabilidade-teo.md) |
| Regras de negócio, arquitetura e UX | [04 — Regras](./04-regras-de-negocio-consolidadas.md) · [05 — Gaps](./05-diagnostico-gaps-e-oportunidades.md) · [06 — TO-BE](./06-arquitetura-funcional-to-be.md) · [07 — Jornadas](./07-ux-jornadas-e-estados-de-experiencia.md) |
| Central P1–P6 | [08 — P1](./08-p1-cockpit-da-competencia.md) · [09 — P2](./09-p2-checklist-e-documentos.md) · [10 — P3](./10-p3-estoque-cutoff-e-conciliacao.md) · [15.1 — Paridade P3](./15.1-p3-criterios-paridade-monetaria.md) · [11 — P4](./11-p4-classificacoes-e-pendencias.md) · [12 — P5](./12-p5-pacote-finalizacao-e-envio.md) · [13 — P6](./13-p6-administracao-e-configuracao.md) |
| **Aprovação e revisão P5 (única authority temática de decisões)** | **[37 — Submissão/revisão no Portal, C2, P5-A..J, DEC-01..04 e D-FINAL-02](./37-p5-submissao-e-revisao-no-portal.md)** |
| Segurança, catálogos, bounded contexts | [14 — Segurança](./14-seguranca-rbac-auditoria-e-ia.md) · [16 — Catálogos/notificações](./16-configuracoes-catalogos-e-notificacoes.md) · [21 — Owners/boundaries](./21-boundaries-produtos-e-owners.md) |
| Páginas comuns (padrão visual) | [24 — Navegação](./24-inicio-e-navegacao-principal.md) · [31 — Página do usuário](./31-pagina-do-usuario.md) · [32 — Início](./32-inicio-home.md) · [25 — Visão geral](./25-visao-geral-indicadores-financeiros.md) · [26 — Sala](./26-sala-de-interacao.md) · [27 — Minhas tarefas](./27-minhas-tarefas.md) · [28 — Administração](./28-administracao.md) · [29 — Ajuda](./29-ajuda.md) · [30 — Reuso UI](./30-plugin-ui-reuse-map.md) |
| **Requisitos, aceites e teste por ID** | **[23 — Ledger RQ/AC/Testes](./23-ledger-rq-ac-testes.md)** · [15 — Critérios gerais](./15-requisitos-criterios-de-aceite-e-testes.md) |
| Pendências técnicas / handoff atual | [17 — Inventários E/T](./17-backlog-de-confirmacoes-e-inventarios.md) · [18 — Readiness](./18-readiness-e-handoff-de-implementacao.md) · [22 — Handoff P1–P6](./22-handoff-implementacao-p1-p6.md) |
| **Roadmap e execução** | **[39 — Roadmap V1](./39-roadmap-mestre-implementacao-v1.md)** · [40 — Slices/dependências](./40-matriz-dependencias-e-slices-v1.md) · [41 — Testes/gates](./41-estrategia-validacao-e-gates-implementacao-v1.md) · [42 — Playbook Cursor](./42-playbook-brief-cursor-execution-report-v1.md) · [43 — Rollout](./43-rollout-operacao-e-handoff-v1.md) |
| Decisões de implementação G0 | [45 — Exceção FastAPI e gates](./45-g0-excecao-fastapi-e-fechamento-gates.md) |

**Histórico de análise, não normas atuais nem PASS inferido:** [20 — cobertura histórica](./20-transforma-plus-coverage.md), [33 — fechamento documental](./33-plano-mestre-fechamento-documental.md), [34 — review A14](./34-revisao-transversal-gate-v2.md), [35 — review A15](./35-contratos-regras-scripts-test-matrix-gate-v2.md), [36 — delivery externo superseded](./36-e04-t04-package-delivery-decision-packet.md), [38 — rebaseline após merge](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md), [44 — evidências A16](./44-a16-revalidacao-final-transversal-2026-10-16.md). Preservados para proveniência; se conflitarem com 37/23/39 e HEAD, prevalecem sources mais altas.

## 4. Sequência de coordenação para o próximo chat

1. **IMP-00 — READ/INVENTORY/VERIFY (sem runtime):** HEAD + `git status` no checkout, Project Instructions, `.cursor`, contratos/Core e owners, diff e CI; confirmar gates A12/A14/A15/A16 aplicáveis **sem reabrir escolhas já aprovadas**. Produzir brief preciso do primeiro slice e decisão `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.
2. **Gate explícito transversal / PO:** registrar `DOCUMENTATION_CLOSURE_COMPLETE=PASS`, quatro freezes documentais com evidência e **autorização posterior** `IMPLEMENTATION_AUTHORIZED=YES`. Se faltar binding material, classificá-lo, bloquear somente o slice dependente quando governança permitir, sem bypass de AuthZ.
3. **IMP-01 / A01 — Página do usuário** primeiro: somente após autorização; inventariar `@delpi/plugin-ui`, Core profile/foto S2S e padrões de MFE/BFF antes de scaffold; UI PT-BR, mobile/desktop, claro/escuro, teclado/foco, Help no mesmo gate e security fail-closed. **Página do usuário é deep route**. Depois páginas comuns e P1–P6 conforme 39/40.

Navegação comum: **Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda** (ordem do menu, não necessariamente ordem de PRs). Nenhuma route/page future placeholder sem capability real. A Ajuda acompanha cada slice, não só a página Ajuda final.

**Conclusão:** documentação consolidada para coordenação, **não** implementação autorizada. Revalidar HEAD no novo chat e não usar SHA histórico como status atual.
