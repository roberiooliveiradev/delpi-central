# Playbook — Autoajuda, autoconhecimento e atualização contínua do Minha DELPI Chat IA

Projeto: **Minha DELPI Chat IA**

Objetivo: garantir que o chat seja capaz de ensinar usuários a usá-lo, tirar dúvidas sobre si mesmo, explicar suas funcionalidades, orientar escolha de agentes, sugerir exemplos práticos e manter esse conhecimento atualizado sempre que uma funcionalidade for criada, alterada ou removida.

---

## 1. Visão geral

O chat precisa funcionar como o próprio **manual vivo da plataforma**.

O usuário deve conseguir perguntar:

- Como uso você?
- O que você consegue fazer?
- Como consulto estoque?
- Como uso um agente?
- Como anexo arquivo?
- Como faço gráfico?
- Como uso a lousa?
- Como peço para corrigir texto?
- Como faço pesquisa na web?
- O que mudou na última versão?
- Por que não tenho acesso?
- Como vejo mais linhas?
- Como continuo uma resposta anterior?

E o chat deve responder com clareza, exemplos e próximos passos.

---

## 2. Base atual do projeto

O projeto já possui uma boa base para isso.

### `capabilities.json`

O arquivo `capabilities.json` já centraliza respostas para perguntas como “o que você pode fazer?”, “quais funcionalidades?”, “quais comandos?”, “o que consegue consultar?”, “menu” e “ajuda”.

Ele também já lista capacidades sempre disponíveis, consultas operacionais, skills, actions, dicas de uso e exemplos.

### `identity.json`

O arquivo `identity.json` já cobre quem é o assistente, o que ele faz, seus limites, origem, uso e primeiros passos.

Ele também define a persona do assistente como amigável, clara, corporativa e com bom humor moderado.

### `chatHomeStarters.ts`

O front já possui starters como:

- O que você pode fazer?
- Consultar produto
- Ver estoque
- Buscar fornecedor
- Ver vendas
- Corrigir texto
- E-mail formal
- Quem é você?

Isso indica que o chat já começou a ensinar o usuário, mas ainda pode evoluir para um sistema completo de autoajuda.

---

## 3. Princípio central

> O chat deve ser o próprio manual vivo da plataforma.

Isso significa que o usuário não deve depender apenas de treinamento externo ou documentação separada para descobrir como usar a ferramenta.

O chat deve explicar:

- o que faz;
- o que não faz;
- como usar cada funcionalidade;
- qual agente escolher;
- quais dados informar;
- quais formatos pode gerar;
- como usar anexos;
- como usar lousa;
- como usar pesquisa web;
- como pedir gráficos;
- como corrigir textos;
- como continuar uma pergunta anterior;
- como resolver erros.

---

## 4. Conceito: Chat Self-Help

Criar uma camada chamada:

`ChatSelfHelpService`

ou

`ChatAssistantKnowledgeService`

Essa camada deve responder perguntas sobre o próprio chat com base em um catálogo atualizado de funcionalidades.

### Responsabilidades

- Explicar recursos disponíveis.
- Ensinar comandos e exemplos.
- Guiar usuários por fluxos.
- Informar limites e permissões.
- Mostrar novidades.
- Adaptar ajuda ao agente ativo.
- Adaptar ajuda ao perfil do usuário.
- Mostrar botões clicáveis.
- Evitar inventar funcionalidades não implementadas.

---

## 5. Catálogo único de funcionalidades

Hoje o conhecimento está espalhado em:

- `capabilities.json`;
- `identity.json`;
- `chatHomeStarters.ts`;
- metadados dos agentes;
- actions OpenAPI;
- skills;
- componentes do front;
- documentação;
- código.

A melhoria principal é criar um **catálogo único de funcionalidades**, usado pelo backend e pelo frontend.

Arquivo sugerido:

`app/content/pt-BR/assistant/features_catalog.json`

### Estrutura sugerida

