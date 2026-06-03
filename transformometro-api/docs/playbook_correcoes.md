# Playbook — Correções do Transformômetro

## 1. Contexto geral

Este playbook documenta as correções realizadas no **Transformômetro** da Minha DELPI, principalmente nos cálculos de economia, ROI, investimentos e recursos compartilhados.

O objetivo foi alinhar:

```text
cálculo em tempo real
dashboard_calculos
frontend
cadastro de recursos
regras de vigência
```

A regra central consolidada é:

```text
Economia líquida =
Economia bruta
- investimento único
- custo recorrente
- custo de recursos compartilhados
```

E o ROI passou a ser:

```text
ROI acumulado =
Economia líquida acumulada / investimento total acumulado
```

---

## 2. Correções já realizadas

## 2.1. Correção do ROI

### Problema encontrado

O ROI estava sendo calculado como se a economia líquida ainda não tivesse descontado investimentos.

Depois que a economia líquida passou a descontar investimentos, o ROI ainda fazia algo equivalente a:

```text
ROI = (economia líquida - investimento total) / investimento total
```

Isso causava **desconto duplo do investimento**.

### Regra correta aplicada

```text
ROI = economia líquida / investimento total
```

### Resultado validado

Na tela:

```text
Economia bruta:      R$ 167.640,54
Investimento total:  R$  68.032,23
Economia líquida:    R$  99.608,28
ROI exibido:         146,4%
```

Validação:

```text
99.608,28 / 68.032,23 = 1,464
ROI = 146,4%
```

### Arquivo alterado

```text
transformometro-api/tm_app/domain/services/dashboard_historical_patch.py
```

### Commit relacionado

```text
4568f83e8de59f941ed952d61f28637767dd63cc
```

---

## 2.2. Ajuste do rótulo no frontend

### Problema

O card mostrava:

```text
ROI médio
Fórmula spec (acumulado)
```

Mas o cálculo passou a representar o **ROI consolidado/acumulado do recorte**, não uma média simples.

### Correção aplicada

Agora o card mostra:

```text
ROI acumulado
Economia líquida / investimento total
```

### Arquivo alterado

```text
plugins/transformometro/src/ui/pages/DashboardPage.tsx
```

### Commit relacionado

```text
a67a31df83d531cbb6db1359def784aa95183c24
```

---

## 2.3. Correção da economia líquida no cache `dashboard_calculos`

### Problema

O cálculo materializado em `transformometro.dashboard_calculos` não estava alinhado com o cálculo em tempo real.

A economia líquida gravada precisava seguir a mesma regra oficial:

```text
economia_liquida_mes =
economia_bruta
- investimento_unico_mes
- custo_recorrente_mes
- custo_recursos_compartilhados_mes
```

### Correção aplicada

O recálculo passou a gravar `economia_liquida_mes` com a regra correta.

### SQL de validação

```sql
SELECT
    competencia,
    ROUND(SUM(economia_liquida_mes), 2) AS liquida_gravada,
    ROUND(SUM(economia_bruta - investimento_unico_mes - custo_recorrente_mes - custo_recursos_compartilhados_mes), 2) AS liquida_calculada,
    ROUND(
        SUM(economia_liquida_mes)
        - SUM(economia_bruta - investimento_unico_mes - custo_recorrente_mes - custo_recursos_compartilhados_mes),
        2
    ) AS diferenca
FROM transformometro.dashboard_calculos
GROUP BY competencia
HAVING ABS(
    SUM(economia_liquida_mes)
    - SUM(economia_bruta - investimento_unico_mes - custo_recorrente_mes - custo_recursos_compartilhados_mes)
) > 0.05
ORDER BY competencia;
```

Resultado esperado:

```text
0 linhas
```

Isso significa que a economia líquida gravada bate com a fórmula oficial.

---

## 2.4. Criação da migration para `base_competencia`

### Problema

Todos os recursos compartilhados eram tratados com a mesma lógica mensal, mas existem recursos com naturezas diferentes:

```text
licença mensal
assinatura
pessoa compartilhada
consultoria
apoio temporário
```

Para recursos como **Power BI Pro** ou **ChatGPT Pro**, faz sentido mês cheio.

