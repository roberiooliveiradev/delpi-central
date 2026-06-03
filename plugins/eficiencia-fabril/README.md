# Eficiência Fabril — plugin Minha DELPI

Microfrontend (Module Federation) para dashboard de eficiência operacional e resultado MOD dos apontamentos de produção (view TOTVS `dbo.vw_Apontamentos_Eficiencia`).

Documentação completa: [docs/12-roadmap-e-evolucao/eficiencia-fabril/](../../docs/12-roadmap-e-evolucao/eficiencia-fabril/) — em especial [ESPECIFICACAO-PLUGIN.md](../../docs/12-roadmap-e-evolucao/eficiencia-fabril/ESPECIFICACAO-PLUGIN.md).

---

## Funcionalidades (resumo)

- Duas entradas no menu: **SC** (filial 01) e **ES** (filial 02)
- KPIs: eficiência (média simples), apontamentos na tabela, a avaliar (Verificar), resultado MOD, horas ganhas/perdidas
- Gráficos: eficiência por dia, MOD por dia, top operadores, eficiência por CT (cores por faixa), horas por CT
- Tabela paginada + exportação Excel (dados em memória)
- Filtros com aplicação local (sem refetch), exceto período novo ou **Atualizar**
- Regras: CTs excluídos (`CT-00`, `CT-70`, `CT-16A`, `CT-99`); eficiência &gt; 250% fora dos indicadores

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
  components/       # FilterBar, KPIs, gráficos, tabela, modal
  hooks/            # filtros + dashboard (cache + agregação local)
  pages/            # DashboardEficienciaFabrilPage
  constants/        # regras (250%, 95%, cores de gráfico)
  utils/            # formatação e export Excel
```
