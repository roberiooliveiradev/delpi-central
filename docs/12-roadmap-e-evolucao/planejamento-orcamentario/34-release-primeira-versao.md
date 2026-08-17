# 34 — Release · Primeira versão (Fase 4.0)

**Branch de trabalho:** `feat/planejamento-orcamentario`  
**Data da validação:** 2026-08-15  
**Escopo desta fase:** fechamento técnico da V1 — validação integral, revisão de manifesto/permissões, documentação de homologação. **Sem novas funcionalidades.**  
**Commit nesta fase:** nenhum (conforme brief).

---

## Status

```text
STATUS: PRONTA PARA HOMOLOGAÇÃO
```

```text
SMOKE AUTENTICADO: PENDENTE
```

---

## 1. Objetivo da primeira versão

Entregar o ciclo orçamentário operacional mínimo: exercício e orientações com aceite, estrutura organizacional (filiais 01/02 + centros ERP), responsabilidades, CAPEX completo (incluindo anexos, workflow, consolidação e Excel) e Pessoal com cargo livre + headcount + workflow — com auditoria, concorrência otimista e RBAC.

## 2. Escopo entregue

| Área | Entregue na V1 |
|------|----------------|
| Exercícios | Sim |
| Orientações e aceite | Sim |
| Estrutura organizacional | Sim |
| Filiais 01 e 02 | Sim |
| Centros de custo (ERP) | Sim |
| Responsabilidades orçamentárias | Sim |
| CAPEX (CRUD, anexos, workflow, consolidação, Excel) | Sim |
| Pessoal (cargo livre, headcount, workflow) | Sim |
| Auditoria / histórico de transições | Sim |
| Concorrência otimista (version) | Sim |
| RBAC (manifesto + api-delpi) | Sim |

## 3. CAPEX entregue

- Meus centros / investimentos (criar, editar)
- Anexos de investimento
- Submissão, bloqueio por status, reenvio após ajustes
- Fila e detalhe de aprovação (ajustes / reprovar / aprovar)
- Segregação de funções no backend
- Consolidação gerencial e exportação Excel

## 4. Pessoal entregue

- Plano por filial + centro de custo + exercício
- Cargo digitado livremente (`position_name`; catálogo removido na V009)
- Quatro colunas de headcount + observações + autosave
- Workflow: submissão, histórico, fila, detalhe, decisões
- Bloqueio visual alinhado ao backend

## 5. Modelo de filial e centro de custo

- Filiais TOTVS **01** e **02**
- Centros originados do ERP, **branch-aware** (V007): `Filial 01 + CC X ≠ Filial 02 + CC X`
- Escopos/responsabilidades amarram usuário a filial + centro

## 6. Modelo de responsabilidades

- Cadastro administrativo de responsáveis por centro/módulo (`scopes.manage` / admin)
- Isolamento de dados: responsável vê apenas centros atribuídos
- Módulos CAPEX e Pessoal respeitam o escopo na API

## 7. Workflow

Estados canônicos (CAPEX e Pessoal):

```text
draft → submitted → changes_requested | rejected | approved
```

Labels PT no MFE (Pessoal): Rascunho / Enviado para aprovação / Ajustes solicitados / Reprovado / Aprovado.

Transições enviam `version`; conflito → `*_version_conflict` sem retry automático.

## 8. Migrations V001–V010

Validadas em 2026-08-15 (`run_plugins_migrations.py status`):

| Migration | Descrição | Status |
|-----------|-----------|--------|
| V001 | create_budget_planning_core | APLICADA |
| V002 | create_budget_responsibilities | APLICADA |
| V003 | create_capex_categories | APLICADA |
| V004 | create_capex_investments | APLICADA |
| V005 | create_capex_investment_attachments | APLICADA |
| V006 | create_capex_plans_and_workflow | APLICADA |
| V007 | make_cost_centers_branch_aware | APLICADA |
| V008 | create_personnel_budget_base | APLICADA |
| V009 | replace_personnel_position_catalog_with_free_text | APLICADA |
| V010 | create_personnel_plan_workflow | APLICADA |

**Não** alterar migrations já aplicadas; **não** usar `reset` em produção.

## 9. Versão real do manifesto

```text
planejamento-orcamentario.manifest.json → 0.2.5
package.json → 0.2.5
```

Sem bump nesta fase (nenhuma correção estrutural de manifesto necessária).