```json
{
  "version": "2026.06.01",
  "updatedAt": "2026-06-01T10:00:00Z",
  "features": [
    {
      "id": "product_lookup",
      "title": "Consulta de produto",
      "category": "operational",
      "status": "available",
      "summary": "Consulta cadastro, descrição e dados principais de produtos.",
      "requiresAgent": true,
      "requiredActions": ["GET /products/{code}"],
      "examples": [
        "Me fale do produto 10080001",
        "Mostre a ficha do produto 10080001"
      ],
      "howToUse": [
        "Escolha um agente com consultas de produto.",
        "Informe o código do produto.",
        "Peça o formato desejado, se quiser."
      ],
      "relatedFeatures": ["stock_lookup", "suppliers_lookup", "structure_lookup"],
      "limitations": [
        "Não inventa produto inexistente.",
        "Se faltar código, pergunta ao usuário."
      ]
    }
  ]
}
```

---

## 6. Categorias do catálogo

### Chat básico

- Cumprimentos.
- Perguntas de identidade.
- Ajuda.
- Data/hora.
- Continuação de conversa.

### Tarefas administrativas

- Corrigir texto.
- Reescrever.
- Traduzir.
- Resumir.
- Criar e-mail.
- Criar ata.
- Criar comunicado.
- Criar checklist.

### Consultas operacionais

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
- Movimentações.
- NF entrada.
- NF saída.
- OV/LMP.
- KPIs.
- SQL.

### Visualizações

- Texto.
- Tabela.
- Gráfico.
- KPI.
- Árvore.
- Cards.
- Lousa/canvas.
- CSV.
- PNG.
- Markdown.

### Interatividade

- Botões.
- Chips.
- Próximos passos.
- Drill-down.
- Feedback.
- Editar e reenviar.
- Continuar de uma mensagem.
- Copiar.
- Exportar.

### Fontes e conhecimento

- RAG.
- Documentos internos.
- Anexos.
- Pesquisa web.
- Fontes por projeto.
- Fontes por agente.

### Segurança

- Permissões.
- Limites.
- Confirmação de actions.
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
- O que tem de novo?
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

```md
Você pode usar o chat de três formas principais:

1. Perguntar livremente
   Ex.: “O que você pode fazer?”

2. Consultar dados com um agente
   Ex.: “Estoque do produto 10080001”

3. Trabalhar com textos e arquivos
   Ex.: “Corrija este texto” ou “Resuma esse PDF”

Escolha uma opção para começar:
```

Chips sugeridos:

- Consultar produto.
- Corrigir texto.
- Anexar arquivo.
- Ver gráficos.
- Usar lousa.
- Escolher agente.
- Ver tudo.

---

## 9. Resposta ideal para “o que você pode fazer?”

A resposta não deve ser só texto longo. Deve ser organizada por cards.

### Operacional

- Produto.
- Estoque.
- Fornecedores.
- Vendas.
- Compras.
- OV/LMP.

### Textos

- Corrigir.
- Traduzir.
- Resumir.
- Escrever e-mail.
- Criar ata.

### Visualizações

- Tabelas.
- Gráficos.
- KPIs.
- Árvores.
- Lousa.

### Fontes

- Anexos.
- Documentos.
- Pesquisa web.
- Projetos.

### Ajuda

- Como usar.
- Exemplos.
- Limites.
- Agentes.

---

## 10. Ajuda contextual por agente

A resposta deve mudar conforme o agente ativo.

### Chat comum

> Posso ajudar com textos, anexos, dúvidas gerais, documentação e escolha de agente.

### Agente Produtos

> Neste agente, posso consultar produto, estoque, fornecedores, estrutura, compras, vendas e visão 360°.

### Agente Administrativo

> Neste agente, posso corrigir textos, escrever e-mails, traduzir, resumir e criar documentos.

### Agente Compras

> Neste agente, posso ajudar com fornecedores, compras, preços, lead time e notas de entrada.

---

## 11. Ajuda contextual por situação

### Tela inicial

Mostrar:

- o que pode fazer;
- exemplos;
- categorias;
- busca de funcionalidade.

### Depois de uma resposta operacional

Mostrar:

- Ver estoque.
- Ver fornecedores.
- Transformar em gráfico.
- Colocar na lousa.

### Depois de uma resposta textual

Mostrar:

- Mais formal.
- Mais curto.
- Traduzir.
- Colocar na lousa.

### Depois de erro

Mostrar:

- Tentar novamente.
- Ampliar filtro.
- Verificar código.
- Escolher agente.
- Entender o erro.

---

