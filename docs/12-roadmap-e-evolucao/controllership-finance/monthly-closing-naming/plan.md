# Plano — «Fechamento mensal da Controladoria» no lugar de PROC-0072

## 1. Problema

O usuário pergunta "como funciona o fechamento mensal?" e a CLARA responde com "PROC-0072 — Ficha do processo…", "Processo: PROC-0072 — Gestão do Fechamento Mensal da Controladoria", "Execução `CF-PROC0072-…`" e o caminho `docs/12-roadmap-e-evolucao/…` como citação. Teste em PROD (14/11/2026, `knowledge search "como funciona o fechamento mensal etapas"`): 4 dos 5 itens trazem PROC-0072 no título, no `heading_path` ou no trecho.

`PROC-0072` é o código do macroprocesso no Transformômetro (TÉO). O nome do macroprocesso é **Fechamento mensal da Controladoria** (owner, 14/11/2026). O código confunde quem usa o Portal e a CLARA.

## 2. Origens (inventário de 14/11/2026, HEAD `01f8df42`+)

| # | Origem | Onde | Chega ao usuário? |
|---|---|---|---|
| O1 | Instruções do conector MCP | `controllership-finance-api/.../interface/mcp/branding.py` (`CLARA_MCP_INSTRUCTIONS`, `CLARA_MISSION`, docstring) | Sim — todo cliente MCP lê antes de responder |
| O2 | Descrição da tool `knowledge` | `.../interface/mcp/server.py` ("Base de conhecimento PROC-0072") | Sim — o modelo lê em toda conversa |
| O3 | Inteligência da CLARA | `.../content/clara_agent_intelligence.json` (`identity.ecosystem`, `knowledge_domains`) | Sim — identidade e domínios |
| O4 | Base de conhecimento (corpus) | 76 das 115 fontes de `corpus_manifest.py` e `corpus_manifest_lnf.py`: 141 menções em texto, 147 em identificadores de execução (`CF-PROC0072-…`), 26 em nomes de arquivo citados; nomes de fonte com PROC-0072 (`doc-02`, `doc-90`, `doc-118`, `doc-156`, `ficha-processo`) | Sim — título, `heading_path`, trecho e citação |
| O5 | Citação | `citation_locator.document` = caminho do repositório | Sim — a diretiva manda apresentar o locator |
| O6 | Plugin da CLARA (skills) | descrição da skill `clara`, README, manifesto | Sim — corrigido pelo Claude, fora desta trilha |
| O7 | Técnico, não visível | migrations V001/V002/V011 (comentários e `process_id DEFAULT 'PROC-0072'`), comentários e ids de teste no MFE (`CF-PROC0072-…`), nomes de arquivo `*-proc0072-*` | Não |

A persona servida por `get_context(topic='persona')` e as telas do Portal **não** mostram o código.

## 3. Decisões

| # | Decisão | Origem |
|---|---|---|
| D1 | Nome do macroprocesso para o usuário: **Fechamento mensal da Controladoria** (em frase, "o fechamento mensal"). | owner, 14/11/2026 |
| D2 | Todas as fontes continuam na base: são documentação legítima do Portal. Muda o texto, não o inventário. | owner, 14/11/2026 |
| D3 | O código `PROC-0072` sai de todo texto que o usuário vê. Fica **uma** vez, na ficha do fechamento mensal (§Identificação: "Código no Transformômetro (TÉO): PROC-0072"), para rastreabilidade; a CLARA só o diz se o usuário perguntar pelo código. | Claude (proposta; owner pode vetar) |
| D4 | "Central de Fechamento" continua como nome da área no Portal. Só o código sai. | Claude (assumido; owner pode mudar depois) |
| D5 | Citação mostrada ao usuário = nome da fonte + seção ("Ficha do Fechamento mensal da Controladoria › Identificação"), não o caminho do repositório. O `citation_locator` técnico continua no retorno para auditoria. | Claude (assumido; owner pode mudar depois) |
| D6 | Identificadores técnicos ficam como estão (O7 e os ids `CF-PROC0072-…`): mudar quebraria a rastreabilidade com commits, testes e o histórico. A CLARA não mostra esses ids ao usuário (diretiva). | Claude |

