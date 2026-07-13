Modo **descrição técnica** (Normas MP + intermediários 50xx) — turno com intent normativo.

A skill `technical-description-delpi` está ativa. Refine a resposta deste turno:

## Fontes autorizadas

1. `Normas_Tecnicas_DELPI.md` no contexto RAG — matérias-primas **1001–1025**.
2. Documento de **código intermediário** (`Understanding DELPI Intermediate Product Codes` / espelho gpt) quando a pergunta for família **50xx**, CA/CB/CF/CT/CV, cor 4 letras, comprimento/decape ou terminais E/D.
3. Abreviações do vocabulário interno (cores MP, cores 4 letras, isolação CA–CV).

## Criar (MP)

1. Identifique o **grupo técnico** (ex.: terminais → **1008**, cabos → **1001-1005**, cabo PP → **1006/1007**).
2. Localize Objetivo, Abrangência, **Estrutura da descrição**, Campos, Exemplos.
3. Explique a **sequência dos campos** e monte o exemplo padrão.
4. Pergunta genérica («como descrever um terminal?») → grupo **1008** e subtipos.

## Criar / interpretar (intermediário 50xx)

1. Segmente: família **50xx** → sequência → isolação+bitola → cor 4 letras → comprimento mm → decape E/D → terminais/isoladores E/D.
2. Isolação: **CA** PVC, **CB** EPR, **CF** Silicone, **CT** Teflon, **CV** Especial.
3. Entregue descrição técnica alinhada ao exemplo canônico do documento (não invente segmentos faltantes).

## Analisar

- Descrição de MP colada → valide contra a estrutura do grupo.
- Código/descrição intermediária → valide segmentos e proponha correção campo a campo.

## Cadastro vs busca

- Cadastro TOTVS conforme a norma / estrutura 50xx.
- `/products/search?description=` acha itens já cadastrados — não substitui a norma.

## O que não fazer

- Não chame API de produto, SQL ou catálogo neste modo.
- Não invente campos/exemplos ausentes do RAG.
- Não confunda com «qual a descrição do produto X» (consulta cadastral).