Para recursos como **Embaixador Robério** e **Embaixador Michael**, que são pessoas atuando na manutenção/melhoria dos processos, faz sentido custo proporcional aos dias de uso.

### Campo criado

```sql
base_competencia VARCHAR(30) NOT NULL DEFAULT 'mensal_cheio'
```

### Valores permitidos

```text
mensal_cheio
proporcional_dias
```

### Migration criada

```text
transformometro-api/migrations/V008__recurso_base_competencia.sql
```

### Commit relacionado

```text
e720f99776be759e2cd050e0c6ae06404d9e902b
```

### Conteúdo da migration

```sql
BEGIN;

ALTER TABLE transformometro.recursos_compartilhados
    ADD COLUMN IF NOT EXISTS base_competencia VARCHAR(30) NOT NULL DEFAULT 'mensal_cheio';

ALTER TABLE transformometro.recursos_compartilhados
    DROP CONSTRAINT IF EXISTS chk_recursos_compartilhados_base_competencia;

ALTER TABLE transformometro.recursos_compartilhados
    ADD CONSTRAINT chk_recursos_compartilhados_base_competencia
    CHECK (base_competencia IN ('mensal_cheio', 'proporcional_dias'));

COMMENT ON COLUMN transformometro.recursos_compartilhados.base_competencia IS
    'Define como o custo mensal do recurso entra na competência: mensal_cheio ou proporcional_dias.';

COMMIT;
```

---

## 2.5. Implementação de `base_competencia` no backend

### Correções aplicadas

Foram adicionados:

```text
- Catálogo BASE_COMPETENCIA_RECURSO
- Retorno em /options
- Campo em RecursoBody
- Validação no CRUD de recursos
- Persistência em RecursoRepository
- Retorno nos vínculos de recursos
```

### Arquivos alterados

```text
transformometro-api/tm_app/core/catalogs.py
transformometro-api/tm_app/interface/http/schemas/crud_schemas.py
transformometro-api/tm_app/interface/http/routes/crud_routes.py
transformometro-api/tm_app/infrastructure/persistence/repositories/recurso_repository.py
```

### Commits relacionados

```text
59b5534b4b19660771ecf2cd255fc9145b66e2fa
52551074d00f055dc762e91b07b9b8f473d94304
0b6c831d4b796055de5a3252dcd2c61ed77edc4f
812c66261a8dd69f4c0a4e4215d6e5ffc2599651
25e5af08203dad43c68b04680b841e59fc57335b
ed9be01ce302f3148a7cf28730e19b400be2bf49
```

---

## 2.6. Implementação de `base_competencia` no frontend

### Correções aplicadas

Foram adicionados:

```text
- Campo no tipo RecursoCompartilhado
- Campo no tipo VinculoRecurso
- Campo em OptionsData
- Campo no formulário de recurso
- Coluna “Competência” no catálogo de recursos
- Labels amigáveis
```

### Labels

```text
mensal_cheio      → Mensal cheio
proporcional_dias → Proporcional aos dias
```

### Arquivos alterados

```text
plugins/transformometro/src/data/api/transformometroApi.ts
plugins/transformometro/src/utils/catalogLabels.ts
plugins/transformometro/src/ui/recursos/recursoCatalogForm.ts
plugins/transformometro/src/ui/recursos/RecursoCatalogFormFields.tsx
plugins/transformometro/src/ui/pages/RecursosPage.tsx
```

### Commits relacionados

```text
bb942212374aae282c94be9ca57d968b5760ec5e
105862f97ea2e842119ffed611930b2b7cbb304b
8bc5837bc9cf7cc01566e0d34440e79dfd19b945
```

---

## 2.7. Correção de erro de build por exports ausentes

### Problema

Durante o build do frontend, apareceram erros como:

```text
downloadDashboardCsv não exportado
downloadDashboardExcel não exportado
DashboardAlertItem não exportado
ImportApplyResult não exportado
ImportPreviewResult não exportado
fetchProcessoComparativo não exportado
```

### Correção aplicada

O arquivo de API do frontend foi recomposto para restaurar os exports esperados.

### Arquivo alterado

```text
plugins/transformometro/src/data/api/transformometroApi.ts
```

---

## 2.8. Correção de erro no comparativo de processo

### Problemas

Após restaurar exports, surgiram novos erros:

