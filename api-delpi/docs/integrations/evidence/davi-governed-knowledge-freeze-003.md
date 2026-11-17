# DAVI Governed Knowledge — Corpus V3 Freeze (MP norm MP1008 generic revision)

**taskId:** `EVA-E1-VAL01-G25-L2-B-MP1008-NORMATIVE-PUBLICATION-AND-ENGINE-ALIGNMENT-01`
**status:** `FROZEN_CONTENT_GOVERNANCE`
**baseCorpus:** `davi-governed-knowledge-freeze-002.md` (V2, `293423bb2cf92b2922f093dc66d388297a74714f`)
**publishedCorpusVersion:** `3`

## Escopo da revisão

V3 é evolução **aditiva** do corpus congelado: os 17 documentos do V2
permanecem membros do corpus (mesmos paths) e **nenhum documento foi removido,
rehasheado retroativamente ou reescrito fora do escopo aprovado**. A única
mudança de conteúdo é a revisão normativa autorizada da seção **Terminais
(Genérico)** do grupo 1008 em
`api-delpi/docs/api/padroes-totvs/normas-tecnicas-descricao-materias-primas.md`,
publicada via PR #238 (merge `f0f6b02606`). Os demais 16 documentos V2
permanecem byte-íntegros; manifesto/índice/freeze V1 e V2 continuam válidos e
servíveis via `corpus_version=1` e `corpus_version=2`.

## Gate de autoridade normativa (registro)

```text
NORMATIVE_SOURCE       = api-delpi/docs/api/padroes-totvs/normas-tecnicas-descricao-materias-primas.md
BUSINESS_OWNER         = ENGENHARIA — elaboração Robério Oliveira, revisão José
                         (bloco de autoria registrado em cada seção normativa)
REVISION_AUTHORITY     = PR #238 — "Revisão normativa autorizada — 17/11/2026"
                         registrada no próprio documento; autorização expressa
                         do solicitante ao texto normativo na delpi-central;
                         Coordination G25-L2-B (EVA — Architecture)
REVISION_MERGE         = f0f6b02606 (PR #238 head fddd88d5bc, base d1e23f930f)
REVISION_SCOPE         = SOMENTE estrutura "Terminais (Genérico)" do grupo 1008:
                         RANGE DA BITOLA aceita MM2 ou AWG (sem conversão
                         automática AWG ↔ mm²); EMBALAGEM aceita GRANEL,
                         FITADO, BLISTER ou CARRETEL (sem equivalência
                         automática CARRETEL → FITADO). Demais estruturas 1008
                         e demais grupos exigem ratificação própria.
V1_V2_IMMUTABILITY     = YES — manifesto/freeze/tópicos V1 e V2 inalterados;
                         hashes pinados permanecem reproduzíveis.
INTENDED_AUDIENCE      = consumidores MCP autorizados via read_governed_technical_knowledge
PUBLICATION_AUTHORIZED = YES — mesma cadeia de autoridade do freeze-002;
                         guidance, não verdade de domínio.
```

## Normative comparison (resumo)

- `sha256` anterior da norma MP (`66aa9c13…4bd2`, manifesto V2) permanece
  verificável via `corpus_version=2`; o novo conteúdo recebe identidade própria
  no manifesto V3 (`source_sha256` do path 16).
- Nenhuma divergência foi introduzida nas seções normativas fora do escopo
  aprovado (diff PR #238 limita-se à seção Terminais (Genérico)).
- Cópias históricas (`sources/gpt-instructions`, `domains/global`, extratos)
  permanecem referências de proveniência V1/V2; não foram retroeditadas —
  divergência registrada para saneamento futuro, nunca reconciliação silenciosa.

## Authority boundary

```text
KNOWLEDGE DOCUMENT != SOURCE OF TRUTH
DOCUMENTATION != AUTHORIZATION
```

As normas explicam descrição e nomenclatura; não concedem permissão, não
redefinem cadastros e não substituem reads autorizados do backend.

## FROZEN_CORPUS_V3

| # | Source path | Scope |
|---|-------------|-------|
| 1 | `api-delpi/docs/api/supplies-inventory-adjustments.md` | inventory adjustment semantics |
| 2 | `api-delpi/docs/api/supplies-stock-balances.md` | warehouse stock balances |
| 3 | `api-delpi/docs/api/supplies-purchase-order-otd.md` | purchase-order OTD |
| 4 | `api-delpi/docs/api/comercial-sales-order-otd.md` | sales-order OTD |
| 5 | `api-delpi/docs/api/padroes-totvs/armazem-custo.md` | warehouse cost model |
| 6 | `api-delpi/docs/api/padroes-totvs/filiais.md` | branch/filial semantics |
| 7 | `api-delpi/docs/api/padroes-totvs/unidades-medida.md` | measurement units |
| 8 | `api-delpi/docs/api/padroes-totvs/producao-entrada-estoque.md` | production stock entry |
| 9 | `api-delpi/docs/api/padroes-totvs/apontamento-operacao-hza.md` | HZA operation reporting |
| 10 | `api-delpi/docs/api/padroes-totvs/cadastro-produto.md` | product master (SB1) |
| 11 | `api-delpi/docs/api/padroes-totvs/ordem-producao-chave.md` | production-order key |
| 12 | `api-delpi/docs/api/padroes-totvs/materiais-terceiros-sb6.md` | third-party materials (SB6) |
| 13 | `api-delpi/docs/api/padroes-totvs/carteira-semanal-previsto-realizado.md` | forecast × realized vocabulary |
| 14 | `api-delpi/docs/api/padroes-totvs/rol-mercado-cfop.md` | ROL market/CFOP semantics |
| 15 | `api-delpi/docs/api/production-machine-load.md` | SH8/HZA machine-load semantics |
| 16 | `api-delpi/docs/api/padroes-totvs/normas-tecnicas-descricao-materias-primas.md` | MP description/classification/nomenclature norm (full; V3 = MP1008 generic AWG + CARRETEL revision) |
| 17 | `api-delpi/docs/api/padroes-totvs/codigos-intermediarios-pi.md` | PI 50xx intermediate-code interpretation (official summary) |

## Compatibility

- `corpus_version=1` → manifesto V1 pinado (`b830a6a9…f49`), 15 tópicos,
  sem os tópicos `mp_description_standards`/`pi_intermediate_codes`
  (NOT_FOUND sob V1).
- `corpus_version=2` → manifesto V2 pinado, 17 tópicos; norma MP na revisão
  pré-PR#238 (`66aa9c13…4bd2`) — reproduzível e imutável.
- `corpus_version=3` → manifesto V3 pinado, 17 tópicos; norma MP na revisão
  PR #238 (AWG + CARRETEL, escopo genérico 1008); default da rota.
- Demais versões → `STALE_VERSION` (409).
