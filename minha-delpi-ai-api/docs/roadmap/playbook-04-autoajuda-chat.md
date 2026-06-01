# Playbook 04 — Autoajuda do Chat

Projeto: Minha DELPI Chat IA  
Escopo: chat comum como manual vivo da plataforma.

> **Implementação (jun/2026):** catálogo `features_catalog.json`, `AssistantCapabilitiesRegistry`, `ChatCapabilitiesService`, painel `?`, release notes, chips de exploração e regressão H1–H12 / A1–A12. Playbook detalhado legado: [melhorias/playbook_autoajuda_autoconhecimento_chat_minha_delpi.md](./melhorias/playbook_autoajuda_autoconhecimento_chat_minha_delpi.md).

---

## 1. Objetivo

Fazer o chat ensinar o usuário a usar o próprio chat, explicando suas funcionalidades, exemplos, limites, agentes, formatos, anexos, lousa, pesquisa web e novidades.

O usuário deve poder perguntar:

- O que você faz?
- Como uso você?
- Como consulto estoque?
- Como anexo arquivo?
- Como uso a lousa?
- Como faço gráfico?
- Qual agente devo escolher?
- O que mudou na última versão?
- Você consegue corrigir textos?
- Como faço uma boa pergunta?
- Como vejo mais linhas?
- Por que não tenho acesso?
- Como uso pesquisa web?

E o chat deve responder de forma clara, útil e atualizada.

---

## 2. Princípio central

O chat deve ser o próprio manual vivo da plataforma.

Isso significa que o usuário não deve depender apenas de documentação externa ou treinamento manual para descobrir como usar a ferramenta.

O próprio chat deve saber explicar:

- o que faz;
- o que não faz;
- como usar cada recurso;
- qual agente escolher;
- quais dados informar;
- quais formatos de resposta existem;
- como usar anexos;
- como usar lousa;
- como pedir gráficos;
- como pedir correção de texto;
- como pedir pesquisa web;
- como resolver erros;
- o que mudou nas últimas versões.

---

## 3. Problemas que essa melhoria resolve

Sem autoajuda forte, o usuário pode:

- não saber o que perguntar;
- não saber qual agente usar;
- não saber que pode anexar arquivos;
- não saber que pode pedir correção de texto;
- não saber que pode colocar respostas na lousa;
- não saber como pedir gráfico;
- não saber como usar pesquisa web;
- não saber interpretar erro ou falta de permissão;
- abandonar o chat por não entender suas capacidades;
- usar sempre comandos básicos e não explorar funcionalidades avançadas.

---

## 4. Fonte única de funcionalidades

Criar um catálogo único de funcionalidades.

Nome sugerido:

`features_catalog.json`

Ou serviço:

`AssistantCapabilitiesRegistry`

Esse catálogo deve consolidar:

- actions disponíveis;
- skills ativas;
- agentes publicados;
- starters do front;
- componentes de UI disponíveis;
- formatos de apresentação;
- recursos de anexos;
- recursos de lousa;
- pesquisa web;
- feature flags;
- release notes;
- permissões por perfil;
- exemplos de uso.

---

## 5. Estrutura sugerida do catálogo

Exemplo:

```json
{
  "version": "2026.06.01",
  "updatedAt": "2026-06-01T10:00:00Z",
  "features": [
    {
      "id": "stock_lookup",
      "title": "Consulta de estoque",
      "category": "operational",
      "status": "available",
      "summary": "Consulta saldo de estoque por produto.",
      "requiresAgent": true,
      "requiresPermission": true,
      "examples": [
        "Qual o estoque do produto 10080001?",
        "Mostre saldo por armazém do produto 10080001."
      ],
      "howToUse": [
        "Escolha um agente com consulta de estoque habilitada.",
        "Informe o código do produto.",
        "Peça o formato desejado, como tabela ou resumo."
      ],
      "limitations": [
        "Depende da permissão do usuário.",
        "Depende da disponibilidade da API."
      ],
      "relatedFeatures": [
        "product_lookup",
        "supplier_lookup",
        "stock_chart"
      ]
    }
  ]
}
```

---

## 6. Categorias de funcionalidades

O catálogo deve organizar recursos por categorias.

### 6.1 Chat básico

- Cumprimentos.
- Perguntas de identidade.
- Ajuda.
- Exemplos.
- Continuação de conversa.
- Pequenas dúvidas.

### 6.2 Textos

- Correção.
- Reescrita.
- E-mails.
- Tradução.
- Resumo.
- Atas.
- Comunicados.
- Checklists.