```text
Duplicate identifier 'RevisionCompareItem'
Property 'items' does not exist on type 'RevisionCompareItem[]'
```

A API real retornava:

```text
{
  processo,
  total_revisoes,
  items
}
```

Mas o frontend estava tipando como se retornasse diretamente um array.

### Correção aplicada

Foram criados tipos separados:

```text
ProcessoComparativoItem
ProcessoComparativoResponse
```

E `fetchProcessoComparativo` passou a retornar:

```text
ProcessoComparativoResponse
```

### Arquivos alterados

```text
plugins/transformometro/src/data/api/transformometroApi.ts
plugins/transformometro/src/ui/pages/ProcessoDetailPage.tsx
```

### Commits relacionados

```text
c05a1e9390b0704ef1d879b1295551320aa89cd3
c796c2796b57ff661e05344a64188216305fe18f
```

---

## 2.9. Correção de erro ao salvar recurso com `tipo_custo = recorrente`

### Problema

Ao editar recurso, a API retornou:

```text
tipo_custo inválido: recorrente
```

O backend aceita:

```text
fixo
variavel
assinatura
licenca
```

Mas existiam dados legados com:

```text
tipo_custo = recorrente
```

### Correção no frontend

Foi criada normalização antes de salvar:

```text
recorrente / mensal / anual → assinatura
unico / único               → fixo
```

### Arquivo alterado

```text
plugins/transformometro/src/ui/recursos/recursoCatalogForm.ts
```

### Commit relacionado

```text
cf6e28c4dbae859c648432f3585bce4c682a7dbd
```

### Correção feita no banco

Consulta usada para identificar dados inválidos:

```sql
SELECT
    codigo_recurso,
    nome_recurso,
    tipo_custo,
    recorrencia
FROM transformometro.recursos_compartilhados
WHERE deletado = FALSE
  AND tipo_custo NOT IN ('fixo', 'variavel', 'assinatura', 'licenca');
```

Foram encontrados:

```text
RC-0003 — Power BI Pro               — recorrente / mensal
RC-0004 — Chat GPT Pro - Conta geral — recorrente / mensal
```

Depois foram ajustados para:

```text
tipo_custo = assinatura
recorrencia = mensal
```

---

## 2.10. Classificação final dos recursos compartilhados

O cadastro ficou assim:

```text
RC-0001 | Embaixador Robério         | horas_internas | variavel   | mensal | proporcional_dias
RC-0002 | Embaixador Michael         | horas_internas | variavel   | mensal | proporcional_dias
RC-0003 | Power BI Pro               | software       | assinatura | mensal | mensal_cheio
RC-0004 | Chat GPT Pro - Conta geral | software       | assinatura | mensal | mensal_cheio
```

Essa classificação está coerente:

```text
Embaixadores:
- são pessoas
- atuam na manutenção/melhoria dos processos
- custo mensal variável
- proporcional aos dias de uso

Power BI / ChatGPT:
- são assinaturas/licenças
- custo mensal cheio
```

---

## 2.11. Cálculo de recursos compartilhados respeitando `base_competencia`

### Problema

Antes, o custo dos recursos compartilhados entrava como mês cheio, mesmo quando o vínculo começava no fim do mês.

Exemplo de setembro/2025:

```text
Processos iniciando em 26/09 ou 29/09 recebiam praticamente o custo cheio do mês.
```

### Correção aplicada

O cálculo agora respeita:

```text
mensal_cheio:
  usa o valor mensal inteiro quando vigente na competência

proporcional_dias:
  usa valor_mensal × dias efetivos de uso no mês / total de dias do mês
```

A regra considera:

```text
data_inicio_uso do vínculo
data_fim_uso do vínculo
data_inicio_vigencia do recurso
data_fim_vigencia do recurso
```

### Arquivo alterado

```text
transformometro-api/tm_app/domain/services/dashboard_historical_patch.py
```

### Commit relacionado

```text
f45d40d5aab805bbfe8a7b14c84d7ff8d09dd3f8
```

---

## 2.12. Validação de setembro/2025 após proporcionalidade

### Antes

Cada processo estava recebendo aproximadamente:

```text
R$ 478,36 de recursos compartilhados
```

### Depois

Processos iniciados em 26/09 ficaram com:

```text
R$ 87,83
```

Processos iniciados em 29/09 ficaram com:

```text
R$ 40,97
```

Isso ficou coerente porque:

```text
- Embaixadores passaram a ser proporcionais aos dias.
- Power BI continuou mensal cheio.
```

### Consolidado de setembro depois da correção

```text
Economia bruta:          R$ 2.953,47
Investimento único:      R$ 1.100,67
Recorrente:              R$     0,00
Recursos compartilhados: R$   872,41
Investimento total:      R$ 1.973,08
Economia líquida:        R$   980,35
```

Validação:

```text
2.953,47 - 1.100,67 - 872,41 = 980,39
```

Diferença de centavos por arredondamento.

---

## 2.13. Correção de autenticação/RBAC com timeout no `core-api`

### Problema

O `transformometro-api` chamava:

```text
http://core-api:8000/me
```

para carregar RBAC.

Quando dava timeout, o middleware interpretava como token inválido e retornava:

```text
401 Unauthorized
```

mesmo com token válido.

### Correção aplicada

O middleware passou a:

```text
- validar o JWT normalmente
- tentar carregar RBAC
- usar cache quando existir
- usar claims básicas do token se o core-api estiver indisponível
- retornar 401 apenas quando o token for realmente inválido
```

Também foram adicionadas variáveis:

```text
DELPI_AUTH_CORE_API_URL
CORE_API_URL
DELPI_AUTH_RBAC_TIMEOUT_SECONDS
DELPI_AUTH_RBAC_CACHE_TTL_SECONDS
DELPI_AUTH_RBAC_STALE_TTL_SECONDS
```

### Arquivo alterado

```text
shared/delpi_auth/middleware/fastapi_auth.py
```

### Commit relacionado

```text
cad3f7866d8f1da0e0d433ea52fedc9f815da183
```

---

## 3. Comandos úteis de operação

### 3.1. Atualizar código no servidor

```bash
cd ~/projetos/delpi-central
git pull
```

### 3.2. Rebuild do frontend

```bash
cd ~/projetos/delpi-central/infra
docker compose -f docker-compose.yml --env-file .env up --build -d --force-recreate transformometro
```

### 3.3. Rebuild da API

```bash
cd ~/projetos/delpi-central/infra
docker compose -f docker-compose.yml --env-file .env up --build -d --force-recreate transformometro-api
```

### 3.4. Rebuild dos dois

```bash
cd ~/projetos/delpi-central/infra
docker compose -f docker-compose.yml --env-file .env up --build -d --force-recreate transformometro transformometro-api
```

### 3.5. Rodar migrations

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
```

### 3.6. Recalcular dashboard materializado

```bash
docker exec -i delpi-transformometro-api sh -lc 'python - <<'"'"'PY'"'"'
from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService

result = DashboardRecalcService().recalculate()
print(result)
PY'
```

### 3.7. Ver logs da API

```bash
docker logs delpi-transformometro-api --tail=120
```

---

## 4. SQLs de validação

### 4.1. Validar recursos compartilhados

```sql
SELECT
    codigo_recurso,
    nome_recurso,
    categoria_recurso,
    tipo_custo,
    recorrencia,
    base_competencia
FROM transformometro.recursos_compartilhados
WHERE deletado = FALSE
ORDER BY codigo_recurso;
```

Resultado esperado atual:

```text
RC-0001 | Embaixador Robério         | horas_internas | variavel   | mensal | proporcional_dias
RC-0002 | Embaixador Michael         | horas_internas | variavel   | mensal | proporcional_dias
RC-0003 | Power BI Pro               | software       | assinatura | mensal | mensal_cheio
RC-0004 | Chat GPT Pro - Conta geral | software       | assinatura | mensal | mensal_cheio
```

---

### 4.2. Verificar tipos de custo inválidos

```sql
SELECT
    codigo_recurso,
    nome_recurso,
    tipo_custo,
    recorrencia
FROM transformometro.recursos_compartilhados
WHERE deletado = FALSE
  AND tipo_custo NOT IN ('fixo', 'variavel', 'assinatura', 'licenca');
