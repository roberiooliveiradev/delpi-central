# Especificação funcional — Plugin Eficiência Fabril (estado atual)

> **Versão do plugin:** `0.1.0` (manifesto)  
> **Última revisão:** 2026-05-28  
> **Escopo:** comportamento implementado em `plugins/eficiencia-fabril` + rotas `api-delpi` de Produção.

---

## 1. Visão geral

Tela única no Portal (**Minha DELPI**) para líderes de produção acompanharem apontamentos da view TOTVS `dbo.vw_Apontamentos_Eficiencia`:

- KPIs de eficiência, apontamentos, resultado MOD e horas ganhas/perdidas;
- cinco gráficos analíticos (layout 3 + 2);
- tabela paginada de apontamentos com exportação Excel;
- filtros com aplicação **local** (sem nova busca na API), exceto mudança de período ou botão **Atualizar**.

**URL:** `/apps/eficiencia-fabril`  
**Permissão:** `eficiencia-fabril.view` (e legado `api-delpi.access` / `dashboard-production.view` na API).

---

## 2. Arquitetura de dados no frontend

```text
Abertura / Atualizar / período novo
  → GET .../eficiencia-fabril/appointments?date_start&date_end&status_ok_only=false
  → lista completa do período em memória

Aplicar filtros (filial, OP, operador, CT)
  → recálculo local de KPIs, gráficos, tabela e paginação
  → sem nova chamada HTTP

Período aplicado fora do intervalo já carregado
  → nova busca em /appointments
```

O endpoint `GET .../dashboard` permanece disponível (agregações no SQL, paginação server-side), mas o **MFE atual** prioriza `/appointments` + agregação no navegador para filtros instantâneos.

---

## 3. API (api-delpi)

Base no gateway: `/apps/api-delpi/production`

| Método | Rota | Uso atual do MFE |
|--------|------|------------------|
| `GET` | `/eficiencia-fabril/appointments` | **Principal** — carga bulk do período |
| `GET` | `/eficiencia-fabril/dashboard` | Legado / smoke / integrações futuras |

### Query params comuns

| Parâmetro | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `date_start` | Sim | Início do período (`YYYY-MM-DD`) |
| `date_end` | Sim | Fim do período |
| `branch` | Não | `01` ou `02` |
| `op` | Não | Busca parcial (`LIKE`) no número da OP |
| `employee` | Não | Busca parcial no **nome** do operador (`NOME_OPERADOR`) |
| `work_center` | Não | Centro de trabalho (match exato no backend; parcial no filtro local) |
| `status_ok_only` | Não | Default `false` em `/appointments` (MFE envia `false` na carga). Default `true` em `/dashboard` |

`/dashboard` adicionalmente: `page`, `page_size` (máx. 500).

---

## 4. Regras de negócio

### 4.1 Centros de trabalho excluídos (sempre)

Não entram em consultas do repository (nem na carga bulk):

- `CT-00`, `CT-70`, `CT-16A`, `CT-99`  
- `CT-99` = não produtivo (regra de aplicação).

Se o usuário filtrar explicitamente por um CT excluído, a API retorna conjunto vazio.

### 4.2 Eficiência nos indicadores (KPIs e gráficos)

| Regra | Detalhe |
|-------|---------|
| Base | Apenas `STATUS_REGISTRO = 'OK'` |
| Agregação | **Média simples** de `EFICIENCIA_PERCENTUAL` (não ponderada por tempo) |
| Teto | Registros com eficiência **> 250%** **não** entram em KPIs/gráficos |
| Tabela | Registros > 250% **permanecem** na tabela com status **Verificar** (linha em vermelho) |

Constante no código: `VERIFY_EFFICIENCY_THRESHOLD_PCT = 250`, `max_efficiency_indicator_pct` no backend.

### 4.3 Filtro de registros na tabela

- Checkbox **“Somente registros OK”** foi **removido da UI**.
- Comportamento fixo: tabela e exportação consideram apenas apontamentos com `STATUS_REGISTRO = 'OK'` (via filtro interno `status_ok_only: true` nos parâmetros derivados).