### 6.3 Consultas operacionais

- Produto.
- Estoque.
- Fornecedores.
- Clientes.
- Estrutura/BOM.
- Onde é usado.
- Compras.
- Vendas.
- Preços.
- Roteiro.
- Inspeção.
- OV/LMP.
- KPIs.
- SQL.

### 6.4 Arquivos e anexos

- PDF.
- Excel.
- CSV.
- Word.
- Imagem.
- JSON.
- Datasheet.
- Relatórios.

### 6.5 Visualizações

- Texto.
- Tabela.
- Gráfico.
- KPI.
- Árvore.
- Cards.
- Checklist.
- Lousa/canvas.
- Exportação.

### 6.6 Pesquisa web

- Pesquisa rápida.
- Pesquisa profunda.
- Fontes oficiais.
- Datasheets.
- Notícias.
- Comparação de fontes.

### 6.7 Agentes

- Agente Produtos.
- Agente Compras.
- Agente Comercial.
- Agente Produção.
- Agente Qualidade.
- Agente Administrativo.
- Agente Técnico.

### 6.8 Segurança

- Permissões.
- Limites.
- Confirmação.
- Dados autorizados.
- Não invenção de dados.

---

## 7. Perguntas que o chat deve entender

### Ajuda geral

- Como usar o chat?
- Me ensine a usar.
- O que você faz?
- O que você consegue fazer?
- Mostre o menu.
- Quais comandos existem?
- Quais funcionalidades existem?
- Quais exemplos posso testar?

### Ajuda por recurso

- Como consulto estoque?
- Como faço gráfico?
- Como uso a lousa?
- Como anexo arquivo?
- Como faço pesquisa na web?
- Como uso um agente?
- Como peço resposta em tabela?
- Como peço próxima página?
- Como comparo dois produtos?
- Como faço uma visão 360°?

### Ajuda por tarefa

- Quero corrigir um texto.
- Quero escrever um e-mail.
- Quero analisar um arquivo.
- Quero consultar uma OV.
- Quero pesquisar um datasheet.
- Quero ver vendas em gráfico.
- Quero transformar uma resposta em ata.

### Ajuda por problema

- Você perdeu o contexto.
- Você não entendeu.
- Como refaço a pergunta?
- Por que não trouxe dados?
- Por que pediu código?
- Por que não tenho acesso?
- Por que não apareceu gráfico?
- Como vejo mais linhas?
- Como altero o formato?

---

## 8. Resposta ideal para “como usar?”

Quando o usuário perguntar “como uso você?”, responder de forma prática.

Exemplo:

Você pode usar o chat de três formas principais:

1. Perguntar livremente  
   Exemplo: “O que você pode fazer?”

2. Consultar dados com um agente  
   Exemplo: “Estoque do produto 10080001”

3. Trabalhar com textos e arquivos  
   Exemplo: “Corrija este texto” ou “Resuma esse PDF”

Escolha uma opção para começar:

Chips sugeridos:

- Consultar produto
- Corrigir texto
- Anexar arquivo
- Ver gráficos
- Usar lousa
- Escolher agente
- Ver tudo

---

## 9. Resposta ideal para “o que você pode fazer?”

A resposta deve ser organizada por categorias, não apenas em texto longo.

Exemplo:

Posso ajudar em várias frentes:

## Operacional

- Consultar produtos.
- Ver estoque.
- Buscar fornecedores.
- Consultar vendas.
- Consultar compras.
- Analisar estrutura/BOM.
- Consultar OV/LMP.

## Textos

- Corrigir textos.
- Escrever e-mails.
- Traduzir.
- Resumir.
- Criar atas.
- Criar comunicados.
- Criar checklists.

## Arquivos

- Resumir PDF.
- Analisar planilhas.
- Extrair pendências.
- Comparar documentos.
- Corrigir textos de arquivos.

## Visualizações

- Tabelas.
- Gráficos.
- KPIs.
- Árvores.
- Lousa/canvas.

## Pesquisa

- Pesquisar na web.
- Buscar fontes oficiais.
- Comparar informações externas.

Chips:

- Quero consultar produto
- Quero corrigir texto
- Quero anexar arquivo
- Quero gerar gráfico
- Quero pesquisar na web

---

## 10. Ajuda contextual por agente

Quando houver agente ativo, a ajuda deve mudar.

### Chat comum

Mensagem:

Você está no chat comum. Posso ajudar com textos, anexos, dúvidas gerais, pesquisa web, lousa e orientação sobre qual agente usar.

### Agente Produtos

Mensagem:

Neste agente, posso ajudar com produto, estoque, fornecedores, estrutura, compras, vendas e visão 360°.

### Agente Compras

Mensagem:

Neste agente, posso ajudar com fornecedores, histórico de compras, preços, lead time, notas de entrada e itens críticos.

### Agente Comercial

Mensagem:

Neste agente, posso ajudar com vendas, clientes, pedidos, faturamento, OV e comparações por período.

### Agente Administrativo

Mensagem:

Neste agente, posso ajudar com e-mails, textos, atas, comunicados, traduções, resumos e checklists.

---

## 11. Ajuda contextual por situação

### Tela inicial

Mostrar:

- principais recursos;
- exemplos;
- categorias;
- botão de ajuda;
- campo de busca de funcionalidade.

### Depois de uma resposta operacional

Sugerir:

- Ver estoque.
- Ver fornecedores.
- Ver vendas.
- Gerar gráfico.
- Colocar na lousa.

### Depois de uma resposta textual

Sugerir:

- Deixar mais formal.
- Deixar mais curto.
- Mostrar alterações.
- Traduzir.
- Colocar na lousa.

### Depois de erro

Sugerir:

- Tentar novamente.
- Verificar código.
- Ampliar filtro.
- Escolher agente.
- Entender o erro.

### Depois de upload de arquivo

Sugerir:

- Resumir.
- Corrigir.
- Traduzir.
- Extrair pendências.
- Criar checklist.
- Colocar na lousa.

---

## 12. Guia de exemplos por categoria

### Produto

- Me fale do produto 10080001.
- Visão 360° do produto 10080001.
- Busque produtos com descrição “cabo”.
- Onde esse componente é usado?

### Estoque

- Qual o estoque do produto 10080001?
- Mostre saldo por armazém.
- Produtos sem estoque.
- Estoque por filial.

### Textos

- Corrija este texto.
- Traduza para inglês.
- Escreva um e-mail profissional.
- Resuma em tópicos.
- Transforme em comunicado.

### Arquivos

- Resuma esse PDF.
- Extraia pendências desse arquivo.
- Transforme esse documento em ata.
- Analise essa planilha.

### Gráficos

- Mostre vendas por mês em linha.
- Faça gráfico de pizza por cliente.
- Mostre ranking em barra horizontal.
- Transforme essa tabela em gráfico.

### Web

- Pesquise na web sobre o manual do CFW500.
- Busque fontes oficiais.
- Compare informações encontradas.
- Procure datasheet do produto.

### Lousa

- Coloque isso na lousa.
- Transforme a lousa em checklist.
- Corrija o texto da lousa.
- Exporte a lousa.

---

## 13. Guia de formatos de resposta

Quando o usuário perguntar “que formatos você consegue mostrar?”, responder:

Posso responder em:

- Texto: explicações e resumos.
- Tabela: listas, comparações e dados estruturados.
- Gráfico: dados numéricos e temporais.
- KPI: indicadores e metas.
- Árvore: estrutura/BOM e hierarquias.
- Cards: menus, resumos e ações rápidas.
- Checklist: tarefas e planos de ação.
- Lousa: rascunhos, atas, relatórios e documentos.
- Arquivo/exportação: quando disponível.

---

## 14. Guia de agentes

Quando o usuário perguntar “o que são agentes?”, responder:

Agentes são versões especializadas do chat.

Use um agente quando precisar de uma área específica, como:

- produtos;
- compras;
- vendas;
- produção;
- qualidade;
- textos;
- análise técnica.

Cada agente pode ter:

- conhecimento próprio;
- ferramentas/actions específicas;
- exemplos de uso;
- limites;
- permissões próprias.

---

## 15. Guia de permissões

Quando o usuário não tiver acesso, explicar de forma simples.

Exemplo:

Algumas consultas dependem do seu perfil e do agente ativo.

Se eu não conseguir acessar algo, posso sugerir:

- escolher outro agente;
- solicitar acesso;
- consultar outra fonte;
- reformular a pergunta;
- usar uma tarefa textual que não dependa de permissão.

---

## 16. Ajuda para “como fazer uma boa pergunta”

Resposta sugerida:

Uma boa pergunta geralmente tem três partes:

1. O que você quer  
   Exemplo: estoque, fornecedor, vendas, correção de texto.

2. O identificador  
   Exemplo: código do produto, OV, cliente ou período.

3. O formato desejado  
   Exemplo: tabela, gráfico, resumo ou checklist.

Exemplo completo:

Mostre o estoque do produto 10080001 em tabela.