```

Resultado esperado:

```text
0 linhas
```

---

### 4.3. Validar economia líquida materializada

```sql
SELECT
    competencia,
    ROUND(SUM(economia_liquida_mes), 2) AS liquida_gravada,
    ROUND(SUM(economia_bruta - investimento_unico_mes - custo_recorrente_mes - custo_recursos_compartilhados_mes), 2) AS liquida_calculada,
    ROUND(
        SUM(economia_liquida_mes)
        - SUM(economia_bruta - investimento_unico_mes - custo_recorrente_mes - custo_recursos_compartilhados_mes),
        2
    ) AS diferenca
FROM transformometro.dashboard_calculos
GROUP BY competencia
HAVING ABS(
    SUM(economia_liquida_mes)
    - SUM(economia_bruta - investimento_unico_mes - custo_recorrente_mes - custo_recursos_compartilhados_mes)
) > 0.05
ORDER BY competencia;
```

Resultado esperado:

```text
0 linhas
```

---

### 4.4. Validar setembro/2025

```sql
SELECT
    dc.competencia,
    ROUND(SUM(dc.economia_bruta), 2) AS economia_bruta,
    ROUND(SUM(dc.investimento_unico_mes), 2) AS investimento_unico,
    ROUND(SUM(dc.custo_recorrente_mes), 2) AS custo_recorrente,
    ROUND(SUM(dc.custo_recursos_compartilhados_mes), 2) AS recursos_compartilhados,
    ROUND(
        SUM(
            COALESCE(dc.investimento_unico_mes, 0)
          + COALESCE(dc.custo_recorrente_mes, 0)
          + COALESCE(dc.custo_recursos_compartilhados_mes, 0)
        ),
        2
    ) AS investimento_total,
    ROUND(SUM(dc.economia_liquida_mes), 2) AS economia_liquida
FROM transformometro.dashboard_calculos dc
WHERE dc.competencia = '2025-09'
GROUP BY dc.competencia;
```

---

### 4.5. Validar processos específicos de setembro

```sql
SELECT
    p.codigo_processo,
    p.nome_processo,
    dc.competencia,
    dc.custo_recursos_compartilhados_mes,
    (
        COALESCE(dc.investimento_unico_mes, 0)
      + COALESCE(dc.custo_recorrente_mes, 0)
      + COALESCE(dc.custo_recursos_compartilhados_mes, 0)
    ) AS investimento_total_mes,
    dc.economia_bruta,
    dc.economia_liquida_mes,
    (
        COALESCE(dc.economia_bruta, 0)
      - COALESCE(dc.investimento_unico_mes, 0)
      - COALESCE(dc.custo_recorrente_mes, 0)
      - COALESCE(dc.custo_recursos_compartilhados_mes, 0)
    ) AS economia_liquida_recalculada,
    ROUND(
        COALESCE(dc.economia_liquida_mes, 0)
        - (
            COALESCE(dc.economia_bruta, 0)
          - COALESCE(dc.investimento_unico_mes, 0)
          - COALESCE(dc.custo_recorrente_mes, 0)
          - COALESCE(dc.custo_recursos_compartilhados_mes, 0)
        ),
        2
    ) AS diferenca_liquida
FROM transformometro.dashboard_calculos dc
JOIN transformometro.processos p
  ON p.processo_id = dc.processo_id
WHERE dc.competencia = '2025-09'
  AND p.codigo_processo IN (
      'PROC-0001','PROC-0002','PROC-0003','PROC-0004',
      'PROC-0009','PROC-0010','PROC-0011','PROC-0012',
      'PROC-0013','PROC-0014','PROC-0015'
  )
ORDER BY p.codigo_processo;
```

Resultado esperado:

```text
diferenca_liquida = 0,00 ou diferença mínima de centavos
```

---

## 5. O que ainda falta avaliar, verificar e corrigir

> **Atualização (implementado no código):** itens 5.1–5.10 implementados ou documentados. Regras oficiais em [regras-de-calculo.md](regras-de-calculo.md). Após deploy, rodar recálculo do cache (seção 3.6).

## 5.1. Economia diária e ranking “Top economia diária” ✅

### Situação

O dashboard mostra ranking de economia diária.

Precisamos verificar se esse cálculo já está alinhado com a regra oficial:

```text
economia líquida = bruta - investimento único - recorrente - recursos
```

### Risco

O ranking pode estar usando uma fórmula antiga, como:

```text
economia_diaria = (economia_bruta - custo_recorrente) / 30
```

sem descontar:

```text
investimento único
recursos compartilhados
```

### O que fazer

Verificar no backend:

```text
DashboardCalculatorService
DashboardLiveService
rotas /dashboard/processos
```

Procurar funções relacionadas a:

```text
economia_diaria
top economia diária
processos calculados
```

### Critério de aceite

A economia diária deve seguir uma regra documentada. Duas possibilidades:

```text
Opção A:
economia_diaria = economia_bruta_mensal / dias do mês

