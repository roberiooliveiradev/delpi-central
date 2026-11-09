# GLPI #1538 — ranking dos operadores com mais NCs

## Escopo implementado (branch `feat/glpi-1538-nc-ranking-operadores`)

- Painel entre **Quantidade devolvida** e **Registros** em `NonconformitiesPage`.
- Top 5 operadores por quantidade de **FNCs** (uma NC = um registro vigente).
- Seleção de qualquer operador presente nos resultados, inclusive fora do top 5.
- Detalhes: total de NCs, quantidade de tipos de defeito e distribuição por defeito.
- Agrupamento por `QI2_OPERAD` + **`QI2_DESCR`** (defeito/descrição resumida), **não** `QI2_TIPO` (classificação interna/cliente/fornecedor).
- Mesmos filtros da aba: filial, período (por `QI2_OCORRE`), tipo, situação, item e descrição, inclusive busca da tabela.
- A agregação é feita na `QI2010` sem `LIMIT/OFFSET`; usa `D_E_L_E_T_ = ''` e `QI2_OBSOL <> 'S'`.

## API

`GET /apps/api-delpi/quality/nonconformities/operators`

Permissão: `KPI_QUALITY_ACCESS` (mesma da consulta de NC). Parâmetros opcionais:
`type, branch, start_date, end_date, date_start, date_end, status, item_code, description, operator_code`.

`data` contém:

- `ranking`: 5 maiores, `operator_code`, `operator_name`, `total_ncs`, `main_defect`.
- `operators`: todos os códigos disponíveis para selecionar, ordenados pelo total.
- `detail`: operador selecionado (por padrão o primeiro), `total_ncs`, `defect_types_count`, `defects` (descrição + contagem).
- `total_operators`: total de códigos distintos associados às NCs.

## Integração Portal RH

O código `QI2_OPERAD` é tratado como **matrícula textual**. Nunca remover zeros à esquerda.
A identificação segue a integração S2S já usada no cockpit:

`GET {PORTAL_RH_API_URL}/api/v1/integrations/collaborators/{registration}/`

Header `X-Delpi-Service-Token: PORTAL_RH_API_SERVICE_TOKEN` (somente backend).

O `api-delpi` lê as mesmas variáveis `PORTAL_RH_API_URL`,
`PORTAL_RH_API_SERVICE_TOKEN` e `PORTAL_RH_API_TIMEOUT` da infraestrutura, sem publicar credenciais ao browser. O nome é consultado apenas para os cinco principais e o selecionado; cache em memória por 15 min. Para operadores sem cadastro ou com RH indisponível, aparece `Operador {código}`; a contagem permanece intacta. Colaboradores inativos continuam visíveis em dados históricos.

## Validação pendente em ambiente integrado

1. Preencher/confirmar as variáveis S2S em `infra/.env`, sem versionar o token.
2. Conferir matrícula real do exemplo (20010) e vínculo no RH.
3. Conferir quantidades por código e por `QI2_DESCR` diretamente na `QI2010` em ambas as filiais.
4. Validar que revisões obsoletas não entram no ranking e que os filtros mudam a contagem.
5. Testar nome indisponível, sem operador, códigos com zeros, responsividade e permissão de acesso.
6. Executar testes unitários de `api-delpi/tests/unit/infrastructure/test_nc_operator_ranking.py`, além dos builds e regressões do plugin.

Nenhuma implantação em produção é realizada pelo PR.