## 4. Regras de substituição (texto)

Aplicar em ordem, revisando cada ocorrência no contexto (não é troca cega):

| # | De | Para |
|---|---|---|
| S1 | `PROC-0072 — Gestão do Fechamento Mensal da Controladoria` | `Fechamento mensal da Controladoria` |
| S2 | `PROC-0072 — Ficha do processo de fechamento mensal` (título) | `Ficha do Fechamento mensal da Controladoria` |
| S3 | `fechamento mensal … (PROC-0072)` (parênteses depois do nome) | remover os parênteses |
| S4 | `processo PROC-0072`, `o PROC-0072` | `o macroprocesso Fechamento mensal da Controladoria` / `o fechamento mensal` |
| S5 | prefixo de seção `PROC-0072 — <assunto>` | `<assunto>` |
| S6 | `PROC-0072` sozinho como referência ao processo | `Fechamento mensal da Controladoria` |
| S7 | `PROC-0072 ↔ TÉO` (crosswalk) | `Fechamento mensal da Controladoria ↔ TÉO` |

Gramática e sentido conferidos em cada troca; frase que fica redundante é reescrita.

## 5. Exceções (não alterar)

- **Migrations já aplicadas** (V001, V002, V011 e qualquer outra): nunca editar — muda o checksum. `process_id DEFAULT 'PROC-0072'` continua (é o código do TÉO, campo técnico).
- **Nomes de arquivo** (`02-proc-0072-…`, `118-…-proc0072.md` etc.): não renomear (links, `source_id`, locators e histórico).
- **Identificadores de execução** (`CF-PROC0072-…`), nomes de teste, SHAs, comentários de código no MFE.
- **A linha de rastreabilidade da D3**.
- Documentos fora do repositório (instruções do projeto no claude.ai, TÉO): ficam com o owner.

## 6. O que muda no produto

1. **O1–O3** — instruções, missão, descrição da tool e inteligência da CLARA usam o nome (D1). Diretiva nova nas instruções: "Nunca mostre ao usuário códigos internos — código do processo no TÉO, ids de execução, números de documento de projeto, commits, caminhos de arquivo. Use o nome de negócio. O código do TÉO só se o usuário pedir." `clara_agent_intelligence.json` com versão nova.
2. **O4** — texto das 76 fontes pelas regras S1–S7; nomes de fonte no manifesto sem o código; docstrings e ajuda da CLI de ingestão sem o código.
3. **O5** — o item de conhecimento ganha `source_title` (nome humano da fonte) e `display_citation` ("<nome da fonte> › <seção>"), aditivos. A diretiva de citação passa a mandar mostrar `display_citation`; o `citation_locator` continua no retorno.
4. **Corpus republicado** em HML e PROD (publicação governada).

## 7. Critério de aceite

1. `grep` no repositório: `PROC-0072` só nas exceções do §5 e na linha da D3 (lista conferida no report).
2. Corpus publicado em PROD: nenhum item publicado com `PROC-0072` no título, `heading_path` ou conteúdo, exceto o item da §Identificação da ficha do fechamento.
3. MCP de PROD: instruções do servidor e descrição das tools sem `PROC-0072`.
4. CLARA em PROD:
   - "como funciona o fechamento mensal?" → resposta e citação sem código, sem `CF-…`, sem caminho de arquivo;
   - "qual é o código do fechamento mensal no TÉO?" → "PROC-0072", citando a ficha.
5. Testes automatizados que travam a regra (corpus e superfície MCP) — §track N4.
6. Nenhuma regressão: suíte da BFF verde contra o commit pai; MCP com as seis tools.