Opção B:
economia_diaria = economia_liquida_mensal / dias do mês
```

Sugestão: para ranking de “top economia diária”, usar **economia bruta diária**, porque ranking de capacidade de economia não deveria ser distorcido por investimento. Se o objetivo for retorno financeiro real, usar **economia líquida diária**.

---

## 5.2. Payback ✅

### Situação

Foi identificado indício de que o payback pode usar regra diferente da economia líquida oficial.

### Risco

O payback pode estar considerando:

```text
economia_bruta - custo_recorrente
```

mas ignorando:

```text
recursos compartilhados
investimentos únicos
```

### O que fazer

Localizar as funções de payback no backend e validar a fórmula.

### Decisão necessária

Definir se payback será:

```text
investimento inicial / economia líquida mensal
```

ou:

```text
investimento inicial / economia bruta mensal
```

Sugestão:

```text
Payback = investimento único acumulado / economia líquida operacional mensal
```

Mas deve-se ter cuidado para não descontar o próprio investimento único duas vezes.

---

## 5.3. Remover dependência de `dashboard_historical_patch.py` ✅

### Situação

Várias regras críticas estão hoje aplicadas via patch runtime:

```text
dashboard_historical_patch.py
```

Esse arquivo sobrescreve métodos do:

```text
DashboardCalculatorService
DashboardLiveService
```

### Risco

Isso funciona, mas é frágil. Se algum script ou rota usar o serviço antes do patch ser aplicado, pode voltar a usar a regra antiga.

### Correção ideal

Mover definitivamente as regras para:

```text
transformometro-api/tm_app/domain/services/dashboard_calculator.py
```

E deixar o patch desnecessário.

### Critério de aceite

Depois da refatoração:

```text
- Remover monkey patch
- Rodar recálculo
- Validar economia líquida
- Validar ROI
- Validar setembro/2025
- Validar recursos proporcionais
```

---

## 5.4. Queries legadas de `dashboard_calculos` ✅

### Situação

Algumas queries antigas do cache podem não expor corretamente:

```text
custo_recursos_compartilhados_total
investimento_total
```

### Risco

Mesmo que o dashboard principal esteja em tempo real, alguma rota futura ou exportação pode usar cache com regra antiga.

### O que verificar

Arquivos/repositórios relacionados a:

```text
DashboardCalculoRepository
dashboard_data_repository.py
dashboard_export_service.py
dashboard_alerts_service.py
```

### Critério de aceite

Qualquer resumo baseado em `dashboard_calculos` deve usar:

```sql
investimento_total =
investimento_unico_mes
+ custo_recorrente_mes
+ custo_recursos_compartilhados_mes
```

E:

```sql
economia_liquida_mes =
economia_bruta
- investimento_unico_mes
- custo_recorrente_mes
- custo_recursos_compartilhados_mes
```

---

## 5.5. Exportação CSV/Excel ✅

### Situação

Foram restaurados exports no frontend:

```text
downloadDashboardCsv
downloadDashboardExcel
```

Mas ainda é necessário validar se o conteúdo exportado usa os mesmos números da tela.

### O que validar

Gerar CSV e Excel no dashboard e conferir:

```text
economia bruta
investimento único
recorrente
recursos compartilhados
investimento total
economia líquida
ROI
```

### Critério de aceite

Os totais exportados devem bater com os cards e tabelas do dashboard.

---

## 5.6. Filtro parcial por datas ✅

### Situação

Existe lógica de prorrata quando o filtro começa ou termina no meio do mês.

### Risco

O sistema pode aplicar um fator global aproximado sobre os totais, em vez de recalcular por processo/revisão/recurso.

### Exemplo

Filtro:

```text
01/08/2025 até 03/06/2026
```

ou:

```text
15/08/2025 até 20/09/2025
```

Pode distorcer valores se usar média global.

### O que fazer

Validar filtros com início/fim no meio do mês.

### Critério de aceite

A regra precisa ser documentada:

```text
O dashboard trabalha por competência mensal cheia?
Ou faz proporcionalidade por dias dentro da competência?
```

Sugestão: para simplificar o Transformômetro, usar competência mensal cheia nos cards principais, e só aplicar proporcionalidade em recursos com `base_competencia = proporcional_dias`.

---

## 5.7. Alertas de economia líquida negativa ✅

### Situação

Os alertas usam economia líquida negativa por 3 meses ou mais.

### Risco

Depois das correções de recursos e ROI, os alertas mudaram. É necessário validar se eles usam a economia líquida oficial.

### O que validar

Verificar se os alertas somam:

```text
economia_liquida_mes
```

já com:

```text
investimento único
recorrente
recursos compartilhados
```

### Critério de aceite

O alerta deve aparecer apenas quando o processo tem economia líquida negativa real conforme a regra oficial.

---

## 5.8. Comparativo de revisões ✅

### Situação

O comparativo de revisões já foi ajustado no frontend para o contrato correto da API.

### O que falta validar

Conferir se os totais por revisão usam:

```text
economia_bruta
economia_liquida_mes
horas_economizadas_mes
investimentos
recursos compartilhados
```

com a mesma regra do dashboard.

### Critério de aceite

Abrir um processo com revisão baseline e melhoria e validar:

```text
- baseline sem economia
- melhoria com economia calculada no período correto
- revisão descontinuada considerada apenas enquanto vigente
- economia líquida alinhada com dashboard
```

---

## 5.9. Recursos compartilhados no detalhe do recurso ✅

### Situação

Foi criada página de detalhe de recurso com processos vinculados e possibilidade de edição de vínculos.

### O que falta validar

Verificar se a tela mostra claramente:

```text
base_competencia
custo mensal vigente
critério de rateio
vínculos ativos
data início/fim do uso
peso de rateio
```

### Critério de aceite

Ao editar um vínculo:

```text
- data_inicio_uso altera cálculo proporcional
- data_fim_uso encerra custo no período
- ativo false remove vínculo do cálculo
- peso_rateio funciona quando critério for por_peso
```

---

## 5.10. Documentação oficial da regra ✅

### Situação

Foi solicitado documentar que `dashboard_calculos` deve estar sempre alinhado ao cálculo em tempo real.

### O que falta complementar

Atualizar documentação com as novas regras:

```text
- Economia líquida oficial
- ROI acumulado
- Investimento total
- Recursos compartilhados
- base_competencia
- mensal_cheio
- proporcional_dias
- recálculo do cache
```

### Sugestão de documento

Criar ou atualizar:

```text
docs/transformometro/regras-de-calculo.md
```

ou dentro da documentação existente do plugin.

---

## 6. Estado atual esperado

Depois de aplicar tudo e rebuildar:

### Cards do dashboard

Devem seguir:

```text
Economia líquida = Economia bruta - Investimento total
ROI acumulado = Economia líquida / Investimento total
Investimento total = investimento único + recorrente + recursos compartilhados
```

### Recursos

Devem permitir editar:

```text
tipo_custo
recorrencia
criterio_rateio
base_competencia
status
vigências
```

### Recursos compartilhados

Devem calcular:

```text
mensal_cheio:
  valor mensal cheio no mês

proporcional_dias:
  valor proporcional aos dias efetivos de uso
```

### Cache

Após recálculo, `dashboard_calculos` deve bater com o cálculo em tempo real.

---

## 7. Ordem recomendada para continuação

Recomenda-se seguir esta ordem:

```text
1. Validar build atual do frontend e backend.
2. Validar tela de recursos editando base_competencia.
3. Validar economia diária/top ranking.
4. Validar payback.
5. Validar exportação CSV/Excel.
6. Validar alertas.
7. Validar comparativo de revisões.
8. Revisar queries legadas do cache.
9. Consolidar regras no DashboardCalculatorService e remover patch runtime.
10. Atualizar documentação oficial.
```

Prioridade mais alta:

```text
1. Economia diária/top ranking
2. Payback
3. Remover dependência de patch runtime
```

Porque essas três áreas têm maior chance de ainda usar regra antiga ou divergente.