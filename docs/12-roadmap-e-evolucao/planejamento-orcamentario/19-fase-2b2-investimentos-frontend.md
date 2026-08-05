# 19 — Fase 2B.2 — Investimentos CAPEX (frontend)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-05  
**Escopo:** listagem, criação/edição de rascunhos, formulário CAPEX, autosave, arquivamento, filtros/paginação, conflito de versão, testes Vitest.  
**Fora:** anexos, submissão, aprovação, reprovação, consolidação, exportações; alterações de migration/backend.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: CONCLUÍDO COM RESSALVAS
```

Ressalva: smoke **autenticado** (criação/edição/autosave/arquivamento na UI com sessão portal) permanece BLOCKED sem token — o shell HTTP e o `remoteEntry.js` foram validados; isso **não** substitui o fluxo funcional autenticado.

---

## 1. Rotas e telas

| Rota | Tela |
|------|------|
| `/apps/planejamento-orcamentario/capex` | Hub CAPEX: centros do usuário; com `?cost_center_id=` lista investimentos |
| `/apps/planejamento-orcamentario/capex/investimentos/novo` | Criação de rascunho (`?cost_center_id=` pré-seleciona CC) |
| `/apps/planejamento-orcamentario/capex/investimentos/:id` | Edição / visualização (arquivado = somente leitura) |

A página inicial do CAPEX continua exibindo somente os centros vinculados via `GET /capex/my-responsibilities`. Ao selecionar um centro, carrega a listagem daquele CC.

---

## 2. Campos do formulário

### Identificação

- exercício (somente leitura)
- unidade / área (derivados do CC selecionado)
- centro de custo (somente responsabilidades do usuário)
- categoria de investimento (`GET /capex/categories`, só ativas)

### Dados do investimento

- descrição, justificativa
- fornecedor provável + código (opcional)
- valor previsto (string decimal, sem float) + moeda (`BRL`)
- Data necessária de recebimento (`required_date`) + ajuda curta
- prioridade `1`–`4`, origem `national`/`imported`, classificação `1`–`6`, turno `1`–`3`
- observações

`accounting_account_code` **não** é enviado (permanece nulo no backend até fonte confiável).

Labels PT em `src/utils/capexInvestments.ts`, alinhados à planilha / constantes do backend.

---

## 3. Integração com a API

| Operação | Endpoint |
|----------|----------|
| Responsabilidades | `GET /capex/my-responsibilities` |
| Categorias ativas | `GET /capex/categories` (filtro ativo no client da listagem ativa) |
| Listar | `GET /capex/investments` (filtros + `page` / `page_size` no servidor) |
| Criar | `POST /capex/investments` |
| Obter / atualizar | `GET` / `PUT /capex/investments/{id}` (PUT com `version`) |
| Arquivar | `POST /capex/investments/{id}/archive` |

Cliente: `plugins/planejamento-orcamentario/src/api/budgetPlanningApi.ts`.

---

## 4. Autosave

- Debounce **1000 ms** (faixa 800–1500).
- Estados: Alterações pendentes / Salvando / Salvo / Erro ao salvar.
- Primeiro persist cria o rascunho; seguintes fazem PUT com `version`.
- Impede PUTs concorrentes (`savingRef`); limpa debounce no salvar manual.
- `beforeunload` quando há alteração não persistida.
- Rascunho incompleto: exibe `is_complete` + `missing_fields` sem bloquear salvamento.

---

## 5. Conflito de versão

HTTP 409 com `budget_capex_version_conflict`:

- não sobrescreve o servidor;
- mensagem clara + botão **Recarregar versão atual**;
- usuário pode permanecer na tela com dados locais (sem merge automático).

---

## 6. Arquivamento

Confirmação → `archive` → atualiza listagem; formulário arquivado fica somente leitura. Sem restauração (endpoint inexistente nesta fase).

---

## 7. Testes

| Arquivo | Cobertura |
|---------|-----------|
| `CapexMyCostCentersPage.test.tsx` | listagem, filtros, incompleto, arquivar, 401/403, vazio, sem CC, orientação |
| `CapexInvestmentFormPage.test.tsx` | CC autorizado, categorias, create, incompleto, autosave, erro autosave, 409, arquivado RO, orientação, sem CC |
| `capexInvestments.test.ts` | money, labels, conflito, rotas |

Vitest: **61** testes no pacote (incluindo regressão das fases anteriores).

---

## 8. Build e smoke

```bash
docker run --rm -v "$PWD/plugins:/plugins" -w /plugins/planejamento-orcamentario node:20-alpine \
  sh -c 'npm run lint && npm run typecheck && npm test && npm run build'
```

| Check | Resultado |
|-------|-----------|
| lint / typecheck / Vitest (61) / `vite build` | OK |
| `./infra/scripts/up-dev-sequential.sh --fase mfe --build planejamento-orcamentario` | OK |
| `HEAD …/assets/remoteEntry.js` | **200** |
| Shell `/capex` e `/capex/investimentos/novo` | **200** (HTML do host) |
| Smoke autenticado create/edit/autosave/archive | **BLOCKED** (sem sessão) |

---

## 9. Arquivos principais

- `src/pages/CapexMyCostCentersPage.tsx`
- `src/pages/CapexInvestmentFormPage.tsx`
- `src/utils/capexInvestments.ts`
- `src/utils/routing.ts` (rotas `capex-investment-*`)
- `src/api/budgetPlanningApi.ts` / `src/types/budgetPlanning.ts`
- `src/App.tsx`, `src/components/PageShell.tsx`, `src/index.css`
- testes acima + esta doc

---

## 10. Pendências

- Anexos, submissão, aprovação/reprovação, consolidação, exportações (fases futuras).
- Conta contábil com fonte ERP.
- Restauração de arquivado (se backend expuser).
- Smoke autenticado no portal.

---

## 11. Relatório resumido

Entrega frontend 2B.2 alinhada aos contratos reais da Fase 2B.1, sem alterar backend. Validação de código concluída; operação Docker/smoke autenticado com ressalvas de ambiente.