## 12. Catálogo de exemplos

### Produto

- Me fale do produto 10080001.
- Visão 360° do produto 10080001.
- Busque produtos com descrição cabo.

### Estoque

- Qual o estoque do produto 10080001?
- Mostre saldo por armazém.
- Produtos sem estoque.

### Texto

- Corrija este texto.
- Traduza para inglês.
- Escreva um e-mail profissional.
- Resuma em tópicos.

### Arquivo

- Resuma esse PDF.
- Extraia pendências desse arquivo.
- Transforme esse documento em ata.

### Gráfico

- Mostre vendas por mês em linha.
- Faça gráfico de pizza por cliente.
- Mostre ranking em barra horizontal.

### Web

- Pesquise na web sobre o manual do CFW500.
- Busque fontes oficiais.
- Compare informações encontradas.

---

## 13. Guia de formatos

Pergunta:

> Que formatos você consegue mostrar?

Resposta sugerida:

```md
Posso responder em:

- Texto: explicações e resumos.
- Tabela: listas, comparações e resultados operacionais.
- Gráfico: dados numéricos e temporais.
- KPI: indicadores e metas.
- Árvore: estruturas/BOM.
- Lousa: rascunhos, atas, relatórios e checklists.
- Arquivo: quando houver exportação disponível.
```

---

## 14. Guia de agentes

O chat deve ensinar:

- o que é agente;
- quando escolher;
- como trocar;
- o que muda;
- quais tools/actions o agente tem;
- exemplos de uso.

Resposta sugerida:

```md
Agentes são versões especializadas do chat.

Use um agente quando precisar de uma área específica, como produtos, compras, vendas, produção, qualidade ou textos.

Cada agente pode ter:
- conhecimento próprio;
- actions/API;
- exemplos;
- permissões específicas.
```

---

## 15. Guia de permissões

Resposta sugerida:

```md
Algumas consultas dependem do seu perfil e do agente ativo.

Se eu não conseguir acessar algo, posso explicar o motivo e sugerir:
- escolher outro agente;
- pedir acesso;
- consultar outra fonte;
- reformular a pergunta.
```

---

## 16. Ajuda para “perguntar melhor”

Pergunta:

> Como faço uma boa pergunta?

Resposta sugerida:

```md
Uma boa pergunta geralmente tem:

1. O que você quer
   Ex.: estoque, fornecedor, vendas, correção de texto.

2. O identificador
   Ex.: código do produto, OV, cliente ou período.

3. O formato desejado
   Ex.: tabela, gráfico, resumo ou checklist.

Exemplo:
“Mostre o estoque do produto 10080001 em tabela.”
```

---

## 17. Atualização contínua de funcionalidades

Este é o ponto mais importante.

O chat deve ser atualizado sempre que:

- nova action for criada;
- action for removida;
- rota mudar;
- skill nova for adicionada;
- componente novo de UI for criado;
- novo gráfico for suportado;
- nova funcionalidade de anexo for liberada;
- novo agente for publicado;
- permissão mudar;
- comportamento de resposta mudar.

---

## 18. Fonte única de verdade

Criar um registro consolidado:

`AssistantCapabilitiesRegistry`

Ele deve consolidar:

1. Actions/OpenAPI publicadas.
2. Skills ativas.
3. Arquivos `content/pt-BR/assistant`.
4. Metadados dos agentes.
5. Componentes de UI disponíveis.
6. Feature flags.
7. Documentação de release.
8. Permissões do usuário.

---

## 19. Geração automática do catálogo

Criar job:

`generate_assistant_capabilities_catalog`

Ele deve:

1. Ler actions registradas.
2. Ler skills disponíveis.
3. Ler agentes publicados.
4. Ler feature flags.
5. Ler arquivos de conteúdo.
6. Montar JSON consolidado.
7. Validar exemplos.
8. Atualizar `features_catalog.json`.
9. Rodar testes.
10. Publicar versão.

---

## 20. Catálogo por usuário

O chat não deve mostrar funcionalidades indisponíveis para o usuário como se estivessem liberadas.

A resposta deve diferenciar:

```json
{
  "availableNow": [],
  "requiresAgent": [],
  "requiresPermission": [],
  "comingSoon": [],
  "disabled": []
}
```