Rotas de detalhe (`…/aprovacoes/:id`, formulários de investimento) **fora do menu** — só via router interno.

## 10. Permissões definitivas (V1)

Códigos reais do manifesto / `api_delpi_permissions.py`:

| Código | Uso |
|--------|-----|
| `planejamento-orcamentario.access` | Acessar o app / home |
| `planejamento-orcamentario.guidance.view` | Ler orientações |
| `planejamento-orcamentario.guidance.manage` | Editar/publicar orientações |
| `planejamento-orcamentario.scopes.manage` | Centros e escopos/responsáveis |
| `planejamento-orcamentario.admin` | Administração (exercícios + superconjunto) |
| `planejamento-orcamentario.capex.submit` | Editar/submeter CAPEX |
| `planejamento-orcamentario.capex.approve` | Fila e decisões CAPEX |
| `planejamento-orcamentario.capex.consolidation.view` | Consolidação |
| `planejamento-orcamentario.capex.export` | Export Excel CAPEX |
| `planejamento-orcamentario.personnel.view` | Consultar Pessoal |
| `planejamento-orcamentario.personnel.edit` | Editar headcount |
| `planejamento-orcamentario.personnel.submit` | Submeter Pessoal |
| `planejamento-orcamentario.personnel.approve` | Fila e decisões Pessoal |

**Não existe** `personnel.positions.manage` na V1.

### Agrupamento conceitual (perfis de homologação)

**Responsável CAPEX:** `access` + `capex.submit` (+ `guidance.view` se precisar do aceite).

**Aprovador CAPEX:** `access` + `capex.approve`.

**Responsável Pessoal:** `access` + `personnel.view` + `personnel.edit` + `personnel.submit` (+ `guidance.view`).

**Aprovador Pessoal:** `access` + `personnel.approve` (view implícito nas listas de gate da API quando aplicável).

**Administrador do Planejamento:** `admin` (+ opcionalmente `scopes.manage`, `guidance.manage`, `capex.consolidation.view`, `capex.export` se quiser atribuição explícita além do alias admin).

## 11. Testes backend

```text
docker exec delpi-api-delpi pytest tests/unit/planejamento_orcamentario/ -q
→ 163 passed
```

Health interno: `{"status":"online"}`.

## 12. Testes frontend

```text
plugins/planejamento-orcamentario
→ ESLint (npm run lint): 0 errors / 24 warnings (react-hooks/set-state-in-effect) — exit 0
→ typecheck: OK
→ Vitest: 189 passed (31 files)
→ vite build: OK
→ rebuild: up-dev-sequential.sh --fase mfe --build planejamento-orcamentario → Started
```

## 13. Procedimento de importação do manifesto (manual)

1. No Portal / console de plugins, **importar** o arquivo `plugins/planejamento-orcamentario/planejamento-orcamentario.manifest.json` (versão **0.2.5**).
2. Confirmar que a versão registrada é `0.2.5`.
3. No RBAC, localizar as permissões com módulo `planejamento-orcamentario`.
4. Atribuir aos usuários/perfis conforme a matriz da §10.
5. Pedir ao usuário para **renovar a sessão** (logout/login ou refresh de token).
6. Validar `GET /me` — lista de permissões inclui os códigos esperados.
7. Validar `GET /me/apps` — app `planejamento-orcamentario` presente.
8. Confirmar rotas de menu conforme permissões.
9. Abrir o plugin pelo Portal e exercitar o smoke autenticado (§14).

**Não** auto-importar nem atribuir permissões por script nesta fase.

## 14. Checklist de homologação (smoke autenticado)

### Administrador

- [ ] Criar/abrir exercício
- [ ] Orientação (rascunho/publicação) e documentos
- [ ] Aceite do responsável
- [ ] Centros de custo ERP (filial 01 e 02)
- [ ] Responsabilidades / escopos
- [ ] Categorias CAPEX

### Responsável CAPEX

- [ ] Só centros atribuídos
- [ ] Criar / editar investimento
- [ ] Anexar arquivo
- [ ] Submeter → grade bloqueada
- [ ] Após ajustes: corrigir e reenviar

### Aprovador CAPEX

- [ ] Fila e detalhe
- [ ] Solicitar ajustes / reprovar / aprovar
- [ ] Segregação (quem submeteu não decide)

### Responsável Pessoal

