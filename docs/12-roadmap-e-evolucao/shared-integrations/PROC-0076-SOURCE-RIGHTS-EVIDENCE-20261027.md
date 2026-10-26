# PROC-0076 — Evidência de direitos de uso das fontes de dados de mercado

- **Execução:** PROC-0076.R1.1.S4
- **Data de consulta das fontes:** 2026-10-27
- **Owner técnico:** `external-data-api`
- **Autoridade de licença:** responsável institucional competente (não o código). Este documento registra evidências e classifica o que está provado; a decisão institucional permanece pendente onde indicado.

## 1. Banco Central do Brasil — PTAX (`bcb-ptax`)

| Uso | Veredito | Evidência |
|---|---|---|
| collect (API Olinda OData) | **PASS** | API pública oficial; documentação e portal de dados abertos do BCB |
| store (histórico) | **PASS** | Dados abertos, licença ODbL-1.0 conforme portal de dados abertos |
| derive (médias, conversão) | **PASS** | ODbL permite obras derivadas com atribuição |
| internal_display (Portal Suprimentos) | **PASS** | Exibição interna com atribuição trafegada no contrato (`source`, `attribution`) |

- Termos: https://dadosabertos.bcb.gov.br/ — dataset "Taxas de câmbio" (PTAX), ODbL-1.0, atribuição "Banco Central do Brasil".
- **Ressalva operacional:** egress de produção recebe HTTP 403 do WAF do BCB — impedimento operacional documentado (não jurídico). Nenhum bypass foi implementado; feed `EXTERNAL_DATA_FEED_FX_DAILY_ENABLED` permanece OFF.

## 2. World Bank — Commodity Markets "Pink Sheet" (`world-bank-pink-sheet`)

### 2.1 Base normativa consultada

| Fonte oficial | URL | Trecho relevante |
|---|---|---|
| WB Terms of Use for Datasets (vigente) | https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets | Datasets sob CC BY 4.0 "unless specifically labeled otherwise"; **exceção de terceiros:** "Some datasets and indicators are provided by third parties, and may not be redistributed or reused without the consent of the original data provider, or may be subject to terms and conditions that are different from those described above. Where applicable, these conditions are included in the dataset or indicator metadata." |
| WB Commodity Markets (página do produto) | https://www.worldbank.org/en/research/commodity-markets | Workbook "Monthly prices" (CMO-Historical-Data-Monthly.xlsx) publicado mensalmente; links para Terms of Use for Datasets |
| Workbook — aba "Description" | (arquivo ingerido) | Séries de metais identificadas como "(LME) ... settlement price" — Alumínio, Cobre, Chumbo, Níquel, Estanho, Zinco |
| LME Market data licensing (vigente) | https://www.lme.com/market-data/market-data-licensing | A LME licencia separadamente: **data distribution**, **derived data**, **non-display use**, **usage** (valuation/pricing) — "licenses LME data for a variety of uses above and beyond limited internal business use" |
| LME Data distribution | https://www.lme.com/market-data/market-data-licensing/data-distribution | Exibição/distribuição de dados LME exige licença de distribuição; next-day também licenciado |

### 2.2 Matriz de direitos por uso

| Uso | Veredito | Fundamento |
|---|---|---|
| collect (download do workbook) | **PASS** | WB publica o arquivo abertamente e os ToU autorizam extração/download; uso via download manual/automatizado do arquivo público |
| store (histórico interno) | **PASS** | CC BY 4.0 sobre a publicação WB autoriza cópia/armazenamento com atribuição |
| derive (médias mensais, agregações) | **PASS** | CC BY 4.0 autoriza obras derivadas sobre a publicação WB |
| internal_display (Portal Suprimentos, usuários autenticados) | **INCONCLUSIVE** | Os ToU do WB delegam dados de terceiros aos termos do provedor original; a LME licencia usos de exibição separadamente do "limited internal business use". Se a exibição corporativa interna das séries com lastro LME excede o uso interno gratuito é decisão institucional/jurídica — **não há evidência documental suficiente para PASS** |
| redistribution / public display | **INCONCLUSIVE** (sem direito comprovado) | Requereria consentimento LME ou licença de distribuição; nenhum documento comprova esse direito |
| Séries **não-LME** do workbook | não aplicável | O catálogo PROC-0076 só ingere as 6 séries de metais, todas com lastro LME |

