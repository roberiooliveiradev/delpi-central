# Trilha — Monthly closing naming (N0–N5)

Fonte: [plan.md](./plan.md). Autoridade: instruções oficiais do arquiteto e `.cursor` > este track > plan.md.

## 1. Regras

1. `main`, sem branch, sem stash/reset/clean. Commits só com os arquivos da etapa (outros agentes trabalham no repositório). Push a cada etapa; recusa por fast-forward → `fetch --depth=80` + rebase em `origin/main` + push.
2. Protocolo por etapa: LER → INVENTARIAR → ALTERAR (mínimo) → TESTAR → VERIFICAR → DOCUMENTAR (quadro e registro deste track no mesmo commit) → REPORTAR.
3. Até 3 ciclos de correção por problema; no 4º, BLOCKED.
4. Sem tool nova e sem mudar as seis tools da CLARA (só texto de instrução/descrição e campos aditivos no retorno do conhecimento).
5. Sem permission nova. Somente leitura em Protheus, Questor e LNF.
6. Repositório público: nenhum dado real em código, fixture ou doc.
7. Evidência `PROVEN | TO_INVENTORY | INCONCLUSIVE`; teste `PASS | FAIL | TEST_NOT_RUN`.

## 2. Paradas

| # | Quando parar |
|---|---|
| Y1 | 4º ciclo de correção no mesmo problema |
| Y2 | Falha nova na suíte (não pré-existente no commit pai) |
| Y3 | Qualquer alteração exigiria editar migration aplicada ou renomear arquivo (§5 do plano) |
| Y4 | Uma ocorrência cuja troca muda o sentido da regra (ex.: o código é o assunto da frase) — listar e perguntar |
| Y5 | Publicação do corpus em PROD falha ou reduz itens/fontes de forma não explicada |
| Y6 | Falha em PROD → rollback do serviço e parar |

## 3. Quadro de status

| Etapa | Status | SHA |
|---|---|---|
| N0 Inventário | DONE | `b33cf37a4e` |
| N1 Superfície MCP e inteligência | DONE | `e2badedc42` |
| N2 Corpus (texto das fontes e manifesto) | DONE | `d833b46a06` |
| N3 Citação legível | DONE | `1e8bdfc1f6` |
| N4 Testes de trava | DONE | `ca85263433` |
| N5 HML → PROD e republicação do corpus | DONE | (commit N5) |
| N5R Citação limpa (sem ref interna) | DONE | (este commit) |

## 4. Etapas

**N0 — Inventário (somente leitura).** Listar todas as ocorrências de `PROC-0072`, `PROC 0072`, `PROC0072` e `proc-0072` no repositório, classificadas: (a) superfície MCP/inteligência, (b) fonte do corpus (com `source_id`), (c) doc fora do corpus, (d) exceção §5 (migration, nome de arquivo, id de execução, teste, comentário de código). Para (b) e (c), a regra S1–S7 que se aplica. Saída: tabela no report (contagens por classe + amostra) e lista das ocorrências Y4.

**N1 — Superfície MCP e inteligência.**
- `branding.py`: `CLARA_MCP_INSTRUCTIONS` e `CLARA_MISSION` com "Fechamento mensal da Controladoria"; acrescentar a diretiva de identificadores internos (plan §6.1); docstring.
- `server.py`: descrição da tool `knowledge` ("Base de conhecimento do Portal Controladoria & Finanças — fechamento mensal, relatórios, auditoria de entradas e LNF").
- `clara_agent_intelligence.json`: `ecosystem` e `knowledge_domains` com o nome; `version` nova; conferir que `get_context(topic='persona')` continua igual no resto.
- Diretiva de citação (`agent_directives.citations`): mostrar `display_citation` (N3) e a classificação de evidência.

