# Playbook de Excelência — PAC Qualidade DELPI

> **Arquivo:** `docs/12-roadmap-e-evolucao/quality-action-plans/PLAYBOOK-EXCELENCIA.md`  
> **Versão:** 1.0  
> **Data:** 2026-06-24  
> **Base:** brainstorm *Tratativa de Não Conformidades*, `playbook_pac_qualidade_delpi.md`, planilha RNC 8D real, estado do código jun/2026

---

## 1. North Star — o que é excelência aqui

**Excelência** no PAC Qualidade não é “ter um CRUD de planos”. É garantir que **todo problema de qualidade relevante**:

1. Entre no sistema com contexto completo (cliente, produto, filial, escopo, evidências).
2. Seja investigado com método (Ishikawa, 5 Porquês duplo quando aplicável).
3. Gere ações rastreáveis com responsável, prazo e evidência quando exigida.
4. Reaproveite histórico real da DELPI (não reinventar solução).
5. Seja visível para a liderança com indicadores acionáveis.
6. Feche com verificação de eficácia mensurável.
7. Alimente conhecimento reutilizável (padrões, lições, anti-padrões).
8. Produza saída formal para o cliente quando exigido (relatório 8D / planilha).

### Definição operacional (métricas de sucesso — 12 meses)

| Métrica | Meta | Como medir |
|---|---|---|
| Planos externos registrados no PAC | ≥ 95% das NC críticas de cliente | Amostragem qualidade vs. e-mail/planilha |
| Tempo médio até contenção documentada | ≤ 2 dias úteis | `containment_at` − `detected_at` |
| Tempo médio até causa raiz validada | ≤ 10 dias úteis (crítico) | status `root_cause_defined` |
| Ações com prazo vencido sem justificativa | < 10% dos planos abertos | dashboard |
| Planos com eficácia `effective` após revisão | ≥ 70% | `effectiveness_reviews` |
| Reincidência mesmo `recurrence_key` em 12 meses | Tendência de queda | painel recorrência |
| Casos com ≥ 1 evidência anexada | ≥ 80% externos | `quality_problem_evidences` |
| Uso do agente com consulta a histórico | ≥ 60% das aberturas via GPT | log de tool calls |

---

## 2. Pilares de excelência

```text
                    ┌─────────────────────┐
                    │   LIDERANÇA / KPI   │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌─────────▼─────────┐   ┌───────▼────────┐
│ OPERAÇÃO NC    │   │ INTELIGÊNCIA      │   │ AGENTE + CHAT  │
│ (plugin 8D)    │   │ (histórico, padrões)│   │ (GPT / futuro) │
└───────┬────────┘   └─────────┬─────────┘   └───────┬────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ DADOS + CONTRATOS   │
                    │ (Postgres, APIs)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ ENGENHARIA + OPS    │
                    │ (testes, deploy)    │
                    └─────────────────────┘
```

| Pilar | Responsabilidade | Dono sugerido |
|---|---|---|
| **Operação NC** | Fluxo analista, 8D, evidências, export cliente | Qualidade + TI |
| **Inteligência** | Similaridade, recorrência, padrões, eficácia agregada | TI + Qualidade |
| **Agente** | GPT com regras, paridade API, confirmação humana | TI |
| **Liderança** | Dashboard executivo, filtros, alertas | Qualidade |
| **Dados** | Migrations, contratos, auditoria, LGPD | TI |
| **Engenharia** | Testes, CI, homologação, observabilidade | TI |

---

## 3. Estado atual (baseline jun/2026)

Ver [status-atual.md](./status-atual.md). Síntese:

- **Feito:** modelo PAC, CRUD duplo (api-pac + api-delpi), plugin com dashboard/lista/detalhe, Ishikawa, 5 Porquês duplo, relatório 8D, evidências, export Excel, inteligência no agente.
- **Parcial:** formulário de criação, dashboard executivo, conhecimento visível na UI, agente alinhado ao 8D.
- **Não feito:** homologação formal, notificações, TOTVS, busca semântica, PDF, aprovação formal, integração com chat Minha DELPI.

---

## 4. Roadmap por ondas

Cada onda tem **objetivo**, **entregas**, **critério de aceite** e **dependências**. Estimativa: **S** ≤ 1 sprint, **M** 2–3 sprints, **L** 1 trimestre.

---

### Onda 0 — Fundação estável *(concluída ~90%)*

**Objetivo:** base transacional confiável.

