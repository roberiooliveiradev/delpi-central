# DAVI Governed Knowledge — Corpus V2 Freeze (MP/PI full norms)

**taskId:** `DAVI-GOVERNED-KNOWLEDGE-MP-PI-FULL-NORMS-V2-IMPLEMENTATION-01`
**status:** `FROZEN_CONTENT_GOVERNANCE`
**baseCorpus:** `davi-governed-knowledge-freeze-001.md` (V1, `d9926cc14a8a4edd1b52775b82cf7353aede75b4`)
**publishedCorpusVersion:** `2`

## Escopo da revisão

V2 é evolução **aditiva** do corpus congelado: os 15 documentos V1 permanecem
byte-íntegros (mesmos paths e hashes do manifesto V1) e duas normas técnicas
completas entram como novos membros. Nenhum documento V1 foi editado, removido
ou rehasheado; o manifesto/índice/freeze V1 continuam válidos e servíveis via
`corpus_version=1`.

## Gate de autoridade normativa (registro)

```text
NORMATIVE_SOURCE (MP)  = minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/Normas_Tecnicas_DELPI.md
NORMATIVE_SOURCE (PI)  = minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/Understanding DELPI Intermediate Product Codes.md
SOURCE_INTRODUCED_AT   = 63cc77bfe60e157623dd77fd7fd335e37735a4e7
BUSINESS_OWNER         = ENGENHARIA — elaboração Robério Oliveira, revisão José
                         (bloco de autoria registrado em cada seção normativa;
                         owner do repositório roberiooliveiradev é o mesmo
                         elaborador registrado)
CURRENTNESS            = cópias sources/gpt-instructions e domains/global idênticas
                         salvo cabeçalho de proveniência; extrato api-delpi é
                         subconjunto consistente; nenhuma revisão posterior
                         divergente localizada no repositório
APPROVAL_EVIDENCE      = AUTORIZAÇÃO OPERACIONAL desta task emitida pelo owner
                         registrado + bloco de autoria por seção +
                         diretrizes_criacao_de_descricao.md declara a norma
                         MP como norma única de descrição
NORMATIVE_SCOPE (MP)   = descrição/classificação/nomenclatura de matérias-primas
                         (grupos 1001–1050; terminais 1008 inclui TERM. BALA)
NORMATIVE_SCOPE (PI)   = interpretação de códigos intermediários família 50xx
                         (resumo oficial do documento de engenharia
                         "ENTENDENDO CÓDIGO INTERMEDIÁRIO NO TOTVS E
                         DESENHOS.pdf" — PDF original não versionado no repo)
INTENDED_AUDIENCE      = consumidores MCP autorizados via read_governed_technical_knowledge
PUBLICATION_AUTHORIZED = YES — cópia integral migrada para
                         api-delpi/docs/api/padroes-totvs/ com cabeçalho de
                         proveniência; guidance, não verdade de domínio
```

## Normative comparison (resumo)

- Cópias `sources/gpt-instructions` × `domains/global/normas-tecnicas-delpi.md`:
  idênticas salvo cabeçalho de sincronização e quebra final — sem divergência
  normativa (revalidado neste HEAD).
- PI `sources` × `domains/agents/.../engenharia-codigos-intermediarios-delpi.md`:
  mesmo conteúdo; a variante de domínio só normaliza cabeçalho/paths.
- Extrato `api-delpi/docs/knowledge/product-vocabulary/normative-product-terms.md`:
  subconjunto de interpretação consistente com a norma integral; permanece como
  extrato READ (não segunda autoridade).
- `diretrizes_criacao_de_descricao.md`: documento operacional do antigo Chat que
  declara `Normas_Tecnicas_DELPI.md` a norma única — corrobora autoridade, não é
  incorporado (contém diretrizes de runtime/agente).
- `TERM.` é prefixo fixo documentado para todos os terminais 1008; `BALA` é o
  tipo técnico de exemplo na seção "Terminais (Genérico)"
  (`TERM. BALA 2,50-6,00MM2 NU GRANEL CURTO UL`).
- Nenhuma contradição com `api-delpi` localizada; divergências futuras devem ser
  registradas, nunca reconciliadas silenciosamente.

## Authority boundary

```text
KNOWLEDGE DOCUMENT != SOURCE OF TRUTH
DOCUMENTATION != AUTHORIZATION
```

As normas explicam descrição e nomenclatura; não concedem permissão, não
redefinem cadastros e não substituem reads autorizados do backend.

## FROZEN_CORPUS_V2

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
| 16 | `api-delpi/docs/api/padroes-totvs/normas-tecnicas-descricao-materias-primas.md` | MP description/classification/nomenclature norm (full) |
| 17 | `api-delpi/docs/api/padroes-totvs/codigos-intermediarios-pi.md` | PI 50xx intermediate-code interpretation (official summary) |

## Compatibility

- `corpus_version=1` → manifesto V1 pinado (`b830a6a9…f49`), 15 tópicos,
  sem os tópicos `mp_description_standards`/`pi_intermediate_codes`
  (NOT_FOUND sob V1).
- `corpus_version=2` → manifesto V2 pinado, 17 tópicos; default da rota.
- Demais versões → `STALE_VERSION` (409).
