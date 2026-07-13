Skill **Descrição técnica de MP e intermediários** (`technical-description-delpi`).

Ajuda a **criar**, **explicar** e **analisar** descrições no padrão DELPI:

- **Matérias-primas** — Normas Técnicas DELPI, grupos **1001–1025**.
- **Produtos intermediários** — família **50xx** (código estruturado TOTVS / desenhos).

## Fontes autorizadas

1. `Normas_Tecnicas_DELPI.md` / `normas-tecnicas-delpi.md` (RAG `company-knowledge`) — MP.
2. `Understanding DELPI Intermediate Product Codes.md` / `gpt-understanding-delpi-intermediate-product-codes.md` — intermediários 50xx (RAG do agente ou trechos no contexto).
3. Vocabulário estruturado do chat (grupos, campos, cores MP e 4 letras, códigos CA/CB/CF/CT/CV) — use para aliases; **não invente** normas.

## Matérias-primas (1001–1025)

### Criar descrição

1. Identifique o **grupo** (terminais → **1008**, cabos → **1001-1005**, cabo PP → **1006/1007**, isoladores/insertos/conectores → **1009**, etiquetas/anilhas → **1011**, tubo isolante → **1012**, termoencolhível → **1013/1050**, prensa cabo → **1015**, resistor → **1016**, termistor → **1025**).
2. Peça ou infira os **campos da estrutura** da seção correspondente (ITEM, MATERIAL, BITOLA, COR, BANHO, ISOLAÇÃO, etc.).
3. Monte a descrição na **sequência canônica** da norma; use abreviações de cor (1ª+4ª letra; compostos como VDAR, MRBN).
4. Entregue **um exemplo completo** no formato TOTVS e, se faltar dado, liste os campos pendentes — não invente bitola, norma ou banho.

### Analisar / validar descrição de MP

1. Identifique o grupo pelo prefixo (**CABO**, **TERM.**, **ISOLADOR**, **TUBO**, **TERMOENCOLHIVEL**, **PRENSA CABO**, **RESISTOR**, **TERMISTOR**, **ANILHA**, **ETIQUETA**, …).
2. Compare com a **estrutura da norma** do grupo: campos, ordem, abreviações de cor, isolação, embalagem.
3. Aponte conformidades, gaps e sugestão corrigida.
4. Não confunda com consulta cadastral («qual a descrição do produto 10xxxxxx») — isso é API de produto.

## Intermediários (50xx)

Formato canônico (segmentos):

```
50xx xxxx xx xxx xxxx-xx/xx-xxxx-xxxx
```

| Segmento | Significado |
| --- | --- |
| **50xx** | Família (5021–5058) |
| **xxxx** | Sequência do sistema |
| **tipo+bitola** | Isolação + bitola: **CA**=PVC, **CB**=EPR, **CF**=Silicone, **CT**=Teflon, **CV**=Especial (ex.: `CB1,50`) |
| **xxxx** | Cor em **4 letras** (PRET, BRAN, VERD, AZUL, …) |
| **xxxxx** | Comprimento em **mm** |
| **xx/xx** | Decape esquerdo / direito (mm) |
| **xxxx-xxxx** | Terminais e isoladores E/D (2 dígitos cada: term.E + isol.E + term.D + isol.D) |

### Criar / interpretar código intermediário

1. Selecionar família → sequência → isolação/bitola → cor 4 letras → comprimento mm → decapes → terminais/isoladores.
2. Exemplo de referência: `50232222 CB1,50VERD-00255/06/06–6314–0111` → Cabo EPR 1,50 mm² verde; 255 mm; decape 06/06; terminais/isoladores 63-14 / 01-11 (prefixos 1008/1009 no texto técnico).
3. Ao explicar um código colado, **segmente campo a campo**; não invente família ou bitola ausente do texto/RAG.

### Cores intermediário vs MP

- **MP (1001–1025):** abreviação curta (PT, BN, VDAR…).
- **Intermediário (50xx):** sempre **4 letras** (PRET, BRAN, VERD…).

## Explicar campos e abreviações

- Campos material/bitola/cor/decape → norma do grupo ou doc de intermediário.
- **VDAR / PT** → cor de MP; **PRET / VERD** → cor de intermediário.
- **CA / CB / CF / CT / CV** → material de isolação no código intermediário.

## Cadastro e busca

- Cadastro TOTVS segue a norma / estrutura 50xx.
- Busca operacional (`/products/search`) acha itens **já cadastrados**; não substitui a regra de escrita.

## O que não fazer

- Não invente campos, exemplos ou normas fora do RAG / vocabulário.
- Não chame API/SQL só para «como descrever» / «analise esta descrição» / «explique o código intermediário».
- Não misture análise de **desenho PDF** (`drawing-analysis-delpi`) com nomenclatura — escopos diferentes (o desenho pode *citar* 50xx; a regra de código fica nesta skill).
