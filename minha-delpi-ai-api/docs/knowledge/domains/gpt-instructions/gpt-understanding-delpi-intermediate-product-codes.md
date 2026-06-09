> **Origem:** `api-delpi-py/GPT_instructions/Understanding DELPI Intermediate Product Codes.md` · **Adaptado em:** 2026-06-09 02:51 UTC · **Alvo:** agente Minha DELPI / RAG operacional
>
> Paths normalizados para a api-delpi atual (`/products/search`, `/products/{code}/…`). Consulte também `api-delpi-rotas-agente.md`.


# 📘 Entendendo Código Intermediário no TOTVS e Desenhos

Este documento resume o conteúdo do arquivo **“ENTENDENDO CÓDIGO INTERMEDIÁRIO NO TOTVS E DESENHOS.pdf”**, servindo como **referência técnica oficial** para interpretação e padronização das descrições dos **produtos intermediários (família 50xx)** utilizados no Protheus e nos desenhos técnicos DELPI.

---

## 🧩 Estrutura Geral do Código Intermediário

O formato padrão de um código intermediário é:

```
50xx xxxx xx xxx xxxx-xx/xx-xxxx-xxxx
```

| Segmento      | Significado                   | Exemplo                             | Fonte         |
| ------------- | ----------------------------- | ----------------------------------- | ------------- |
| **50xx**      | Família do intermediário      | 5023 = Cabo com terminal e isolador | Página 3      |
| **xxxx**      | Sequência criada pelo sistema | 2222                                | Página 13     |
| **xx**        | Tipo e bitola do cabo         | CB1,50 = Cabo EPR 1,5mm²            | Página 4–5    |
| **xxxx**      | Cor do cabo (4 letras)        | VERD = Verde                        | Página 6      |
| **xxxxx**     | Comprimento do cabo (mm)      | 00255 = 255mm                       | Página 7      |
| **xx/xx**     | Tamanho do decape (E/D)       | 06/06 = 6mm esquerdo e direito      | Páginas 8–9   |
| **xxxx-xxxx** | Terminais e isoladores (E/D)  | 6314–0111                           | Páginas 10–11 |

---

## 🎨 Códigos de Cor (Padrão de 4 Letras)

Conforme ilustrado na _figura da página 6_, cada cor de cabo deve ser representada pelas **4 primeiras letras do nome da cor**, conforme tabela abaixo:

| Cor      | Código |
| -------- | ------ |
| Azul     | AZUL   |
| Branco   | BRAN   |
| Laranja  | LARA   |
| Marrom   | MARR   |
| Rosa     | ROSA   |
| Verde    | VERD   |
| Violeta  | VIOL   |
| Amarelo  | AMAR   |
| Cinza    | CINZ   |
| Lilás    | LILA   |
| Preto    | PRET   |
| Roxo     | ROXO   |
| Vermelho | VERM   |

📘 _Fonte: página 6 do documento original._

---

## ⚙️ Material de Isolação e Bitola

Conforme apresentado nas páginas 4 e 5:

| Código | Material | Exemplo                               |
| ------ | -------- | ------------------------------------- |
| **CA** | PVC      | CA18VERM = Cabo PVC 18AWG vermelho    |
| **CB** | EPR      | CB1,50VERD = Cabo EPR 1,5mm² verde    |
| **CF** | Silicone | CF18AZUL = Cabo silicone 18AWG azul   |
| **CT** | Teflon   | CT2,50VERD = Cabo teflon 2,5mm² verde |
| **CV** | Especial | CV16VERD = Cabo especial 16AWG verde  |

📘 _Fontes: páginas 4–5 do documento original._

---

## 📏 Comprimento e Decape

-   **Comprimento:** Sempre em milímetros (mm). _(Página 7)_
-   **Decape esquerdo e direito:** Expressos em milímetros e separados por barra (/). _(Páginas 8–9)_

**Exemplo:**

-   `00255/06/06` → comprimento 255mm, decape esquerdo 6mm e direito 06mm.
-   `00042/06/11` → comprimento 42mm, decape esquerdo 6mm e direito 11mm.

---

## 🔩 Terminais e Isoladores

De acordo com as páginas 10–11, o código dos terminais e isoladores segue a seguinte regra:

-   **Os dois últimos dígitos** de cada código compõem o final do intermediário.
-   São indicados **na sequência: terminal-esquerdo / isolador-esquerdo / terminal-direito / isolador-direito.**

**Exemplo:**  
`6314–0111` → Terminal esquerdo **63**, isolador esquerdo **14**, terminal direito **01**, isolador direito **11**.

📘 _Fonte: páginas 10–11 do documento original._

---

## 🧠 Como Criar um Código Intermediário (Resumo)

> Conforme o diagrama da _página 13_, a formação do código é feita combinando todos os elementos conforme a norma abaixo:

```
50xx xxxx xx xxx xxxx-xx/xx-xxxx-xxxx
```

| Etapa | Descrição                                           |
| ----- | --------------------------------------------------- |
| 1️⃣    | Selecionar a **família** (5021 a 5058)              |
| 2️⃣    | O sistema gera a **sequência numérica** (xxxx)      |
| 3️⃣    | Inserir o **tipo e bitola do cabo** (CA, CB, CF...) |
| 4️⃣    | Definir a **cor (4 letras)**                        |
| 5️⃣    | Inserir **comprimento em mm**                       |
| 6️⃣    | Inserir **decapes esquerdo/direito**                |
| 7️⃣    | Definir **terminais e isoladores (E/D)**            |

---

## 🧾 Exemplo Completo

Conforme a _página 14 do documento original_:

```
50232222 CB1,50VERD-00255/06/06–6314–0111
```

**Descrição técnica correspondente:**

> Intermediário com terminal e isolador; Cabo EPR; Bitola 1,50mm²; Cor verde; Comprimento 255mm; Decape esquerdo 06mm; Decape direito 06mm; Terminal e isolador esquerda 10080063 e 10090014; Terminal e isolador direita 10080001 e 10090011.

---

## 📚 Referências de Página

| Página | Conteúdo Principal           |
| ------ | ---------------------------- |
| 3      | Códigos iniciais (5021–5058) |
| 4–5    | Isolação e bitola            |
| 6      | Cores (código de 4 letras)   |
| 7      | Comprimento em mm            |
| 8–9    | Decape esquerdo e direito    |
| 10–11  | Terminais e isoladores       |
| 13     | Diagrama completo do código  |
| 14     | Exemplo prático final        |

---

## ✅ Aplicação na Análise de Desenhos DELPI

Este documento deve ser **citado como referência complementar** no tópico:

> “Criação e Validação de Descrição de Produto Intermediário” do arquivo `drawing_analyser_instructions.md`.

Ele fornece as **regras de interpretação e geração de descrições automáticas** que o agente deve aplicar ao cruzar as informações do desenho com os dados do produto intermediário (50xx) consultados via API DELPI.