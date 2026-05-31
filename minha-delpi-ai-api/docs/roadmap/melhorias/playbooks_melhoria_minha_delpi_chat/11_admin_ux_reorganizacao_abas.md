# Playbook 11 — Admin UX: reorganização das abas

> **Status (maio/2026):** implementação das fases 1–4 **revertida** no MFE (`ea9eaf0e` — 10 abas planas estáveis). Novo ciclo: **estudo + mockups Markdown por aba** → implementação única no final. Ver [`11_admin_ux_reorganizacao_abas/00_processo_refatoracao.md`](./11_admin_ux_reorganizacao_abas/00_processo_refatoracao.md) e [`mockups/`](./11_admin_ux_reorganizacao_abas/mockups/README.md).

## Objetivo

Reorganizar o painel administrativo do Minha DELPI Chat (`plugins/minha-delpi-chat`) para reduzir fragmentação, agrupar informações por jornada do administrador e alinhar a navegação aos padrões já usados no Portal e no Strategic Indicators.

Hoje existem **10 abas de primeiro nível** em barra horizontal plana. O admin concentra curadoria, configuração, observabilidade, testes e governança — mas a estrutura atual mistura propósitos e esconde blocos importantes.

---

## Problemas que este playbook resolve

- O administrador não sabe por onde começar (não há painel inicial).
- Curadoria do chat está espalhada em três abas relacionadas (Conhecimento, Diretrizes, Skills).
- Configuração e observabilidade convivem na mesma aba (Métricas).
- Permissões administrativas (RBAC) ficam enterradas dentro de Ferramentas.
- Teste de agente (Simulação) está separado da configuração de agentes.
- Qualidade operacional está dividida entre Métricas e Avaliações.
- Segurança e Auditoria tratam eventos sobrepostos sem relação visual clara.
- A configuração de agente existe em três lugares distintos (builder do chat, aba Agentes, aba Ferramentas).
- Não há deep link por aba (`/admin` sempre abre Conhecimento).
- Em telas estreitas, 10 abas geram rolagem horizontal confusa.
- Rótulos inconsistentes (ex.: **Skills** em inglês entre abas em português).

---

## Princípio central

> O admin do chat deve seguir a mesma lógica dos outros módulos DELPI: **painel primeiro**, abas por **domínio de trabalho**, e **sub-abas** para tarefas dentro do domínio — nunca uma aba por endpoint.

Separar três camadas mentais:

| Camada | Pergunta do admin | Exemplos |
|---|---|---|
| **Curadoria** | O que o chat sabe e como se comporta? | documentos, diretrizes, skills |
| **Especialização** | Como cada agente usa esse conhecimento? | escopo RAG, simulação, builder |
| **Operação** | O chat está saudável, seguro e auditável? | métricas, avaliações, tools, auditoria |

---

## Diagnóstico — estado atual

### Mapa das 10 abas existentes

| Aba | Componente | Conteúdo principal | Problema de agrupamento |
|---|---|---|---|
| Conhecimento | `AdminKnowledgeTab` | ingestão, listagem, metadados curadoriais, teste RAG por documento | OK isolada, mas irmã de Diretrizes/Skills |
| Métricas | `AdminMetricsTab` | KPIs, custo LLM, distribuições, série histórica | **Mistura observabilidade + `ChatIntelligenceSettingsPanel` (config)** |
| Diretrizes | `AdminGuidelinesTab` | CRUD, versionamento, teste RAG | Deveria estar com Conhecimento |
| Skills | `AdminSkillsTab` | catálogo global de skills, policy Markdown | Deveria estar com Conhecimento; label em inglês |
| Simulação | `AdminSimulateTab` | sandbox de agente, prompt preview, RAG | Deveria estar com Agentes |
| Avaliações | `AdminEvaluationsTab` | nota 1–5, sugestões LLM, candidatos | Deveria estar com Métricas (qualidade) |
| Agentes | `AdminAgentsTab` | especialização, presets, escopo RAG/tools | OK, mas desconectada de Simulação e do builder |
| Segurança | `AdminSecurityTab` | anti-injection, scan, eventos 24h | Sobrepõe Auditoria |
| Ferramentas | `AdminToolsTab` + `AdminRbacPanel` | LLM, health, actions, logs por agente, **RBAC** | **RBAC não é ferramenta**; logs de agente duplicam builder |
| Auditoria | `AdminAuditTab` | filtros, timeline, export, detalhe | OK, mas separada de Segurança |