Exemplo:

> Você pode corrigir textos e anexar arquivos agora. Para consultar estoque, escolha um agente com action de estoque habilitada.

---

## 21. Versionamento

Cada funcionalidade deve ter:

- ID.
- Nome.
- Status.
- Versão.
- Data de atualização.
- Responsável.
- Exemplos.
- Dependências.
- Permissões.
- Links internos.
- Changelog.

Exemplo:

```json
{
  "id": "web_search",
  "title": "Pesquisa na web",
  "status": "available",
  "version": "1.2.0",
  "updatedAt": "2026-06-01",
  "changelog": [
    "Adicionado modo pesquisa profunda",
    "Adicionados cards de fontes"
  ]
}
```

---

## 22. Resposta “o que mudou?”

Usuário:

> O que mudou na última versão?

Resposta sugerida:

```md
Estas foram as principais novidades:

- Pesquisa web agora mostra fontes e etapas.
- Gráficos agora suportam linha e rosca.
- O chat agora ajuda com correção de textos.
- A lousa pode transformar respostas em checklist.

Quer ver exemplos?
```

Chips:

- Ver exemplos.
- Ver novidades por área.
- Como usar.
- Abrir changelog.

---

## 23. Integração com release notes

Criar arquivo:

`assistant_release_notes.json`

Exemplo:

```json
{
  "releases": [
    {
      "version": "2026.06.01",
      "date": "2026-06-01",
      "items": [
        {
          "featureId": "chart_donut",
          "title": "Gráfico de rosca",
          "description": "Agora o chat pode mostrar participação em formato de rosca.",
          "examples": [
            "Mostre participação de vendas por cliente em rosca"
          ]
        }
      ]
    }
  ]
}
```

---

## 24. Testes obrigatórios após nova funcionalidade

Sempre que uma funcionalidade for criada ou alterada:

1. Atualizar catálogo.
2. Atualizar exemplos.
3. Atualizar starters/chips, se fizer sentido.
4. Atualizar ajuda.
5. Atualizar testes.
6. Validar resposta “o que você pode fazer?”.
7. Validar resposta “como uso X?”.
8. Validar permissões.
9. Validar agente.
10. Atualizar release notes.

---

## 25. Testes de autoajuda

Criar:

`test_chat_self_help.py`

### H1 — Ajuda geral

Input:

> o que você pode fazer?

Esperado:

- lista funcionalidades;
- personaliza por agente;
- não inventa recurso.

### H2 — Como usar estoque

Input:

> como consulto estoque?

Esperado:

- pede agente/código;
- dá exemplo.

### H3 — Como usar gráfico

Input:

> como faço gráfico?

Esperado:

- explica dados necessários;
- dá exemplos.

### H4 — Funcionalidade indisponível

Input:

> você consegue excluir produto?

Esperado:

- diz que não;
- explica limite.

### H5 — Novidade

Input:

> o que mudou?

Esperado:

- usa release notes.

### H6 — Ajuda contextual

Com agente ativo:

> o que você consegue consultar?

Esperado:

- lista capacidades do agente.

### H7 — Textos

Input:

> você corrige textos?

Esperado:

- responde sim;
- dá exemplos.

### H8 — Pesquisa web

Input:

> como uso pesquisa web?

Esperado:

- explica quando usar;
- dá exemplo.

### H9 — Lousa

Input:

> como uso a lousa?

Esperado:

- explica comandos.

### H10 — Permissões

Input:

> por que não consigo consultar estoque?

Esperado:

- explica agente/permissão.

---

## 26. UI de autoajuda

Criar uma página ou painel:

**Ajuda do chat**

Com:

- busca de funcionalidades;
- categorias;
- exemplos;
- novidades;
- agentes;
- formatos;
- limites;
- tutoriais rápidos.

### Cards

- Consultas operacionais.
- Textos.
- Arquivos.
- Gráficos.
- Lousa.
- Pesquisa web.
- Agentes.
- Permissões.

---

## 27. Busca dentro da ajuda

Usuário digita:

> estoque

A ajuda mostra:

- Consultar estoque.
- Exemplos.
- Agente necessário.
- Dados necessários.
- Próximos passos.

Usuário digita:

> traduzir

Mostra:

