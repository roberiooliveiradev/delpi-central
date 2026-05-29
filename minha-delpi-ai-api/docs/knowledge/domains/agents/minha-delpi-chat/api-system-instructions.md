> **Origem:** `api-delpi-py/GPT_instructions/system_api_instructions.md` · **Adaptado em:** 2026-05-29 18:03 UTC · **Alvo:** agente Minha DELPI / RAG operacional
>
> Paths normalizados para a api-delpi atual (`/products/search`, `/products/{code}/...`). Consulte também `api-delpi-rotas-agente.md`.

# ⚙️ Guia de Uso — System API (DELPI)

## 📘 Descrição

A **System API** é responsável por consultas estruturais ao banco **Protheus**, permitindo ao agente explorar tabelas, colunas e descrições do dicionário de dados (SX2010 e SX3010).
Agora com **busca semântica aprimorada**, o agente consegue encontrar tabelas mesmo que a descrição não bata exatamente com o texto pesquisado.

---

## 🚀 Endpoints Principais

| Método | Endpoint | Descrição |
| ------ | ------------------------------------ | ------------------------------------------------------------ |
| `GET` | `/system/tables` | Lista tabelas do Protheus com suporte à paginação |
| `GET` | `/system/tables/{tableName}` | Retorna os detalhes de uma tabela específica |
| `GET` | `/system/tables/{tableName}/columns` | Lista as colunas da tabela (SX3) |
| `GET` | `/system/tables/search` | 🔍 Busca tabelas pela descrição (SX2), com ranking semântico |

---

## 🔍 Parâmetros Gerais

| Parâmetro | Tipo | Padrão | Descrição |
| ------------- | ---- | ------ | ------------------------------------------------- |
| `page` | int | 1 | Número da página de retorno |
| `limit` | int | 50 | Quantidade de registros por página |
| `tableName` | str | — | Nome lógico da tabela (ex: `SB1010`, `SC2010`) |
| `description` | str | — | Texto de busca (ex: “Descrição Genérica Produto”) |

---

## 🧩 Novidades — Busca Semântica

A rota `/system/tables/search` utiliza um algoritmo híbrido:

1. Busca inicial por **termos exatos** via `LIKE` (rápida).
2. Se o retorno for pequeno, ativa o **fallback total** (varre SX2010 inteira).
3. O **ranking é calculado em Python**, considerando:
- Similaridade global (`SequenceMatcher`);
- Cobertura de palavras da frase pesquisada;
- Ordem das palavras no nome da tabela;
- Tamanho proporcional do texto.

### 🧠 Fórmula de ranking simplificada:

```
TotalScore = (seq_ratio * 60 + coverage * 25 + order * 10 + length * 5) * 100
```

> Onde cada fator é normalizado entre 0 e 1.

---

## 📊 Exemplo de Busca Semântica

### 🔹 Requisição

```http
GET /system/tables/search?description=Descrição Genérica Produto&page=1&limit=20
```

### 🔹 Resposta

```json
{
"success": true,
"message": "Busca de tabelas realizada com sucesso!",
"data": {
"page": 1,
"page_size": 20,
"total_records": 269,
"results": [
{
"X2_ARQUIVO": "SB1010",
"X2_NOME": "Descrição Genérica do Produto",
"X2_CHAVE": "B1_FILIAL+B1_COD",
"total_score": 93.5,
"similarity_ratio": 0.91,
"coverage_ratio": 1.0,
"order_ratio": 1.0
},
{
"X2_ARQUIVO": "HJ3010",
"X2_NOME": "Dimensão Produto Comercial",
"X2_CHAVE": "HJ3_FILIAL+HJ3_COD",
"total_score": 63.2
}
]
}
}
```

---

## 🧠 Diretrizes para o Agente GPT

- Sempre que o usuário solicitar **busca por descrição de tabela**, use a rota:
**`GET /system/tables/search?description={texto}`**
- Caso o usuário peça **detalhes de uma tabela**, use:
**`GET /system/tables/{tableName}`**
- Para verificar **colunas e tipos**, utilize:
**`GET /system/tables/{tableName}/columns`**
- Caso o usuário deseje **listar todas as tabelas**, utilize:
**`GET /system/tables?page={n}&limit={m}`**
- Quando a busca retornar poucos resultados, o agente deve informar:
“O sistema ativou o fallback semântico total da SX2010.”

---

## ⚙️ Boas Práticas

- Sempre validar se a tabela possui o campo `D_E_L_E_T_` antes de montar filtros.
- Utilize paginação (`page`, `limit`) para evitar sobrecarga.
- Para termos genéricos (“produto”, “ordem”, “cliente”), use a busca semântica.
- Para buscas exatas, use o nome lógico da tabela (`SB1`, `SC2`, `SA1`).

---

## 🧭 Fluxo Recomendado ao Agente

1. Receber o termo de busca do usuário.
2. Chamar `/system/tables/search` para localizar tabelas relacionadas.
3. Exibir o nome lógico (`X2_ARQUIVO`) e a descrição (`X2_NOME`).
4. Se o usuário confirmar uma tabela, chamar `/system/tables/{tableName}` para detalhar.
5. Caso precise das colunas, usar `/system/tables/{tableName}/columns`.

---

## 🧩 Observação Final

Esta rota faz parte do módulo **SystemRepository** e é implementada com suporte a:

- Fallback inteligente;
- Busca **case-insensitive**;
- Ranking ajustável via Python.