### Referências no código

- Definição das abas: `plugins/minha-delpi-chat/src/ui/pages/ChatAdminPage.tsx`
- Tipos: `plugins/minha-delpi-chat/src/ui/components/admin/shell/adminShellTypes.ts`
- Rotas: `plugins/minha-delpi-chat/src/navigation/chatRoutes.ts` (só `admin` e `admin/agentes/:id`)
- Documentação interna: `plugins/minha-delpi-chat/src/ui/components/admin/README.md`

### Fragmentação da configuração de agentes

| Local | O que configura | Público |
|---|---|---|
| `ChatAgentBuilderPage` | identidade, prompt, skills do agente, actions, knowledge do agente | operador / curador de agente |
| `AdminAgentsTab` | especialização admin (domínio RAG, presets, allowedTools) | admin técnico |
| `AdminToolsTab` | catálogo global, health, logs de teste de actions por agente | admin de plataforma |

O administrador precisa saltar entre três telas para entender um único agente.

---

## Comparação com o restante do projeto

### Portal (`portal/src/ui/admin/AdminPage.tsx`)

| Padrão | Portal | Admin Chat (atual) |
|---|---|---|
| Abas de 1º nível | 7, com ícones Lucide | 10, só texto |
| Mobile | dropdown com aba ativa | rolagem horizontal |
| Hub inicial | `StatsTab` com sub-navegação interna | ausente; default = Conhecimento |
| Navegação cruzada | `StatsTab` chama `onNavigateTab` | ausente |
| Agrupamento | entidades de governança (usuários, papéis, apps) | mistura curadoria + ops + config |

### Strategic Indicators (`SettingsPage.tsx`)

| Padrão | Strategic Indicators | Admin Chat (atual) |
|---|---|---|
| Abas de 1º nível | 6 | 10 |
| Primeira aba | **Painel** (overview executivo) | Conhecimento (tarefa específica) |
| Status strip | erros, sucesso, última atualização | só alertas globais no shell |
| PageHeader | título, descrição, ação de refresh | topbar genérica |
| Sub-estrutura | workspaces dentro de cada aba | componentes grandes sem sub-nav consistente |

### Conclusão comparativa

O admin do chat é o painel administrativo **mais denso** da plataforma, mas usa o shell **menos maduro**: sem hub, sem ícones, sem sub-nav padronizada, sem deep link e com default tab inadequado.

---

## Modelo proposto — 6 abas de primeiro nível

Reduzir de **10 → 6** abas, cada uma com **sub-abas internas** quando necessário.

```text
┌─────────────────────────────────────────────────────────────────┐
│  Painel │ Conhecimento │ Agentes │ Qualidade │ Plataforma │ Governança │
└─────────────────────────────────────────────────────────────────┘
         │              │         │           │            │
         │              │         │           │            ├─ Segurança
         │              │         │           │            └─ Auditoria
         │              │         │           ├─ Ferramentas
         │              │         │           └─ Inteligência
         │              │         ├─ Métricas
         │              │         └─ Avaliações
         │              ├─ Especialização
         │              └─ Simulação
         ├─ Documentos
         ├─ Diretrizes
         └─ Comportamentos (ex-Skills)
```

### 1. Painel

**Propósito:** ponto de entrada; responder “como está o chat?” em 30 segundos.

**Conteúdo (novo `AdminOverviewTab`):**

- KPIs resumidos (sessões, mensagens 24h, taxa de erro, custo estimado)
- Saúde de tools/LLM (resumo de `AdminToolsTab` / health)
- Alertas de segurança 24h (resumo de `AdminSecurityTab`)
- Avaliações pendentes / score médio recente
- Base de conhecimento (documentos ativos, falhas RAG)
- **`AdminRbacPanel`** (movido de Ferramentas)
- Cards de navegação rápida para as outras abas

**Referência de implementação:** `StatsTab` do Portal + overview do `SettingsPage` do Strategic Indicators.