**N2 — Corpus.**
- Texto das fontes (b) e dos docs (c) do mesmo diretório: regras S1–S7, uma a uma, com leitura do contexto. A ficha do fechamento (`fichas/processo-fechamento-ficha.md`) recebe o título novo e, em §Identificação, a única linha "Código no Transformômetro (TÉO): PROC-0072" (D3).
- `corpus_manifest.py` / `corpus_manifest_lnf.py`: nomes de fonte sem o código (ex.: `doc-118` → "Base canônica do Fechamento mensal da Controladoria"); `source_id` e caminhos inalterados; docstrings.
- `corpus_ingestion.py`: docstring e ajuda da CLI.
- Os índices `docs/12-roadmap-e-evolucao/README.md` e `financeiro-controladoria/README.md`: mesma regra.

**N3 — Citação legível.** O item de conhecimento ganha, de forma aditiva, `source_title` (o nome da fonte no manifesto) e `display_citation` (`<source_title> › <último nível do heading_path>`; sem heading, só o título). Contrato da tool `knowledge` documentado; `citation_locator` inalterado. Teste de contrato.

**N4 — Testes de trava.**
- Corpus: teste que percorre as fontes do manifesto e falha se `PROC-0072` aparecer fora da linha da D3 e dos identificadores `CF-PROC0072-…` (que a diretiva esconde).
- Superfície MCP: teste que falha se instruções do servidor, descrição das tools ou `clara_agent_intelligence.json` contiverem `PROC-0072`.
- `display_citation` presente e sem caminho de arquivo.
- Suíte inteira da BFF contra o commit pai.

**N5 — HML → PROD.**
- HML: publicar a BFF; republicar o corpus (governado); conferir `knowledge search "fechamento mensal"` sem código.
- PROD: tag `rollback-monthly-closing-naming-controllership-finance-api` no SHA anterior; publicar a BFF; republicar o corpus (governado); contagem de fontes e itens antes/depois (deve ficar igual, salvo itens que mudaram de título); critério de aceite do plano §7 itens 1–3 conferidos. Falha → rollback (Y6).
- Parar e entregar o report. A verificação pela conversa (§7 item 4) é do Claude.

## 5. Rollback

BFF: imagem anterior pela tag. Corpus: republicar a versão anterior (o pipeline mantém o histórico com `SUPERSEDED`). Nenhuma migration nova nesta trilha.

## 6. Verificação pela CLARA (Claude, depois do N5)

1. `get_context(topic='persona')` e instruções do servidor sem o código.
2. "Como funciona o fechamento mensal?" → sem código, sem `CF-…`, sem caminho; citação "Ficha do Fechamento mensal da Controladoria › …".
3. "O que é o relatório R10?" → idem.
4. "Qual é o código do fechamento mensal no TÉO?" → "PROC-0072", citando a ficha.
5. `knowledge search` com cinco perguntas de fechamento: nenhum item com o código no título ou trecho, salvo o da D3.

## 7. Registro