- Tradução.
- Idiomas.
- Exemplos.
- Botão para começar.

---

## 28. Botão “?”

Adicionar no chat:

- Como usar.
- O que posso fazer?
- Exemplos.
- Atalhos.
- Novidades.
- Limites.
- Falar com suporte.

---

## 29. Ajuda em contexto

O chat deve mostrar ajuda no momento certo.

### Usuário parado

> Precisa de ideias? Você pode consultar produto, corrigir texto ou anexar arquivo.

### Após erro

> Quer que eu explique como essa consulta funciona?

### Primeiro uso de funcionalidade

> Dica: você pode pedir “em tabela” ou “em gráfico”.

---

## 30. Guias rápidos

### Consultar produto

1. Escolha agente adequado.
2. Informe código do produto.
3. Peça o formato.

Exemplo:

> Me fale do produto 10080001 em tabela.

### Corrigir texto

1. Cole o texto.
2. Peça correção ou tom.
3. Use chips para ajustar.

Exemplo:

> Corrija este texto mantendo o sentido original.

### Anexar arquivo

1. Clique em `+`.
2. Anexe o arquivo.
3. Peça resumo, tradução ou extração de pendências.

### Usar lousa

1. Gere uma resposta.
2. Peça “coloque isso na lousa”.
3. Edite, revise ou exporte.

### Pesquisa web

1. Peça “pesquise na web sobre...”.
2. Informe se quer fonte oficial.
3. Peça resumo, comparação ou relatório.

---

## 31. Não inventar funcionalidades

Se o usuário pergunta sobre algo não implementado:

```md
Ainda não tenho essa funcionalidade disponível nesta sessão.

Posso ajudar de formas próximas:
- ...
```

Exemplo:

> Você consegue enviar e-mail sozinho?

Resposta:

> Posso redigir o e-mail, mas não envio automaticamente nesta sessão.

---

## 32. Integração com permissões

A ajuda deve diferenciar:

- existe na plataforma;
- existe, mas não está habilitado neste agente;
- existe, mas seu perfil não tem permissão;
- está em desenvolvimento;
- foi removido.

Exemplo:

```md
A consulta de estoque existe na plataforma, mas precisa de um agente com a action de estoque habilitada.
```

---

## 33. Governança

### Responsáveis

Cada funcionalidade deve ter dono:

- Produto.
- Engenharia.
- Compras.
- Comercial.
- Plataforma.
- IA.
- Segurança.

### Processo de mudança

Ao alterar funcionalidade:

1. Atualizar código.
2. Atualizar catálogo.
3. Atualizar exemplos.
4. Atualizar ajuda.
5. Atualizar release notes.
6. Rodar testes.
7. Publicar.

---

## 34. Observabilidade

Registrar eventos:

```json
{
  "event": "self_help_requested",
  "topic": "stock_lookup",
  "agent": "minha-delpi",
  "resolved": true,
  "suggestionClicked": "Ver estoque"
}
```

Métricas:

- tópicos de ajuda mais buscados;
- perguntas não respondidas;
- funcionalidades confusas;
- cliques em exemplos;
- uso após ajuda;
- dúvidas por agente;
- dúvidas após erro.

---

## 35. Feedback de ajuda

Após resposta de ajuda, perguntar discretamente:

> Isso ajudou?

Motivos se negativo:

- Não encontrei o que queria.
- Explicação confusa.
- Exemplo não funcionou.
- Funcionalidade indisponível.
- Faltou passo a passo.

---

## 36. Métricas de sucesso

- Redução de dúvidas repetidas.
- Aumento de uso de starters.
- Aumento de consultas bem-sucedidas.
- Redução de erros por falta de parâmetro.
- Redução de feedback “não respondeu”.
- Cliques em exemplos.
- Uso de funcionalidades novas.
- Taxa de conclusão após ajuda.
- Tempo até primeira ação útil.

---

## 37. Roadmap

### Fase 1 — Organizar ajuda atual

- [x] `featureAnswers` — web, lousa, gráfico, anexo, agente (`ChatCapabilitiesService`).
- [x] `ChatHelpFollowUpService` → `helpFollowUpSuggestions` no metadata.
- [x] Starters no MFE (`chatHomeStarters.ts`) — como usar, pesquisa web, lousa.
- [x] Chips «Explorar» no `ChatMessageList`.
- [ ] Revisão completa de `identity.json` alinhada ao catálogo.
- [x] Matriz de testes H1–H10 — `test_chat_self_help.py` + `chat_self_help_cases.py`.