### 2. Conhecimento

**Propósito:** curar tudo que alimenta o comportamento base do chat.

| Sub-aba | Componente existente | Notas |
|---|---|---|
| Documentos | `AdminKnowledgeTab` | manter ingestão + listagem |
| Diretrizes | `AdminGuidelinesTab` | manter versionamento e teste |
| Comportamentos | `AdminSkillsTab` | renomear label **Skills → Comportamentos** ou **Skills do chat** |

**Regra:** testes RAG por documento e por diretriz permanecem nas sub-abas respectivas; não criar aba “Teste RAG” separada.

### 3. Agentes

**Propósito:** configurar e validar especialização por agente.

| Sub-aba | Componente existente | Notas |
|---|---|---|
| Especialização | `AdminAgentsTab` | presets, escopo RAG, allowedTools |
| Simulação | `AdminSimulateTab` | sandbox; manter seleção de agente/sessão |

**Complementos UX (sem mover código do builder):**

- Banner/link persistente: “Identidade, prompt e actions → Configurar agente no workspace”
- Deep link existente `/admin/agentes/:id` continua abrindo sub-aba Especialização
- Quando agente selecionado na Simulação, oferecer link para Especialização do mesmo agente

**Não absorver** `ChatAgentBuilderPage` nesta refatoração — apenas conectar visualmente.

### 4. Qualidade

**Propósito:** medir e melhorar respostas (observabilidade + revisão humana).

| Sub-aba | Componente existente | Notas |
|---|---|---|
| Métricas | `AdminMetricsTab` **sem** `ChatIntelligenceSettingsPanel` | KPIs, custo, distribuições, série |
| Avaliações | `AdminEvaluationsTab` | revisão de candidatos, sugestões |

**Relacionamento:** alinha com [Playbook 05 — Feedback e melhoria contínua](05_feedback_e_melhoria_continua.md). Futuro: card no Painel ligando feedback do chat (thumbs) a esta aba.

### 5. Plataforma

**Propósito:** infraestrutura técnica do chat (tools, LLM, toggles de inteligência).

| Sub-aba | Componente existente | Notas |
|---|---|---|
| Ferramentas | `AdminToolsTab` **sem** `AdminRbacPanel` | health, actions, providers, logs |
| Inteligência | `ChatIntelligenceSettingsPanel` | **movido de Métricas** |

**Justificativa:** `ChatIntelligenceSettingsPanel` altera comportamento do pipeline (`ChatIntelligencePipelineService`), não é métrica. Pertence à camada de plataforma junto com tools e LLM.

### 6. Governança

**Propósito:** segurança operacional e trilha de auditoria.

| Sub-aba | Componente existente | Notas |
|---|---|---|
| Segurança | `AdminSecurityTab` | config, scan, eventos recentes |
| Auditoria | `AdminAuditTab` | filtros, timeline, export |

**UX de ligação:**

- Em Segurança, eventos suspeitos linkam para Auditoria com filtro pré-aplicado (`context=security` ou `action` equivalente)
- Em Auditoria, badge “evento de segurança” quando action/context indicar bloqueio ou flag

Alinha com [Playbook 08 — Segurança, permissões e confiança](08_seguranca_permissoes_confianca.md).

---

## Mapeamento de migração

| Aba atual | Destino | Sub-aba |
|---|---|---|
| Conhecimento | Conhecimento | Documentos |
| Diretrizes | Conhecimento | Diretrizes |
| Skills | Conhecimento | Comportamentos |
| Agentes | Agentes | Especialização |
| Simulação | Agentes | Simulação |
| Métricas (KPIs) | Qualidade | Métricas |
| Avaliações | Qualidade | Avaliações |
| Ferramentas | Plataforma | Ferramentas |
| Métricas (`ChatIntelligenceSettingsPanel`) | Plataforma | Inteligência |
| Segurança | Governança | Segurança |
| Auditoria | Governança | Auditoria |
| RBAC (`AdminRbacPanel`) | Painel | — |
| *(novo)* | Painel | overview |

### Chaves de rota propostas

Substituir `AdminTab` plano por estrutura de dois níveis:

```typescript
type AdminSection =
  | "overview"
  | "knowledge"
  | "agents"
  | "quality"
  | "platform"
  | "governance";

type AdminSubTab =
  | "documents"
  | "guidelines"
  | "behaviors"
  | "specialization"
  | "simulation"
  | "metrics"
  | "evaluations"
  | "tools"
  | "intelligence"
  | "security"
  | "audit";
```

### URLs sugeridas

| URL | Seção | Sub-aba |
|---|---|---|
| `/apps/minha-delpi-chat/admin` | overview | — |
| `/apps/minha-delpi-chat/admin/conhecimento/documentos` | knowledge | documents |
| `/apps/minha-delpi-chat/admin/conhecimento/diretrizes` | knowledge | guidelines |
| `/apps/minha-delpi-chat/admin/conhecimento/comportamentos` | knowledge | behaviors |
| `/apps/minha-delpi-chat/admin/agentes/especializacao` | agents | specialization |
| `/apps/minha-delpi-chat/admin/agentes/simulacao` | agents | simulation |
| `/apps/minha-delpi-chat/admin/agentes/especializacao/:agentId` | agents | specialization |
| `/apps/minha-delpi-chat/admin/qualidade/metricas` | quality | metrics |
| `/apps/minha-delpi-chat/admin/qualidade/avaliacoes` | quality | evaluations |
| `/apps/minha-delpi-chat/admin/plataforma/ferramentas` | platform | tools |
| `/apps/minha-delpi-chat/admin/plataforma/inteligencia` | platform | intelligence |
| `/apps/minha-delpi-chat/admin/governanca/seguranca` | governance | security |
| `/apps/minha-delpi-chat/admin/governanca/auditoria` | governance | audit |

Manter redirect temporário das rotas antigas (`/admin` abrindo conhecimento) por uma release.

---

## Shell UX — alinhar ao restante do projeto

### Topbar

Evoluir `AdminShellTopbar` para:

1. **6 abas** com ícones Lucide (como Portal)
2. **Sub-nav** abaixo da aba ativa (padrão `StatsTab` / `si-settings-tabbar`)
3. **Dropdown mobile** quando `max-width: 767px` (copiar padrão `admin-mobile-select` do Portal)
4. Descrição contextual por seção (como `PageHeader` do Strategic Indicators)
5. Default: **Painel**, não Conhecimento

### Ícones sugeridos

| Seção | Ícone |
|---|---|
| Painel | `LayoutDashboard` |
| Conhecimento | `BookOpen` |
| Agentes | `Bot` |
| Qualidade | `BarChart3` |
| Plataforma | `Wrench` |
| Governança | `Shield` |

### Status strip

Adicionar faixa entre topbar e conteúdo (como `SettingsStatusStrip`):

- erro global do `useChatAdmin`
- mensagem de sucesso
- última atualização / botão Atualizar

---

## Fases de implementação

### Fase 1 — Arquitetura de navegação (baixo risco)

**Escopo:** shell, tipos, rotas, redirects.

- Criar `AdminSectionNav` + `AdminSubTabNav` em `admin/shell/`
- Atualizar `adminShellTypes.ts` com section/subTab
- Estender `chatRoutes.ts` e `parseChatRoute` / `buildChatHref`
- Wrapper `AdminSectionPanel` que monta sub-abas sem alterar componentes internos
- Redirect `/admin` → Painel; mapa de compatibilidade para URLs antigas

**Arquivos principais:**

- `ChatAdminPage.tsx`
- `admin/shell/AdminShellTopbar.tsx`
- `navigation/chatRoutes.ts`
- `navigation/chatRoutes.test.ts`

### Fase 2 — Reagrupar conteúdo existente (médio risco)

**Escopo:** mover blocos entre abas sem reescrever lógica.

- Extrair `ChatIntelligenceSettingsPanel` de `AdminMetricsTab` → sub-aba Plataforma/Inteligência
- Mover `AdminRbacPanel` de Ferramentas → Painel
- Renomear labels (Skills → Comportamentos)
- Agrupar tabs condicionais em wrappers finos (`AdminKnowledgeSection`, etc.)

### Fase 3 — Painel overview (médio risco)

**Escopo:** nova aba Painel.