- [ ] Só centros atribuídos
- [ ] Cargo livre + headcounts + autosave
- [ ] Submeter → bloqueio
- [ ] Corrigir após ajustes e reenviar

### Aprovador Pessoal

- [ ] Fila, detalhe, histórico
- [ ] Solicitar ajustes / reprovar / aprovar
- [ ] Segregação de funções

### Filiais

- [ ] Cenário filial **01**
- [ ] Cenário filial **02**
- [ ] Preferencialmente mesmo código de CC nas duas filiais para provar isolamento

## 15. Limitações da V1

- Shell HTTP 200 **não** prova autorização de negócio.
- Lint com warnings de `react-hooks/set-state-in-effect` (não bloqueiam o script `lint` do pacote).
- Smoke autenticado depende de manifesto importado + permissões + sessão.
- Gateway em dev pode estar em porta **9080** (não 80).

## 16. Backlog congelado (fora da V1)

- Consolidação de Pessoal (backend/frontend)
- Exportação Excel de Pessoal
- Notificações
- Salários, benefícios, encargos
- Importação de colaboradores
- Catálogo de cargos / integração ERP de cargos
- Dependência do módulo de Receita
- Reabertura de planos aprovados
- Importação em massa
- Novos dashboards

## 17. Pendências operacionais

1. Importar manifesto **0.2.5** e atribuir RBAC.
2. Executar smoke autenticado completo (§14).
3. Em produção: `up` de migrations do plugin (nunca `reset`); rebuild `api-delpi` + MFE `planejamento-orcamentario`.
4. Restaurar WIP stashed de outras frentes se necessário (`git stash list`).

---

## Validação técnica (Fase 4.0) — resumo

| Check | Resultado |
|-------|-----------|
| Migrations V001–V010 | APLICADAS |
| Backend unit | 163 passed |
| Health api-delpi | online |
| Frontend Vitest | 189 passed |
| Lint / typecheck / build | OK (warnings ESLint não-fatais) |
| Container MFE | Up |
| remoteEntry.js | HTTP 200 |
| Shells principais + detalhes | HTTP 200 |
| Manifesto | 0.2.5 coerente; sem `positions.manage` |
| Refs executáveis catálogo cargos | Nenhuma em `src/` / Python runtime |
| Smoke autenticado | PENDENTE |

---

## Como retomar o desenvolvimento

Sequência recomendada pós-homologação:

1. Consolidação backend de Pessoal  
2. Consolidação frontend de Pessoal  
3. Exportação Excel de Pessoal  
4. Notificações  
5. Análise de salários, benefícios e encargos  
6. Avaliação da dependência do módulo de Receita  
7. Melhorias levantadas durante homologação  

### Documentos a reler antes da retomada

- [`35-playbook-usuario-v1.md`](./35-playbook-usuario-v1.md) — **playbook operacional** (fluxos e FAQ)  
- [`09-roadmap-de-implementacao.md`](./09-roadmap-de-implementacao.md)  
- [`26-fase-3a0-especificacao-pessoal.md`](./26-fase-3a0-especificacao-pessoal.md)  
- [`30-fase-3b1-1-cargo-livre.md`](./30-fase-3b1-1-cargo-livre.md)  
- [`32-fase-3c1-workflow-pessoal-backend.md`](./32-fase-3c1-workflow-pessoal-backend.md)  
- [`33-fase-3c2-workflow-pessoal-frontend.md`](./33-fase-3c2-workflow-pessoal-frontend.md)  
- [`24-fase-2d1-consolidacao-capex-backend.md`](./24-fase-2d1-consolidacao-capex-backend.md) / [`25-fase-2d2-consolidacao-capex-frontend.md`](./25-fase-2d2-consolidacao-capex-frontend.md) (padrão de consolidação a espelhar)  
- Este documento (`34-release-primeira-versao.md`) — limitações e backlog congelado  

---

## Referências obsoletas (classificação)

| Ocorrência | Classificação |
|------------|---------------|
| `V008` / `V009` SQL (`personnel_positions`, `position_id`) | Histórico legítimo de migration — **manter** |
| `test_personnel_v009_migration.py` | Teste de regressão da migração — **manter** |
| Docs `29` / `30` mencionando catálogo | Narrativa histórica — **manter** |
| Assert `"position_id" not in line` em use cases | Anti-regressão do contrato atual — **manter** |
| Código runtime MFE / permissões `positions.manage` | **Ausente** (OK) |