| # | Entrega | Repo | Esforço | Status |
|---|---|---|---|---|
| 0.1 | Migrations V001–V005 | api-delpi | S | Feito |
| 0.2 | API PAC CRUD + inteligência | api-pac-quality | M | Feito |
| 0.3 | api-delpi leitura consolidada | api-delpi | M | Feito |
| 0.4 | Plugin MVP (dashboard, lista, detalhe) | plugin | M | Feito |
| 0.5 | Manifesto + RBAC | plugin + Core API | S | Feito |
| 0.6 | Agente GPT documentado | api-pac-quality/docs | S | Feito |

**Aceite:** criar plano PAC-YYYY-####, preencher Ishikawa/5 Porquês/ações, ver na lista e dashboard.

---

### Onda 1 — Operação NC fechada *(prioridade máxima)*

**Objetivo:** analista consegue tratar NC externa ponta a ponta (caso RNC 8D) sem planilha paralela.

| # | Entrega | Repo | Esforço |
|---|---|---|---|
| 1.1 | Aplicar V006 em todos os ambientes | ops | S |
| 1.2 | Template `rnc_8d_template.xlsx` versionado ou script de deploy | api-delpi | S |
| 1.3 | Espelhar `PUT /rnc-8d` e CRUD evidências na **api-pac-quality** | api-pac-quality | M |
| 1.4 | Atualizar OpenAPI + instruções GPT (5 Porquês duplo, 8D, anexos) | api-pac-quality/docs | S |
| 1.5 | Formulário de criação: `customer_template`, `source_type`, `client_nc_registry` | plugin | M |
| 1.6 | `PATCH` plano (editar identificação após criação) | api-delpi + api-pac | M |
| 1.7 | Evidência vinculada à ação (`action_id` + UI quando `evidence_required`) | migration + APIs + plugin | M |
| 1.8 | Export 8D com imagens na aba Anexos | api-delpi | M |
| 1.9 | Atualizar `quality-action-plans-pac.md` | api-delpi/docs | S |
| 1.10 | Homologar 3 casos reais anonimizados | [HOMOLOGACAO.md](./HOMOLOGACAO.md) | M |

**Critério de aceite Onda 1:**

- [ ] Analista cria plano `rnc_8d`, preenche todas as seções da planilha referência, anexa evidências, exporta Excel aceito pela qualidade.
- [ ] Agente GPT executa o mesmo fluxo via API PAC (sem plugin).
- [ ] Nenhum campo obrigatório do 8D fica só na planilha offline.

**Riscos:** template xlsx fora do git; divergência api-delpi vs api-pac.

---

### Onda 2 — Conhecimento visível *(inteligência para humanos)*

**Objetivo:** histórico e padrões não ficam presos no GPT — analista e liderança veem no plugin.

| # | Entrega | Repo | Esforço |
|---|---|---|---|
| 2.1 | `GET /quality/action-plans/{id}/similar-cases` (read-only, proxy intelligence) | api-delpi | M |
| 2.2 | Painel “Casos similares” no detalhe do plano | plugin | M |
| 2.3 | `GET /quality/action-plans/recurrence` — agrupamento por `recurrence_key` | api-delpi | M |
| 2.4 | Tela / seção Recorrência (§20.4 playbook) | plugin | M |
| 2.5 | `GET /quality/solution-patterns` — listagem curada | api-delpi | M |
| 2.6 | Tela Soluções testadas (§20.5) | plugin | M |
| 2.7 | Fluxo “Promover a padrão” ao fechar plano eficaz | api-pac + plugin | M |
| 2.8 | `symptom_tags`, `failure_mode`, `problem_category` na UI | plugin | S |
| 2.9 | Busca textual em evidências (metadados + nome arquivo) | api-delpi | S |

**Critério de aceite Onda 2:**

- [ ] Ao abrir plano de produto X, analista vê ≥ 3 casos similares sem abrir o GPT.
- [ ] Liderança identifica recorrência de modo de falha em uma tela dedicada.
- [ ] Plano fechado como eficaz pode virar entrada em `quality_solution_patterns` com um clique.

---

### Onda 3 — Liderança e excelência analítica

**Objetivo:** dashboard responde perguntas da diretoria, não só contadores.

| # | Entrega | Repo | Esforço |
|---|---|---|---|
| 3.1 | KPIs: tempo médio fechamento, tempo até eficácia | api-delpi | M |
| 3.2 | Gráficos: por causa raiz, modo de falha, tipo de ação | api-delpi + plugin | M |
| 3.3 | Ranking cliente / produto / responsável (top NC) | api-delpi + plugin | M |
| 3.4 | Card reincidências detectadas (últimos 12 meses) | api-delpi + plugin | M |
| 3.5 | Taxa de eficácia por tipo de ação | api-delpi + plugin | M |
| 3.6 | Filtros avançados: responsável, departamento, atrasado, causa raiz | plugin | M |
| 3.7 | Linha do tempo visual no detalhe (status, ações, evidências, eficácia) | plugin | M |
| 3.8 | Export PDF do plano / 8D para arquivo | api-delpi | L |
| 3.9 | Vista “Minha fila” (ações do usuário logado) | api-delpi + plugin | M |

