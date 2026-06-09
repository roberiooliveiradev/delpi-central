> **Origem:** `api-delpi-py/GPT_instructions/product_api_instructions.md` · **Adaptado em:** 2026-06-09 02:51 UTC · **Alvo:** agente Minha DELPI / RAG operacional
>
> Paths normalizados para a api-delpi atual (`/products/search`, `/products/{code}/...`). Consulte também `api-delpi-rotas-agente.md`.

# 🧩 Guia de Uso — Product API

## 📘 Descrição

A API **Product** fornece acesso estruturado aos dados de produtos no **TOTVS Protheus**. Esta documentação mantém o **padrão original** e detalha **todas as rotas**, incluindo:

- parâmetros
- tabelas Protheus consultadas
- exemplos de requisição
- exemplos de resposta

Totalmente alinhada ao `product_repository.py`.

---

## 👁️ Visão Geral

A **Product API** centraliza informações técnicas, comerciais, produtivas e fiscais dos produtos cadastrados no Protheus, permitindo:

- consulta detalhada de produtos
- navegação pela estrutura (BOM)
- rastreamento de uso (Where Used)
- análise de roteiros, inspeções e tempos
- acompanhamento de estoque, compras, vendas e preços

É indicada para **integrações sistêmicas**, **análises técnicas** e **uso por agentes GPT**.

---

## ⚙️ Endpoints

| Método | Endpoint | Descrição |
|------|--------|----------|
| GET | `/products/{code}` | Consulta produto por código |
| GET | `/products/search` | Busca de produtos por descrição com score |
| GET | `/products/{code}/structure` | Estrutura do produto (BOM) |
| GET | `/products/{code}/structure/excel` | Exportação pública da estrutura em Excel |
| GET | `/products/{code}/parents` | Produtos pais (Where Used) |
| GET | `/products/{code}/guide` | Roteiro de produção do produto e componentes |
| GET | `/products/{code}/inspection` | Inspeção de processo (QP6 / QP7 / QP8) |
| GET | `/products/{code}/analyser` | Análise completa do produto |
| GET | `/products/{code}/stock` | Estoque por filial e local |
| GET | `/products/{code}/internal-movements` | Movimentações internas de estoque |
| GET | `/products/{code}/suppliers` | Fornecedores vinculados ao produto |
| GET | `/products/{code}/customers` | Clientes amarrados ao produto |
| GET | `/products/{code}/inbound-invoice-items` | Notas fiscais de entrada |
| GET | `/products/{code}/outbound-invoice-items` | Notas fiscais de saída |
| GET | `/products/{code}/purchases` | Histórico resumido de compras |
| GET | `/products/{code}/sales` | Resumo consolidado de vendas |
| GET | `/products/{code}/sales/open-orders` | Pedidos de venda em aberto |
| GET | `/products/{code}/sales/billing` | Faturamento do produto |
| GET | `/products/{code}/pricing` | Preços comerciais do produto |

---

## 🔹 1. Consultar Produto

```http
GET /products/{code}
```

### 📌 Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|-----|------|-------------|----------|
| code | string | ✔ | Código do produto (SB1.B1_COD) |

### 📗 Tabelas consultadas
- SB1010

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": {
"code": "10080522",
"description": "TERMINAL BANDEIRA",
"group_code": "1008",
"unit": "UN",
"type": "PA"
}
}
```

---

## 🔹 2. Busca por Descrição

```http
GET /products/search?description=terminal&page=1&page_size=5
```

### 📌 Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|----------|
| description | string | ✔ | Texto da busca |
| page | int | ✖ | Página |
| page_size | int | ✖ | Registros por página |

### 📗 Tabelas
- SB1010

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": {
"total": 12,
"page": 1,
"page_size": 5,
"results": [
{ "code": "10080522", "description": "TERMINAL BANDEIRA", "relevance_score": 60 }
]
}
}
```

---

## 🔹 3. Estrutura do Produto (BOM)

```http
GET /products/{code}/structure?max_depth=5&page=1&page_size=50
```

### 📌 Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|----------|
| code | string | ✔ | Produto raiz |
| max_depth | int | ✖ | Profundidade da BOM |
| page | int | ✖ | Página |
| page_size | int | ✖ | Registros |