| Data | Etapa | SHA | Status | Nota |
|---|---|---|---|---|
| 2026-11-14 | plano | — | READY | Plano registrado (doc 169). D1 e D2 do owner; D3–D6 propostas pelo Claude (owner pode vetar). |
| 2026-11-14 | N0 | `b33cf37a4e` | DONE | Inventário em `ab07b642`+. Y4: nenhuma parada. Evidência histórica e docs desta trilha ficam de fora da troca (abaixo). |
| 2026-11-14 | N1 | `e2badedc42` | DONE | Instruções, missão, tool `knowledge`, `ecosystem`/`knowledge_domains` versão `2026.11.14.1` e diretiva de citação (`display_citation`). `get_context(persona)` inalterado no resto. |
| 2026-11-14 | N2 | `d833b46a06` | DONE | S1–S7 nas fontes e nos docs do eixo. Código só na ficha §Identificação. `source_id` e nomes de arquivo intactos. Índices e docstrings do manifesto/ingestão sem o código. Rebase sobre as fichas TES. |
| 2026-11-14 | N3 | `1e8bdfc1f6` | DONE | `source_title` e `display_citation` aditivos na busca e no item. `citation_locator` intacto. Contrato na descrição da tool `knowledge`. |
| 2026-11-14 | N4 | `ca85263433` | DONE | Trava do corpus e da superfície MCP. Suíte BFF local: 1370 passed, 199 skipped; PG 79 skipped (sem Postgres local). Nenhuma falha nova. |
| 2026-11-14 | N5 | (commit N5) | DONE | HML imagem `bb62ceea34c1` e PROD imagem `65b9ab2682f0`, ambas em `ca85263433`, healthy. Tag `rollback-monthly-closing-naming-controllership-finance-api` → `dde564efe3`. Imagem PROD que estava no ar antes do rebuild: `c533f3146afc` (ainda sem N1). Corpus antes: 115 fontes / 2517 publicados. Depois (HML e PROD): 121 / 2637. Versão final PROD `dbbb34ce-7394-454e-8cf0-9f35294d4186`. Delta: +6 fontes TES ainda não publicadas; `lnf-api-doc` de 31 seções obsoletas para 1 (arquivo atual é ponteiro de 360 bytes). `PROC-0072` publicado só no item Identificação de `ficha-processo`. MCP sem o código. |
| 2026-11-14 | N5R | (este commit) | DONE | `display_citation` remove `(doc/docs/GATE/D-…)` da seção e deduplica seção=título. `heading_path`/`citation_locator` intactos. Calculado na leitura → sem republicar corpus. Pytest `test_clara_display_citation.py` 8 PASS. Tag `rollback-monthly-closing-naming-n5r-controllership-finance-api`. |

## 8. Inventário N0 (HEAD de partida `ab07b642`)

Contagem de `PROC-0072` (o código, já sem `CF-PROC0072-…` e sem o token dentro de nome de arquivo).

| Classe | Arquivos | Ocorrências | Regra |
|---|---|---|---|
| (a) MCP e inteligência | 3 | 6 | N1 — nome + diretiva |
| (b) fonte do corpus | 52 | 119 | S1–S7; `source_id` e caminho intactos |
| (c) doc fora do corpus, mesmo eixo | 24 | 35 | S1–S7 |
| (d) exceção §5 | migrations V001/V002/V011 (4 linhas com o código); demais migrations só com `CF-PROC0072-…`; comentários/testes (`test_pg_remainder_build.py`, `test_bpmn_migration.py`, MFE); nomes de arquivo | não trocar | |
| meta desta trilha | 4 | 34 | o código é o assunto do plano; fora do manifesto |
| evidência g082rw/g083 | 4 jsonl | 4888 | snapshot com hash de claim; não é fonte do manifesto |

Amostra (a): `branding.py` missão, instruções e docstring; `server.py` descrição de `knowledge`; `clara_agent_intelligence.json` `ecosystem` e `knowledge_domains`.

Amostra (b): `doc-00` README 17; `doc-82` 13; `doc-118` 5; `doc-90` 5; `doc-156` 4; `ficha-processo` 2. Manifesto: nomes de `doc-02`, `doc-90`, `doc-118`, `doc-156`, `ficha-processo`.

Amostra (c): docs 127, 39, 46, 92 (3 cada); `19-rastreabilidade-teo.md` (`Código: PROC-0072`); índices `docs/12-roadmap-e-evolucao/README.md` e `financeiro-controladoria/README.md`.

Y4 — lidas e não paradas: linha «Código: PROC-0072» (docs 02 e 19) não vira «Código: <nome>»; a linha sai e o código fica só na ficha (D3). `record_read(process=PROC-0072)` (doc 46) conserva o UUID na mesma frase. Checkpoint «perguntar por PROC-0072» (doc 93) passa a perguntar pelo fechamento mensal — o sentido do aceite (CLARA responde com fonte) permanece.