**Critério de aceite Onda 3:**

- [ ] Gerente responde em < 2 min: “quantos planos críticos externos abertos na filial 02?” e “qual produto mais reincide?”.
- [ ] Dashboard carrega em < 3 s com 500+ planos (índices validados).

---

### Onda 4 — Engajamento e governança

**Objetivo:** nada importante depende de memória ou cobrança manual.

| # | Entrega | Repo | Esforço |
|---|---|---|---|
| 4.1 | Notificações in-app (prazo ação, plano parado > N dias) | Core API + plugin | L |
| 4.2 | E-mail digest semanal para responsáveis (opcional) | serviço notificação | L |
| 4.3 | Workflow aprovação eficácia (analista → coordenador) | migration + APIs | L |
| 4.4 | Reabrir plano `completed`/`cancelled` com motivo auditado | APIs + plugin | S |
| 4.5 | Permissões granulares: `close`, `validate_effectiveness`, `admin` | Core API + APIs | M |
| 4.6 | SLA por severidade (alertas visuais) | plugin | M |
| 4.7 | Auditoria imutável (`quality_audit_log` expandido) | api-delpi | M |

**Critério de aceite Onda 4:**

- [ ] Responsável recebe alerta 48 h antes do vencimento da ação.
- [ ] Plano crítico sem movimento em 5 dias úteis aparece no dashboard da coordenação.

---

### Onda 5 — Agente de classe mundial

**Objetivo:** GPT como copiloto confiável, não chat genérico.

| # | Entrega | Repo | Esforço |
|---|---|---|---|
| 5.1 | Paridade total OpenAPI api-pac ↔ api-delpi (escrita) | api-pac-quality | M |
| 5.2 | Upload de evidência via multipart no agente (tool documentada) | api-pac-quality | M |
| 5.3 | Extração estruturada de PDF/e-mail (prompt + validação humana) | docs + evals | M | ✅ jun/2026 |
| 5.4 | Suite de evals com 20 cenários anonimizados (CI opcional) | api-pac-quality/tests | L | ✅ jun/2026 — runner `run_pac_agent_eval.py` |
| 5.5 | Log de decisão: quais casos similares influenciaram sugestão | api-pac-quality | M | ✅ jun/2026 |
| 5.6 | Integração: agente no **Minha DELPI Chat** (skill PAC) | minha-delpi-ai-api | L | ✅ jun/2026 |
| 5.7 | Modo “só consulta” para liderança no chat | minha-delpi-ai-api | L | ✅ jun/2026 |

**Critério de aceite Onda 5:**

- [ ] 90% dos cenários de eval passam sem inventar causa raiz.
- [ ] Toda gravação via agente registra `created_by` / trilha de confirmação.

---

### Onda 6 — Conhecimento avançado

**Objetivo:** busca que entende linguagem natural e imagens.

| # | Entrega | Repo | Esforço |
|---|---|---|---|
| 6.1 | `pgvector` + embeddings de `search_text` | migration | L | ✅ V009 `search_embedding` |
| 6.2 | Busca semântica em casos e padrões | api-pac-quality + api-delpi | L | ✅ jun/2026 — híbrido trgm + pgvector |
| 6.3 | OCR de evidências (foto NC) → tags automáticas sugeridas | minha-delpi-ai-api ou api-pac | L | ✅ jun/2026 |
| 6.4 | Detecção proativa de recorrência na abertura (score + alerta) | api-pac-quality | M | ✅ jun/2026 |
| 6.5 | Grafo “produto ↔ modo falha ↔ causa ↔ ação eficaz” | api-pac-quality + api-delpi | L | ✅ jun/2026 — `GET .../intelligence/knowledge-graph` |

---

### Onda 7 — Ecossistema DELPI *(visão)*

**Objetivo:** PAC não é ilha — conecta operação real.

| # | Entrega | Esforço | Notas |
|---|---|---|---|
| 7.1 | Link bidirecional NC TOTVS (`QI2010`) | L | Import manual → automático |
| 7.2 | Vínculo plano PAC ↔ Kaizen gerado | M | Fechar ciclo melhoria |
| 7.3 | Vínculo plano ↔ Auditoria 5S (NC origem) | M | Mesmo schema `quality` |
| 7.4 | Indicadores PAC no **strategic-indicators-api** | M | PPM, reincidência cliente |
| 7.5 | NC fornecedor (escopo `supplier`) | L | Novo `nonconformity_scope` |
| 7.6 | Custo da não qualidade (horas × material) | L | Campos opcionais + BI |
| 7.7 | Templates por cliente (`customer_template` extensível) | M | Além de `rnc_8d` |

