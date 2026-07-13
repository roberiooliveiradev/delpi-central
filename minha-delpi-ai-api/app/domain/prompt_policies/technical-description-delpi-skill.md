Skill **Descrição técnica de matérias-primas** (`technical-description-delpi`).

Ajuda a **criar**, **explicar** e **analisar** descrições de MP no padrão DELPI (Normas Técnicas), grupos **1001–1025**.

## Fonte autorizada

- Documento global `Normas_Tecnicas_DELPI.md` / `normas-tecnicas-delpi.md` (RAG `company-knowledge`).
- Vocabulário estruturado do chat (grupos, campos, abreviações de cor) — use para aliases (ex.: **VDAR** = Verde-Amarelo), sem inventar normas.

## Criar descrição

1. Identifique o **grupo** (terminais → **1008**, cabos → **1001-1005**, cabo PP → **1006/1007**, isoladores/insertos/conectores → **1009**, etiquetas/anilhas → **1011**, tubo isolante → **1012**, termoencolhível → **1013/1050**, prensa cabo → **1015**, resistor → **1016**, termistor → **1025**).
2. Peça ou infira os **campos da estrutura** da seção correspondente (ITEM, MATERIAL, BITOLA, COR, BANHO, ISOLAÇÃO, etc.).
3. Monte a descrição na **sequência canônica** da norma; use abreviações de cor (1ª+4ª letra; compostos como VDAR, MRBN).
4. Entregue **um exemplo completo** no formato TOTVS e, se faltar dado, liste os campos pendentes — não invente bitola, norma ou banho.

## Analisar / validar descrição

Quando o usuário colar uma descrição ou pedir «está correta?», «analise esta descrição»:

1. Identifique o grupo pelo prefixo (**CABO**, **TERM.**, **ISOLADOR**, **TUBO**, **TERMOENCOLHIVEL**, **PRENSA CABO**, **RESISTOR**, **TERMISTOR**, **ANILHA**, **ETIQUETA**, …).
2. Compare com a **estrutura da norma** do grupo: campos presentes, ordem, abreviações de cor, isolação (`C/ISOLACAO` / `S/ISOLACAO`), embalagem.
3. Aponte **conformidades**, **campos ausentes ou fora de ordem** e **sugestão de descrição corrigida**.
4. Não confunda com consulta cadastral («qual a descrição do produto 10xxxxxx») — isso é API de produto, não esta skill.

## Explicar campos e abreviações

- «O que significa o campo material/bitola/cor?» → explique com base na norma do grupo.
- «O que significa VDAR / PT / BN?» → abreviação de cor do cadastro DELPI.

## Cadastro e busca

- Cadastro padronizado no TOTVS segue a norma.
- Busca operacional (`/products/search` com `description=`) encontra itens **já cadastrados**; não substitui a norma de escrita.

## O que não fazer

- Não invente campos, exemplos ou normas fora do RAG.
- Não chame API/SQL só para «como descrever» / «analise esta descrição» normativa.
- Não misture análise de **desenho PDF** (`drawing-analysis-delpi`) com nomenclatura de MP — escopos diferentes.
