# Matriz canônica de catálogos — cadastro de fornecedores (SA2)

Evidência do inventário F5-UX-R3. Inventário **read-only** executado em
`DELPI_TST01` (SQL Server `192.168.1.230`), dicionário SX3/SX5 e tabelas
mestras. Nenhuma escrita foi realizada; gates POST/PUT permanecem OFF.

Owner dos catálogos: `api-delpi` (consulta SQL canônica ao Protheus).
`supplies-api` apenas proxeia com autorização efetiva; `plugins/supplies`
exibe descrições e envia **códigos** conforme o contrato SA2 vigente.

## Fontes comprovadas (SX3 → tabela)

| Campo Portal | SX3 (SA2) | Fonte das opções | Chave | Descrição | Filtro | Cardinalidade | Controle | Estado |
|---|---|---|---|---|---|---|---|---|
| `person_type` | `A2_TIPO` | CBOX estático do dicionário | `F/J` | Física/Jurídica | — | 1 | `STATIC_SELECT` (já existia) | PROVEN |
| `state` | `A2_EST` | SX5 tabela `12` | `X5_CHAVE` | `X5_DESCRI` | `X5_FILIAL=''` | 1 | `DYNAMIC_SELECT` (preload, filtro local) | PROVEN |
| `country_code` | `A2_PAIS` | `SYA010` | `YA_CODGI` | `YA_DESCR` | `YA_FILIAL=''` | 1 | `DYNAMIC_SELECT` (preload) | PROVEN |
| `bacen_country_code` | `A2_CODPAIS` | `CCH010` | `CCH_CODIGO` | `CCH_PAIS` | `CCH_FILIAL=''` | 1 | `DYNAMIC_SELECT` (preload) | PROVEN |
| `rohs_indicator` | `A2_YROHS` | CBOX estático do dicionário | conforme dicionário | — | — | 1 | `STATIC_SELECT` (já existia) | PROVEN |
| `payment_condition_code` | `A2_COND` | `SE4010` | `E4_CODIGO` | `E4_DESCRI` | `E4_FILIAL=''`; `E4_MSBLQL='1'` → `disabled` | 1 | `DYNAMIC_SELECT` (preload) | PROVEN |
| `payment_method_code` | `A2_FORMPAG` | SX5 tabela `58` | `X5_CHAVE` | `X5_DESCRI` | `X5_FILIAL=''` | 1 | `DYNAMIC_SELECT` (preload) | PROVEN |
| `financial_nature_code` | `A2_NATUREZ` | `SED010` | `ED_CODIGO` | `ED_DESCRIC` | `ED_FILIAL IN ('','01')` | 1 | `DYNAMIC_SELECT` (preload) | PROVEN |
| `accounting_account` | `A2_CONTA` | `CT1010` | `CT1_CONTA` | `CT1_DESC01` | `CT1_FILIAL=''` | 1 | `SEARCH_COMBOBOX` (remoto, `LIMIT 50`) | PROVEN |
| `city` / `city_code` | `A2_MUN` / `A2_COD_MUN` | `CC2010` | `CC2_CODMUN` (+`CC2_EST`) | `CC2_MUN` | `CC2_FILIAL=''` **e `CC2_EST=<UF>`** | 1 | `SEARCH_COMBOBOX` dependente de `state` | PROVEN |

Regras comuns: `D_E_L_E_T_ = ''` em todas as fontes; códigos preservados
como string (zeros à esquerda); busca por prefixo de código **ou** trecho
de descrição (`CI_AI`); ordenação previsível; `SELECT TOP (limit+1)`
para `has_more`.

## Contagens em DELPI_TST01 (registros ativos)

| Catálogo | Registros | Observação |
|---|---|---|
| `states` (SX5/12) | 28 | inclui `EX` (exterior) |
| `countries` (SYA) | 253 | |
| `bacen-countries` (CCH) | 240 | |
| `payment-conditions` (SE4) | 235 | 1 bloqueada (`E4_MSBLQL='1'`) → `disabled:true` |
| `payment-methods` (SX5/58) | 34 | |
| `financial-natures` (SED) | 172 | filiais `''` e `'01'` |
| `accounting-accounts` (CT1) | 1 321 | catálogo grande → busca remota |
| `municipalities` (CC2) | 5 572 total / 295 em `SC` | nunca consultado sem UF |

## Cardinalidade e multiselect

Todos os campos SA2 acima são escalares (`A2_*` C(n)) — cardinalidade 1
comprovada. **Nenhum multiselect** foi implementado.

## Dependências

- `municipalities` exige `state` (UF) — `catalogDependsOn: "state"`;
  sem UF o campo fica desabilitado e nenhuma consulta é disparada.
- `city_code` é derivado da escolha do município
  (`catalogDerivedFrom: "city"`) — preenchido junto, sem segunda fonte.

## Contrato HTTP

`GET /supplies/catalogs/{kind}?query=&state=&limit=` na `api-delpi`
(`supplier_catalogs_router`), proxeado por `supplies-api` com
autenticação bearer + autorização efetiva (mesma capability dos
endpoints de fornecedores). Envelope:

```json
{ "catalog": "states", "items": [{"code":"SC","label":"SANTA CATARINA","disabled":false}], "has_more": false, "total": 28 }
```

- `kind` ∈ allowlist fechada (`_SOURCES`); `limit` máx. 500, padrão 100.
- `state` obrigatório para `municipalities` (rejeitado sem UF).
- Busca: prefixo em código (`LIKE 'q%'`) ou trecho em descrição
  (`CI_AI LIKE '%q%'`).
- Erros sanitizados; sem exposição de tabela/coluna ao cliente.

## Residual / pendente

- Nenhum campo candidato ficou `PENDING` — todos os gates fecharam.
- Opções CBOX de `A2_TIPO`/`A2_YROHS` já existiam como `STATIC_SELECT`
  no registry (valores do contrato, não de consulta SQL).
- Inventário executado em `DELPI_TST01`; paridade com `DELPI`
  pressupõe dicionário equivalente (mesma base de dados de dicionário
  compartilhada no ambiente).