### 📗 Tabelas
- SG1010
- SB1010

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": {
"code": "10080522",
"components": [
{ "code": "20010001", "quantity": 2 }
]
}
}
```

---

## 🔹 4. Estrutura em Excel (Pública)

```http
GET /products/{code}/structure/excel
GET /products/{code}/structure/excel?format=xlsx
```

### 📘 Descrição

Gera e disponibiliza a **estrutura formatada do produto em planilha Excel (formato oficial DELPI)**.

- Esta rota **não requer autenticação** (é pública).
- O arquivo é gerado dinamicamente com formatações, agrupamentos e regras visuais específicas.
- Existem dois modos de uso:
- **Sem parâmetro `format=json`** → Retorna um JSON contendo o link público clicável para download.
- **Com parâmetro `format=xlsx`** → Retorna diretamente o arquivo Excel (StreamingResponse).

---

### 📘 Parâmetros

| Nome | Tipo | Padrão | Descrição |
|------|------|--------|----------|
| code | string | — | Código do produto a ser exportado |
| format | string | json | Use `xlsx` para download direto |

---

### 📗 Tabelas consultadas

- SG1010
- SB1010

---

### 📘 Exemplo de requisição

```http
GET /products/90264135/structure/excel
```

**Resposta (modo link):**

```json
{
"message": "Arquivo Excel gerado com sucesso!",
"download_url": "https://api.transformamaisdelpi.com.br/products/90264135/structure/excel?format=xlsx",
"html_link": "<a href=\"https://api.transformamaisdelpi.com.br/products/90264135/structure/excel?format=xlsx\" target=\"_blank\">📂 Baixar Estrutura 90264135</a>"
}
```

**Resposta (modo download):**

- O navegador inicia automaticamente o download do arquivo `Estrutura_90264135.xlsx`.

---

### 📗 Observações

- O arquivo Excel segue o **padrão de formatação DELPI**, incluindo:
- Agrupamento hierárquico (Produto → Intermediário → MP)
- Cores padronizadas
- Fonte Arial Narrow 10
- Regras visuais para destaque de MPs com unidade “PC”
- Cache configurado por 24h (`Cache-Control: public, max-age=86400`).
- Ideal para integração com agentes GPT e consultas públicas.

---

### 📘 Exemplo de uso com agente GPT

Usuário:

> “Gerar o Excel da estrutura do produto 9026xxx.”

Agente:

> Aqui está o link para baixar o arquivo:
> 👉 [📂 Baixar Estrutura 9026xxxx](https://api.transformamaisdelpi.com.br/products/9026xxxx/structure/excel?download=true)

> Ou apenas visualizar o link em JSON:
> https://api.transformamaisdelpi.com.br/products/9026xxxx/structure/excel

---

### 🔧 Endpoint Interno

- Implementação: `product_routes.py`
- Função: `structure_excel_public`
- Tipo de retorno:
- `JSONResponse` (modo link)
- `StreamingResponse` (modo download)

---

## 🔹 5. Produtos Pais (Where Used)

```http
GET /products/{code}/parents?max_depth=5&page=1&page_size=50
```

### 📗 Tabelas
- SG1010
- SB1010

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": {
"code": "20010001",
"parents": [
{ "code": "10080522", "quantity": 2 }
]
}
}
```

---

## 🔹 6. Roteiro de Produção

```http
GET /products/{code}/guide?page=1&page_size=20&branch=01&max_depth=10
```

### 📗 Tabelas
- SG2010
- SG1010
- SGF010
- SB1010

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": [
{
"product_code": "10080522",
"bom_level": 0,
"operations": [
{ "operation_code": "010", "setup_hours": 0.02 }
]
}
]
}
```

---

## 🔹 7. Inspeção de Processo

```http
GET /products/{code}/inspection?max_depth=10&page=1&page_size=50
```

### 📗 Tabelas
- SG1010
- QP6010
- QP7010
- QP8010

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": [
{
"product": "10080522",
"level": 0,
"QP6": { "QP6_REVI": "01" },
"QP7": [],
"QP8": []
}
]
}
```

---

## 🔹 8. Análise Completa do Produto

```http
GET /products/{code}/analyser?page=1&page_size=20&max_depth=10
```