### 4.4 KPI — card Eficiência

- Valor: média simples (%) dos indicadores.
- Cor **vermelha** se média **< 95%** (`EFFICIENCY_KPI_WARNING_PCT`).

### 4.5 KPI — card Apontamentos

- Valor: quantidade de linhas na **tabela** (filtros aplicados).
- Legenda: quantos precisam **avaliar (Verificar)** — eficiência > 250%, não “com problema”.

### 4.6 KPI — Horas ganhas/perdidas

- Soma de `TEMPO_GANHO_PERDIDO_HORAS` nos registros dos indicadores.
- Exibição: `{valor} Horas` (ex.: `-1.504,19 Horas`).

---

## 5. Filtros (UI)

| Campo | Comportamento |
|-------|----------------|
| Data início / fim | Draft até clicar **Aplicar filtros** |
| Filial | `01`, `02` ou todas |
| Operador | Texto — busca parcial no **nome** |
| OP | Texto — busca parcial (ex.: `24546` encontra OPs que contêm o trecho) |
| Centro de trabalho | Texto — filtro local parcial |
| ~~Centro de custo~~ | Removido |
| ~~Somente OK~~ | Oculto (sempre OK na tabela) |

**Atualizar** (cabeçalho): recarrega dados do período atual da API.

---

## 6. Gráficos

Layout na página:

| Linha | Gráficos |
|-------|----------|
| Superior (3 colunas) | Eficiência por dia · Lucro vs prejuízo MOD · Top operadores |
| Inferior (2 colunas) | Eficiência por CT · Horas por centro de trabalho |

Todos sem linhas de grade de fundo. Modal expandido: **1320px** × gráfico **700px** de altura.

| Gráfico | Detalhes |
|---------|----------|
| Eficiência por dia | Linha; referência 100% tracejada (semi-transparente) |
| Lucro vs prejuízo MOD | Barras empilhadas; tooltip Lucro/Prejuízo corrigido |
| Top operadores | Barras horizontais; card = **primeiro nome**; expandido = nome completo; top 10 |
| Eficiência por CT | Barras verticais; cores: &lt;90% vermelho, 90–99,99% amarelo, ≥100% verde; labels % só no **modal** |
| Horas por CT | Real vs previsto; top 12 por horas reais |

---

## 7. Tabela de apontamentos

Colunas: Data, Início, Fim, Qtd. apontada, Filial, OP, CT, Operador, Eficiência, Resultado MOD, Status.

- Paginação local (50 por página).
- **Exportar Excel:** usa dados já filtrados em memória (sem nova API).
- Linha vermelha + badge **Verificar** quando eficiência > 250%.

---

## 8. Mensagens na tela

- Aviso: eficiência **> 250%** desconsiderada nos indicadores; na tabela como **Verificar**.
- Legenda “eficiência &gt; 100%” removida (só permanece o aviso de 250%).

---

## 9. Deploy e operação

| Item | Valor |
|------|--------|
| Manifesto | `plugins/eficiencia-fabril/eficiencia-fabril.manifest.json` |
| Container | `delpi-eficiencia-fabril` |
| Compose | `infra/docker-compose.dev.yml` (target `static` recomendado) |
| Registro | `plugins/eficiencia-fabril/scripts/register-manifest.sh` |
| Build CI | `scripts/ci/build-eficiencia-fabril.sh` |
| Smoke | `scripts/homologacao/check-eficiencia-fabril.sh` |

Ver também: [plugins/eficiencia-fabril/README.md](../../../plugins/eficiencia-fabril/README.md).

---

## 10. Pendências conhecidas (pós-MVP)

- RBAC operacional (role dedicada além de superadmin).
- Documentação OpenAPI dedicada em `api-delpi/docs/api/`.
- Deploy produção e validação com usuários finais.
- Evoluções: cache, drill-down, incluir registros não-OK na tabela via UI.