### 2.3 Classificação consolidada

`SOURCE_RIGHTS = INCONCLUSIVE` para o uso de exibição das séries com lastro LME.

- Não é **FAIL**: nenhuma restrição expressa e comprovada foi violada pelo uso atual (coleta/armazenamento/derivação são cobertos; a exibição interna é a dimensão pendente de veredito).
- Não é **PASS**: a licença subjacente LME não pôde ser comprovada para exibição corporativa (AC-R1.1-17).

### 2.4 Fidelidade do catálogo (V003 → V004)

- **V003** (`fix/proc-0076-r1`, R1): registrou a proveniência LME e marcou `no_redistribution_pending_lme_review`, mas manteve `internal_display` como uso concedido.
- **V004** (R1.1, aditiva): refine o escopo registrado para `collect;store;derive;internal_display_pending_lme_review;no_redistribution_pending_lme_review` — refletindo fielmente a evidência acima, sem remover dados e sem desativar o feed (já opt-in e OFF).
- V001/V002 permanecem imutáveis.

### 2.5 Estratégia de segurança operacional enquanto a decisão institucional está pendente

- Feed de metais permanece **OFF** (`EXTERNAL_DATA_FEED_METALS_MONTHLY_ENABLED` não habilitado em produção) — nenhum dado novo entra sem autorização.
- Dados históricos já persistidos são **preservados** conforme orientação institucional (nenhuma remoção automática).
- **Quarentena efetiva implementada (R1.2):** a política por operação em `external-data-api/app/domain/usage_policy.py` aplica fail-closed — `internal_display_pending_lme_review` **não** é concessão. As rotas de observações e o catálogo recusam exibição com `EXTERNAL_DATA_USE_NOT_APPROVED` (HTTP 403 no produtor), o catálogo expõe `display_allowed=false` para as seis séries LME-backed e o BFF traduz para `503 source_use_not_approved` + `selectable:false` nos filtros. Ingestão exige concessão explícita de `collect`+`store` no escopo — flag de feed ativada indevidamente não basta. O bloqueio vive no owner dos dados: nenhum consumidor HTTP contorna.
- **Liberação futura** exige (a) decisão institucional/jurídica documentada e (b) migration aditiva alterando o `allowed_use_scope` da fonte. Não existe bypass por configuração nem endpoint administrativo de desbloqueio.
- Decisão pendente: avaliação institucional/jurídica da necessidade de licença LME de display/non-display, ou substituição da fonte por provedor com direito de exibição comprovado.

## 3. Fontes avaliadas e **rejeitadas**

| Fonte | Motivo |
|---|---|
| LME direto (site/API) | Requer licença paga de dados; fora do catálogo (V002 não o semeia) |
| Shockmetais | Termos/licença não comprovados; fora do catálogo |
| Scraping de qualquer fonte | Proibido por política; nenhum crawler existe no código |

## 4. Rastreabilidade

- Catálogo seed: `external-data-api/migrations/V002__seed_market_data_catalog.sql`
- Proveniência LME: `external-data-api/migrations/V003__pink_sheet_lme_provenance.sql`
- Refino de escopo R1.1: `external-data-api/migrations/V004__pink_sheet_internal_display_review.sql`
- Guarda de ingestão: `market_data_ingestion.py` exige fonte ativa/licenciada + feed habilitado por env
- Atribuição ao usuário: contrato BFF → `meta.source`/`attribution` exibido na página e no glossário