### 📗 Tabelas
- SB1010
- SG1010
- SG2010 / SGF010
- QP6010 / QP7010 / QP8010

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": {
"product": { "code": "10080522" },
"structure": { },
"guide": [ ],
"inspection": [ ]
}
}
```

---

## 🔹 9. Estoque

```http
GET /products/{code}/stock?page=1&page_size=50&branch=01&location=01
```

### 📗 Tabelas
- SB2010
- SBZ010

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": [
{ "branch": "01", "current_quantity": 1500, "available_quantity": 1500 }
]
}
```

---

## 🔹 10. Fornecedores

```http
GET /products/{code}/suppliers?page=1&page_size=50
```

### 📗 Tabelas
- SA5010
- SA2010
- SC7010 / SD1010

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": [
{ "supplier_code": "000001", "last_price": 2.87 }
]
}
```

---

## 🔹 11. Clientes

```http
GET /products/{code}/customers?page=1&page_size=50
```

### 📗 Tabelas
- SA7010
- SA1010
- SD2010

---

## 🔹 12. NF Entrada

```http
GET /products/{code}/inbound-invoice-items?page=1&page_size=50
```

### 📗 Tabelas
- SD1010
- SB1010
- SA2010

---

## 🔹 13. NF Saída

```http
GET /products/{code}/outbound-invoice-items?page=1&page_size=50
```

### 📗 Tabelas
- SD2010
- SB1010
- SA1010

---

## 🔹 14. Compras

```http
GET /products/{code}/purchases?page=1&page_size=50
```

### 📗 Tabelas
- SC7010
- SA2010

---

## 🔹 15. Vendas

### Resumo
```http
GET /products/{code}/sales
```
Base: SD2010

### Pedidos em aberto
```http
GET /products/{code}/sales/open-orders
```
Base: SC6010

### Faturamento
```http
GET /products/{code}/sales/billing
```
Base: SD2010

---

## 🔹 16. Preços

```http
GET /products/{code}/pricing
```

### 📗 Tabelas
- DA1010
- DA0010
- SB1010

---

## 🔹 17. Movimentações Internas de Produto
```http
GET /products/{code}/internal-movements
```

### 📌 Parâmetros
| Nome | Tipo | Obrigatório | Descrição |
| ---------- | ------ | ----------- | ---------------------------------- |
| code | string | ✔ | Código do produto (SD3.D3_COD) |
| page | int | ✖ | Página (default: 1) |
| page_size | int | ✖ | Registros por página (default: 50) |
| date_start | string | ✖ | Data inicial da movimentação |
| date_end | string | ✖ | Data final da movimentação |
| branch | string | ✖ | Filial (D3_FILIAL) |
| location | string | ✖ | Local de estoque (D3_LOCAL) |
| tm | string | ✖ | Tipo de movimento (D3_TM) |
| op | string | ✖ | Ordem de produção (D3_OP) |

> 📅 Datas aceitam múltiplos formatos (YYYY-MM-DD, DD/MM/YYYY, ISO, etc.), sendo convertidas internamente para o padrão Protheus.

### 📗 Tabelas consultadas

- SD3010 — Movimentações internas
- SB1010 — Cadastro do produto

### 📘 Exemplo de requisição
```http
GET /products/10080522/internal-movements?page=1&page_size=20&branch=01&date_start=2024-01-01
```

### 📘 Exemplo de resposta

```json
{
"success": true,
"data": {
"total": 3,
"page": 1,
"page_size": 20,
"total_pages": 1,
"filters": {
"date_start": "20240101",
"date_end": null,
"branch": "01",
"location": null,
"tm": null,
"op": null
},
"data": [
{
"branch": "01",
"location": "01",
"document": "REQ000123",
"issue_date": "20240115",
"product_code": "10080522",
"product_description": "TERMINAL BANDEIRA",
"unit": "UN",
"movement_type": "501",
"cf": "RE",
"quantity": -200,
"production_order": "OP000045",
"user_name": "PCP01"
}
]
}
}
```

### 📗 Observações Importantes

- ❌ Não inclui notas fiscais
- NF Entrada → SD1010
- NF Saída → SD2010

- ✔ Utilizar esta rota para:
- consumo real de produção
- rastreamento de ajustes
- auditoria de estoque

- Quantidades podem ser:
- positivas → entrada interna
- negativas → saída / consumo

---

## 🧠 Observações Finais

- Todas as rotas retornam `{ success, data }`
- Paginação obrigatória em grandes volumes
- Profundidade recomendada: **5–10 níveis**
- Documentação 100% aderente ao código