### Fase 2 — Catálogo único

- [x] `features_catalog.json` — funcionalidades com id, categoria, exemplos e `helpTopicId`.
- [x] `AssistantCapabilitiesRegistry` — busca, disponibilidade por agente, release notes.
- [x] `assistant_release_notes.json` + resposta «o que mudou?».
- [x] Integração com `ChatCapabilitiesService` e chips Explorar via features relacionadas.
- [x] Geração automática a partir de actions/skills (Fase 3).

### Fase 3 — Autoatualização

- [x] `AssistantCapabilitiesCatalogValidator` + `scripts/check_assistant_capabilities_catalog.py` (CI/local).
- [x] Guias adicionais: estoque, textos, permissões, ações destrutivas (`featureAnswers`).
- [x] Job `scripts/generate_assistant_capabilities_catalog.py` (`--check`, `--write`) + `AssistantCapabilitiesCatalogGenerator`.
- [x] `check_assistant_capabilities_catalog.py` valida JSON e sincronização com actions/skills.
- [x] `scripts/check_help_pr_gate.py` — bloqueia PR com mudança em actions/skills sem ajuda/catálogo.

### Fase 4 — UI de ajuda

- [x] `GET /chat/assistant/catalog` — busca, categorias, disponibilidade e atalhos.
- [x] Painel lateral `ChatHelpPanel` no MFE (busca, cards, exemplos clicáveis).
- [x] Botão `?` na topbar (`ChatContextTopbar`).

### Fase 5 — Ajuda inteligente

- [x] Personalizar por usuário — `userContext`, `requiresProfilePermission`, filtro de cards sem permissão de tools/perfil.
- [x] Personalizar por agente no painel (`agentId` / `agentName` no catálogo) e chips pós-erro com nome do agente.
- [x] `ChatHelpErrorFollowUpService` → `helpErrorFollowUpSuggestions` (chips «Ajuda após erro» no MFE).
- [x] Novidades contextuais — `contextualHighlights` no catálogo, home vazia e painel `?`.
- [x] Métricas leves — `POST /chat/assistant/help-events` (`help_panel_open`, etc.) + log estruturado.

---

## 38. Checklist para novas funcionalidades

Toda nova funcionalidade deve preencher:

```md
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
```

---

## 39. Anti-padrões

Evitar:

1. O chat dizer que faz algo que não está implementado.
2. Ajuda genérica demais.
3. Ajuda desatualizada.
4. Exemplo que não funciona.
5. Mostrar funcionalidade sem permissão.
6. Misturar capacidades do chat comum com agente sem explicar.
7. Não atualizar ajuda após release.
8. Não ensinar o próximo passo.
9. Responder “veja a documentação” sem orientar.
10. Não ter teste para “o que você pode fazer?”.

---

## 40. Exemplo final de resposta ideal

Usuário:

> Como faço para gerar gráfico?

Resposta:

```md
Você pode pedir gráfico quando houver dados numéricos.

Exemplos:
- “Mostre vendas por mês em gráfico de linha”
- “Faça gráfico de pizza por cliente”
- “Mostre top 10 produtos em barra horizontal”

Se a consulta retornar uma tabela com números, também posso transformar a tabela em gráfico.
```

Chips:

- Vendas por mês.
- Gráfico de pizza.
- Ranking horizontal.
- Transformar tabela anterior.
- Ver formatos.

---

## 41. Resumo executivo

O Minha DELPI Chat IA deve ser seu próprio manual vivo.

Para isso, é necessário criar um catálogo único e atualizado de funcionalidades, integrar esse catálogo com agentes, actions, skills, permissões, starters e release notes, e criar respostas de ajuda contextual.

A regra principal é:

> Toda funcionalidade nova precisa atualizar o código, o catálogo, os exemplos, os testes e a ajuda do chat.

Com isso, o usuário aprende dentro do próprio chat, sem depender de treinamento externo, e a plataforma mantém a autoexplicação sempre alinhada com sua evolução.
