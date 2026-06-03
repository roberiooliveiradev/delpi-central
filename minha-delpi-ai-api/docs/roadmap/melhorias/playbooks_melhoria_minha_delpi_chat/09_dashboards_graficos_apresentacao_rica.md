# Playbook 09 — Dashboards, gráficos e apresentação rica

> **Status (03/06/2026):** [Concluído](../STATUS_ROADMAP_MELHORIAS.md) — ver [`playbook-09-apresentacao-rica.md`](../../playbook-09-apresentacao-rica.md) Fases 1–6.


## Objetivo

Definir como o Minha DELPI Chat IA deve usar tabelas, gráficos, árvores, KPIs e cards para apresentar dados de forma clara, interativa e útil.

O chat não deve responder dados complexos apenas em texto. Ele deve escolher o melhor formato.

---

## Formatos disponíveis

- Texto.
- Tabela.
- Gráfico.
- KPI.
- Árvore.
- Cards.
- Checklist.
- Lousa.
- CSV.
- Markdown.

---

## Princípio central

> O formato deve ajudar a decisão, não apenas enfeitar a resposta.

---

## Quando usar tabela

Usar tabela quando houver:

- múltiplas linhas;
- colunas estruturadas;
- comparação;
- resultado operacional;
- lista de produtos;
- estoque por armazém;
- vendas por cliente;
- compras por fornecedor;
- notas fiscais;
- SQL.

Exemplos:

- Produtos encontrados.
- Estoque por filial.
- Fornecedores.
- Clientes.
- OVs.
- NFs.
- Compras.

---

## Quando usar gráfico

Usar gráfico quando houver:

- série temporal;
- valores numéricos;
- comparação de categorias;
- ranking;
- evolução;
- tendência.

Exemplos:

- vendas por mês;
- compras por fornecedor;
- estoque por armazém;
- faturamento por cliente;
- KPI por período;
- produção programada x realizada.

---

## Quando usar KPI

Usar KPI quando houver:

- indicador único;
- meta;
- variação;
- status;
- percentual.

Exemplos:

- OTD.
- OEE.
- EBITDA.
- faturamento do mês.
- saldo total.
- percentual de entrega.

---

## Quando usar árvore

Usar árvore quando houver hierarquia:

- BOM;
- estrutura;
- produto pai/filho;
- componentes;
- organograma;
- dependências.

---

## Quando usar cards

Usar cards para:

- capacidades;
- menu inicial;
- ações rápidas;
- resumo de produto;
- visão 360°;
- alertas;
- próximos passos.

---

## Resposta com apresentação rica

Estrutura:

```md
## Resumo

[conclusão]

[componente rico]

## Próximos passos
[chips]
```

Evitar duplicar tabela em markdown se já existe componente rico.

---

## Interatividade em tabela

A tabela deve permitir:

- ordenar;
- copiar;
- baixar CSV;
- expandir;
- clicar linha;
- filtrar;
- ver detalhes;
- ações por linha.

Ações por linha:

- Detalhar item.
- Ver estoque.
- Ver fornecedores.
- Ver vendas.
- Ver compras.
- Colocar na lousa.

---

## Interatividade em gráfico

O gráfico deve permitir:

- trocar para tabela;
- clicar ponto/barra;
- filtrar período;
- comparar período anterior;
- exportar;
- explicar gráfico.

---

## Interatividade em árvore

A árvore deve permitir:

- ampliar níveis;
- recolher;
- clicar nó;
- ver estoque do componente;
- ver fornecedor;
- onde é usado;
- exportar.

---

## Escolha automática de formato

Criar serviço:

`ChatPresentationDecisionService`

Entrada:

- intent;
- tool result;
- número de linhas;
- tipos de colunas;
- se há datas;
- se há hierarquia;
- preferência do usuário.

Saída:

```json
{
  "preferredFormat": "chart",
  "fallbackFormat": "table",
  "reason": "dados por período com valores numéricos"
}
```

---

## Regras de decisão

| Dados | Formato |
|---|---|
| 1 valor + meta | KPI |
| lista simples | tabela |
| datas + valores | gráfico + tabela |
| hierarquia | árvore |
| texto/documento | markdown |
| comparação | tabela + resumo |
| capacidade/menu | cards |
| resultado vazio | texto + chips |

---

## Preferência do usuário

Se o usuário disser:

- “em tabela” → priorizar tabela.
- “em gráfico” → gráfico, se fizer sentido.
- “resumo executivo” → texto curto.
- “checklist” → checklist.
- “árvore” → árvore, se houver hierarquia.

Se o formato pedido não fizer sentido:

> Não há dados suficientes para um gráfico útil. Organizei em tabela.

---

## Alertas visuais

Usar destaque para:

- saldo zero;
- KPI abaixo da meta;
- atraso;
- valor negativo;
- divergência;
- fornecedor único;
- falta de dados.

---

## Cards de visão 360°

Para produto:

- Cadastro.
- Estoque.
- Fornecedores.
- Compras.
- Vendas.
- Estrutura.
- Riscos.
- Próximos passos.

Cada card pode ter:

- valor;
- status;
- ação.

---

## Exportação

Oferecer:

- CSV para tabelas;
- PNG para gráficos;
- Markdown para lousa;
- PDF para relatório, se implementado;
- copiar para área de transferência.

---

## Testes

- tabela pequena;
- tabela grande;
- gráfico de série temporal;
- gráfico sem dados;
- KPI com meta;
- árvore BOM;
- alternância tabela/gráfico;
- CSV;
- clique em linha;
- apresentação sem duplicar markdown.

---

## Métricas

- uso de tabela;
- uso de gráfico;
- uso de CSV;
- cliques em linha;
- feedback de formato;
- taxa de “formato ruim”;
- uso de expandir;
- uso de chips após gráfico.

---

## Resumo executivo

Apresentação rica transforma o chat em interface de trabalho. A melhoria principal é escolher automaticamente o melhor formato, evitar duplicação, tornar gráficos/tabelas clicáveis e sempre oferecer próximos passos.