- Criar `AdminOverviewTab` consumindo endpoints já existentes:
  - `GET /admin/metrics/summary`
  - `GET /admin/tools/health`
  - `GET /admin/security/summary`
  - `GET /admin/responses/evaluations/summary`
  - `GET /admin/rbac/summary`
- Cards clicáveis com navegação para sub-abas (`onNavigateSection`)
- Não duplicar queries pesadas — usar resumos e lazy load ao clicar

### Fase 4 — Polish e consistência (baixo risco)

- Ícones, mobile dropdown, animação de sub-aba
- Cross-links Segurança ↔ Auditoria
- Cross-links Agentes ↔ Builder
- Atualizar `admin/README.md` e `docs/roadmap/admin-minha-delpi-chat.md`
- Testes de rota e smoke manual das 6 seções

---

## RBAC e visibilidade

Respeitar `AdminRbacSummary` ao montar abas:

| Capacidade | Efeito na navegação |
|---|---|
| Sem permissões admin | esconder entrada Admin no chat |
| `canManageTools` | Plataforma/Ferramentas editável |
| `canCreateGuidelines` etc. | Conhecimento/Diretrizes com ações |
| `canExportAudit` | Governança/Auditoria export habilitado |
| Viewer/auditor | Painel + Qualidade + Governança (leitura) |

**Regra:** RBAC no Painel é informativo; bloqueios de ação permanecem nos componentes filhos.

---

## Critérios de aceite

1. Máximo **6 abas** visíveis no topbar desktop.
2. Abas antigas acessíveis via redirect por **1 release** (log de depreciação no console dev).
3. `/admin` abre **Painel**, não Conhecimento.
4. `ChatIntelligenceSettingsPanel` **não** aparece em Qualidade/Métricas.
5. `AdminRbacPanel` aparece no **Painel**, não em Plataforma.
6. Mobile: navegação utilizável sem rolagem horizontal de 10 itens.
7. Deep link `/admin/agentes/especializacao/:id` preservado (redirect da rota antiga).
8. Nenhum endpoint backend novo obrigatório na Fase 1–2.
9. Build do plugin passa (`npm run build` em `plugins/minha-delpi-chat`).
10. Testes de rota atualizados em `chatRoutes.test.ts`.

---

## O que não fazer nesta refatoração

- Unificar `ChatAgentBuilderPage` dentro do admin (escopo futuro).
- Renomear endpoints `/admin/*`.
- Mover notificações de plataforma para este plugin (permanecem no Portal).
- Reescrever componentes de aba — apenas **reorganizar** e extrair shell.
- Criar aba por feature de roadmap futuro (feedback do usuário final, health por tool individual).

---

## Relacionamento com outros playbooks

| Playbook | Conexão |
|---|---|
| [03 — Agentes especialistas](03_agentes_especialistas.md) | aba Agentes concentra especialização + simulação |
| [04 — RAG e conhecimento interno](04_rag_e_conhecimento_interno.md) | aba Conhecimento unifica curadoria documental |
| [05 — Feedback e melhoria contínua](05_feedback_e_melhoria_continua.md) | aba Qualidade recebe métricas + avaliações admin |
| [08 — Segurança, permissões e confiança](08_seguranca_permissoes_confianca.md) | aba Governança + RBAC no Painel |

---

## Checklist de entrega

- [x] `AdminSection` + `AdminSubTab` tipados
- [x] Rotas nested em `chatRoutes.ts` / `adminNavigation.ts`
- [x] Shell com 6 abas + sub-nav + mobile dropdown
- [x] `AdminOverviewTab` mínimo viável
- [x] Intelligence settings em Plataforma
- [x] RBAC em Painel
- [x] Redirects de compatibilidade + aviso DEV em `legacyTabToNav`
- [x] Status strip (erro/sucesso, última atualização)
- [x] Cross-links Governança e Agentes ↔ Builder
- [x] README admin atualizado (`plugins/minha-delpi-chat/src/ui/components/admin/README.md`)
- [x] `adminNavigation.test.ts` (6 seções + legado)

---

## Status (maio/2026)

**Fases 1–4 concluídas.** Evoluções futuras fora deste playbook: unificar `ChatAgentBuilderPage` no admin, E2E Playwright dedicado, status strip com polling automático.
