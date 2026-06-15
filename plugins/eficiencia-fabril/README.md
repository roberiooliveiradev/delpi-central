# Eficiência Fabril — plugin Minha DELPI

Microfrontend (Module Federation) para dashboard de eficiência operacional e resultado MOD dos apontamentos de produção (view TOTVS `dbo.vw_Apontamentos_Eficiencia`).

Documentação completa: [docs/12-roadmap-e-evolucao/eficiencia-fabril/](../../docs/12-roadmap-e-evolucao/eficiencia-fabril/) — em especial [ESPECIFICACAO-PLUGIN.md](../../docs/12-roadmap-e-evolucao/eficiencia-fabril/ESPECIFICACAO-PLUGIN.md).  
Faixa válida de eficiência (alinhada ao OEE): [regras-faixa-eficiencia-producao.md](../../api-delpi/docs/api/regras-faixa-eficiencia-producao.md).

---

## Funcionalidades (resumo)

- Duas entradas no menu: **SC** (filial 01) e **ES** (filial 02)
- KPIs: eficiência (média simples), apontamentos na tabela, a avaliar (Verificar), resultado MOD, horas ganhas/perdidas
- Gráficos: eficiência por dia, MOD por dia, top operadores, eficiência por CT (cores por faixa), horas por CT
- Tabela paginada com **ordenação por coluna** + exportação Excel (dados filtrados e ordenados em memória)
- Clique na linha → detalhe do apontamento (mesmo contrato do OEE: roteiro, tempos, estrutura em **árvore**, `time_analysis.findings`)
- Filtros **automáticos** (sem botão aplicar): período, OP, operador, CT e **turno (multiseleção)**; debounce em campos de texto
- Refetch da API só quando o período sai do intervalo já carregado ou ao clicar **Atualizar**
- Regras: CTs excluídos (`CT-00`, `CT-70`, `CT-16A`, `CT-99`); eficiência fora da faixa **0–199%** fora dos indicadores (status **Verificar** na tabela)

---

## API

```http
GET /apps/api-delpi/production/eficiencia-fabril/appointments
GET /apps/api-delpi/production/eficiencia-fabril/dashboard
```

Parâmetros principais: `date_start`, `date_end`, `branch` (fixo pela rota SC/ES), `op`, `employee`, `work_center`.

Rotas no Portal:

- `/apps/eficiencia-fabril/sc` — Filial SC (TOTVS `01`)
- `/apps/eficiencia-fabril/es` — Filial ES (TOTVS `02`)
- `/apps/eficiencia-fabril/sc/appointment/{appointment_id}` — Detalhe (consome `GET /production/oee/appointments/{id}`)

---

## Desenvolvimento local

```bash
cd plugins/eficiencia-fabril
npm install
npm run build
```

A partir de `infra/`:

```bash
docker compose -f docker-compose.dev.yml build eficiencia-fabril --no-cache
docker compose -f docker-compose.dev.yml up -d eficiencia-fabril gateway api-delpi
```

Após mudanças só no **backend**:

```bash
docker compose -f docker-compose.dev.yml restart api-delpi
```

---

## Registro no Portal

```bash
export TOKEN="<jwt_superadmin>"
./scripts/register-manifest.sh
```

---

## Smoke

```bash
curl -sI http://localhost/apps/eficiencia-fabril/assets/remoteEntry.js

# Com JWT (opcional):
TOKEN="<jwt>" ../../scripts/homologacao/check-eficiencia-fabril.sh
```

---

## Estrutura do código

```text
src/
  api/              # HTTP + fetch bulk appointments
  components/       # FilterBar, ShiftMultiSelect, KPIs, gráficos, tabela, árvore de estrutura
  hooks/            # filtros (auto-aplicação + debounce) + dashboard (cache + agregação local)
  pages/            # Dashboard + detalhe do apontamento
  constants/        # regras (faixa 0–199%, turnos, cores de gráfico)
  utils/            # formatação, ordenação da tabela e export Excel
```