Outro exemplo:

Corrija este texto mantendo o sentido original.

---

## 17. Ajuda quando falta parâmetro

Em vez de apenas pedir o dado, ensinar o usuário.

Exemplo:

Para consultar estoque, preciso do código do produto.

Exemplo:

Estoque do produto 10080001

Se você não souber o código, posso buscar por descrição.

Chips:

- Digitar código
- Buscar por descrição
- Ver exemplo

---

## 18. Ajuda quando ocorre erro

Quando uma consulta falhar:

Não responder apenas:

Não encontrei dados.

Responder:

Não consegui concluir essa consulta.

Pode ser por:

- código incorreto;
- falta de permissão;
- API indisponível;
- filtro muito restrito;
- agente inadequado.

Você pode tentar:

- verificar código;
- ampliar filtro;
- trocar agente;
- tentar novamente;
- pedir ajuda sobre essa consulta.

---

## 19. Atualização contínua das funcionalidades

O chat deve ser atualizado sempre que:

- nova action for criada;
- action for removida;
- rota mudar;
- skill nova for adicionada;
- novo gráfico for suportado;
- novo agente for publicado;
- novo recurso de anexo for criado;
- lousa mudar de comportamento;
- pesquisa web mudar;
- permissão mudar;
- comportamento textual for alterado.

---

## 20. Processo obrigatório para novas funcionalidades

Toda nova funcionalidade deve atualizar:

1. Código.
2. Catálogo de funcionalidades.
3. Exemplos.
4. Starters ou chips, se fizer sentido.
5. Help do chat.
6. Testes.
7. Release notes.
8. Documentação interna.

Checklist:

- [ ] Nome da funcionalidade
- [ ] Categoria
- [ ] Descrição curta
- [ ] Como usar
- [ ] Exemplos
- [ ] Permissões necessárias
- [ ] Agentes relacionados
- [ ] Limitações
- [ ] Sugestões/chips
- [ ] Testes de autoajuda
- [ ] Release note

---

## 21. Release notes do chat

Arquivo:

`assistant_release_notes.json`

---

## 22. Resposta para “o que mudou?”

Ver `AssistantCapabilitiesRegistry.format_release_notes_answer()` e chips de exploração.

---

## 23. Busca dentro da ajuda

O chat deve permitir perguntas como:

- ajuda sobre estoque;
- ajuda sobre lousa;
- ajuda sobre e-mail;
- ajuda sobre gráficos;
- ajuda sobre anexos.

Implementação: `ChatCapabilitiesService.build_help_about_answer()` + `AssistantCapabilitiesRegistry.search()`.

---

## 24–32. UI, botão ?, contexto, feedback, observabilidade

Ver Fases 4–5 no playbook legado e `ChatAssistantCatalogService`, `ChatHelpAdoptionService`, `ChatHelpErrorFollowUpService`.

---

## 33. Testes de regressão

Arquivos:

- `tests/fixtures/chat_self_help_cases.py` — casos A1–A12 / H1–H10
- `tests/unit/application/services/test_chat_self_help.py`
- `scripts/smoke_help_capabilities.py`
- `scripts/smoke_self_help_http.py` (HTTP com usuário homologação)

| Caso | Entrada | Esperado |
|------|---------|----------|
| A1 | o que você faz? | lista funcionalidades |
| A2 | como consulto estoque? | explica passos |
| A3 | como anexo arquivo? | explica upload |
| A4 | como gero gráfico? | exemplos |
| A5 | o que mudou? | usa release notes |
| A6 | funcionalidade inexistente | não inventa |
| A7 | agente ativo | ajuda contextual |
| A8 | permissão negada | explica limites |
| A9 | ajuda sobre lousa | comandos de lousa |
| A10 | ajuda sobre texto | exemplos de texto |
| A11 | ajuda após erro | sugere recuperação |
| A12 | ajuda desatualizada | validador de catálogo |

---

## 36. Roadmap de implementação

| Fase | Status |
|------|--------|
| 1 — Organizar ajuda atual | Concluída |
| 2 — Catálogo único | Concluída |
| 3 — Autoatualização / CI | Concluída (`check_help_pr_gate.py`, gerador) |
| 4 — UI de ajuda (`?`) | Concluída |
| 5 — Ajuda inteligente contextual | Parcial (chips, agente, permissões) |

---

## 38. Resumo executivo

A autoajuda transforma o chat em um manual vivo da plataforma.

A regra principal é:

**Toda funcionalidade nova precisa atualizar código, catálogo, exemplos, testes e ajuda.**