---

## 5. Sugestões além do brainstorm (recomendadas)

Itens que elevam a aplicação a referência interna:

### 5.1 Qualidade de dados

- **Validação na API:** produto existe no cadastro Protheus? (lookup opcional via api-delpi).
- **Campos obrigatórios por severidade:** crítico exige contenção + evidência em 48 h.
- **Duplicata na abertura:** alertar se já existe plano aberto mesmo `product_code` + sintoma similar.

### 5.2 Experiência do analista

- **Autosave** no editor 8D (como Auditoria 5S).
- **Atalhos de teclado** na lista de ações.
- **Duplicar plano** como modelo para NC parecida.
- **Checklist D0–D8** com % conclusão visível no pipeline.

### 5.3 Confiança e compliance

- **Versionamento do `template_payload`** (histórico de revisões do 8D).
- **Assinatura digital** no export (coordenador qualidade) — futuro.
- **Retenção LGPD:** política para dados de cliente em evidências.
- **Anonimização** para treino/evals do agente.

### 5.4 Engenharia

- Script `check-quality-action-plans.sh` (padrão Auditoria 5S).
- Testes de contrato OpenAPI api-delpi ↔ plugin.
- Gate CI: migration `--check` + smoke export 8D.
- Feature flags: `rnc_8d_export_images`, `intelligence_in_plugin`.

### 5.5 Cultura de melhoria

- **Retrospectiva trimestral** com qualidade: quais padrões mais eficazes?
- **Gamificação leve:** reconhecer analista com maior taxa de eficácia (interno).
- **Playbook de resposta ao cliente** embutido no export (textos padrão PT).

---

## 6. Arquitetura alvo (estável)

```text
Analista / Liderança
        │
        ├─► Plugin quality-action-plans ──► api-delpi (consolidado, RBAC JWT)
        │                                      │
        │                                      ▼
        └─► Agente GPT ──► api-pac-quality ──► Postgres quality.*
                           (API key / JWT)         ▲
                                                    │
                           minha-delpi-ai-api ──────┘  (futuro: skill PAC)
```

**Regra de ouro:** uma fonte de verdade no Postgres; duas APIs com **paridade de escrita**; plugin **nunca** chama api-pac-quality diretamente (segurança e contrato).

---

## 7. Priorização MoSCoW (próximos 90 dias)

| Must | Should | Could | Won't (agora) |
|---|---|---|---|
| Onda 1 completa | Onda 2.1–2.4 | PDF export | TOTVS auto |
| Homologação 3 casos | Dashboard avançado (3.1–3.4) | Chat skill PAC | Embeddings |
| Paridade API PAC 8D/evidências | Timeline visual | OCR evidências | E-mail digest |
| Docs atualizadas | Filtros avançados | Kaizen link | Multi-tenant |

---

## 8. Governança do roadmap

| Ritual | Frequência | Participantes |
|---|---|---|
| Review status-atual.md | A cada entrega | TI + Qualidade |
| Demo onda concluída | Fim da onda | Stakeholders |
| Atualizar métricas §1 | Mensal | Coordenação qualidade |
| Revisar prioridades MoSCoW | Trimestral | Gerência |

**Como marcar progresso:** checkbox nas ondas → atualizar [status-atual.md](./status-atual.md) → mencionar no changelog do plugin.

---

## 9. Referências cruzadas

| Documento | Uso |
|---|---|
| `api-pac-quality/playbook_pac_qualidade_delpi.md` | Especificação funcional detalhada |
| `api-pac-quality/docs/Playbook — Tratativa de Não Conformidades.pdf` | Brainstorm original |
| `api-delpi/docs/api/quality-action-plans-pac.md` | Contrato HTTP (manter sincronizado) |
| `docs/12-roadmap-e-evolucao/auditoria-5s/ROADMAP.md` | Modelo de roadmap + scripts homologação |

---

## 10. Resumo executivo para decisão

1. **Curto prazo (30 dias):** fechar Onda 1 — operação NC sem planilha paralela + agente alinhado.
2. **Médio prazo (90 dias):** Ondas 2 e 3 — conhecimento visível + dashboard que a diretoria usa.
3. **Longo prazo (12 meses):** Ondas 4–7 — governança, ecossistema, busca semântica.

A excelência chega quando a pergunta *“como tratamos essa NC?”* tem resposta única: **no PAC**, com histórico, evidência e melhoria contínua — não em e-mail, pasta de rede ou planilha solta.
