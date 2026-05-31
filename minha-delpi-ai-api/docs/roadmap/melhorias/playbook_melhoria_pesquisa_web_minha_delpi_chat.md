# Playbook — Melhoria da funcionalidade de pesquisa na web

Projeto: **Minha DELPI Chat IA**

Objetivo: evoluir a funcionalidade de pesquisa na web para que o chat consiga pesquisar melhor, explicar melhor de onde veio a informação, comparar fontes, lidar com notícias recentes, resumir páginas, validar confiabilidade e integrar resultados externos com o contexto interno da DELPI.

> **Status (31/05/2026):** [Concluído](./STATUS_ROADMAP_MELHORIAS.md) — **Fases 1–5** no chat base e MFE, incluindo salvar fontes no projeto.

---

## 1. Diagnóstico do estado atual

O projeto já possui sinais de suporte à pesquisa web.

No contrato do frontend existe o tipo `ChatWebSearchResearch`, com campos como:

- `sourceCount`;
- `durationMs`;
- `provider`;
- `query`;
- `attemptedQueries`;
- `searchStatus`;
- `synthesized`;
- `steps`;
- `sites`.

Também existe `ChatWebSearchResearchStep`, com etapas de pesquisa como:

- `search`;
- `synthesis`;
- `organize`;
- mensagem da etapa;
- query executada;
- estado da etapa;
- sites encontrados.

Além disso, `ChatMessageMetadata` já aceita `webSearchResearch`, e `ChatMessageList` já possui lógica para obter `message.metadata?.webSearchResearch`.

Isso mostra que a plataforma já foi desenhada para guardar e exibir rastros de pesquisa web. A melhoria principal é transformar essa base em uma experiência mais rica, confiável e interativa.

---

# 2. Objetivo da pesquisa web no chat

A pesquisa web deve servir para responder perguntas que dependem de informação externa, pública ou recente.

Exemplos:

- “Pesquise sobre uma norma técnica.”
- “Veja notícias recentes sobre determinado fornecedor.”
- “Busque informações públicas de uma empresa.”
- “Compare especificações de um produto no site do fabricante.”
- “Pesquise tendências do mercado elétrico.”
- “Procure referências para um procedimento.”
- “Valide se essa informação ainda está atual.”
- “Busque equivalentes de componentes.”
- “Ache documentação pública de um conector.”
- “Pesquise datasheet de um item.”

---

# 3. Princípio central

> Pesquisa web deve ser usada quando a resposta precisa de informação atual, externa ou verificável fora da base interna.

Não usar web para tudo.

A web deve complementar:

- RAG interno;
- dados operacionais;
- anexos;
- contexto da conversa;
- conhecimento geral do modelo.

---

# 4. Quando usar pesquisa web

## Usar web quando

- o usuário pedir explicitamente “pesquise”, “busque na web”, “veja na internet”;
- a informação pode ter mudado recentemente;
- envolve notícia, preço, norma, legislação, fornecedor, mercado ou produto atual;
- precisa validar fonte pública;
- precisa comparar dados de sites;
- precisa encontrar datasheet público;
- precisa consultar documentação externa;
- precisa obter referência pública.

## Não usar web quando

- o usuário pedir correção de texto;
- a pergunta for sobre dados internos DELPI;
- a resposta está em documento interno autorizado;
- a pergunta for small talk;
- a pergunta for data/hora;
- a pergunta envolver estoque, vendas, compras ou ERP;
- o usuário pedir “não pesquise”;
- houver fonte interna mais confiável e suficiente.

---

# 5. Tipos de pesquisa web

## 5.1 Pesquisa factual

Objetivo: encontrar uma resposta objetiva.

Exemplos:

- “Qual é o site oficial da WEG?”
- “O que significa IP67?”
- “Qual a norma de cores para cabos?”

## 5.2 Pesquisa recente

Objetivo: encontrar atualizações.

Exemplos:

- “Notícias recentes sobre WEG.”
- “Mudanças recentes em norma NR-10.”
- “Atualização de preço de cobre.”

## 5.3 Pesquisa técnica

Objetivo: encontrar documentação, datasheet ou especificação.

Exemplos:

- “Datasheet do terminal X.”
- “Manual técnico de inversor WEG.”
- “Tabela de corrente para cabo.”

## 5.4 Pesquisa comparativa

Objetivo: comparar opções ou fontes.

Exemplos:

- “Compare fornecedores.”
- “Compare dois componentes.”
- “Compare motores WEG e Siemens.”

## 5.5 Pesquisa de validação

Objetivo: verificar se uma informação é verdadeira.

Exemplos:

- “Confirme se essa norma ainda está válida.”
- “Verifique se esse produto foi descontinuado.”
- “Esse fornecedor ainda existe?”

## 5.6 Pesquisa para redação

Objetivo: coletar contexto para texto.

Exemplos:

- “Pesquise e monte um resumo.”
- “Busque referências para um comunicado.”
- “Pesquise e gere uma explicação simples.”

---

# 6. Pipeline recomendado

Criar ou evoluir o pipeline:

```text
Mensagem do usuário
  → classificação de intenção
  → decisão: precisa web?
  → planejamento de busca
  → execução de uma ou mais queries
  → leitura/seleção de fontes
  → avaliação de confiabilidade
  → síntese
  → resposta com fontes
  → sugestões de próximos passos
```

---

# 7. Serviço recomendado

Criar:

`ChatWebSearchResearchService`

Responsabilidades:

- decidir se deve pesquisar;
- montar queries;
- executar busca;
- registrar tentativas;
- coletar sites;
- avaliar fonte;
- sintetizar achados;
- retornar metadados;
- gerar resposta com citações;
- gerar sugestões.

---

# 8. Modelo de metadata recomendado

A estrutura atual já permite algo como:

```json
{
  "webSearchResearch": {
    "sourceCount": 4,
    "durationMs": 3200,
    "provider": "web",
    "query": "WEG inversor CFW500 manual",
    "attemptedQueries": [
      "WEG CFW500 manual oficial",
      "site:weg.net CFW500 manual pdf"
    ],
    "searchStatus": "success",
    "synthesized": true,
    "steps": [
      {
        "id": "1",
        "type": "search",
        "message": "Buscando fontes oficiais...",
        "query": "WEG CFW500 manual oficial",
        "state": "done"
      },
      {
        "id": "2",
        "type": "synthesis",
        "message": "Organizando os resultados encontrados...",
        "state": "done"
      }
    ],
    "sites": [
      {
        "hostname": "weg.net",
        "url": "https://...",
        "title": "Manual CFW500"
      }
    ]
  }
}
```

## Evolução sugerida

Adicionar:

```json
{
  "confidence": "high",
  "freshness": "recent",
  "sourceTypes": ["official", "pdf", "documentation"],
  "warnings": [],
  "excludedSources": [
    {
      "hostname": "site-exemplo.com",
      "reason": "fonte não oficial ou duplicada"
    }
  ]
}
```

---

# 9. Planejamento de busca

Antes de pesquisar, o sistema deve definir:

- qual é a pergunta real;
- quais termos usar;
- se precisa fonte oficial;
- se precisa notícia recente;
- se precisa PDF/datasheet;
- se precisa comparar fontes;
- idioma da busca;
- domínio preferencial;
- número máximo de resultados.

## Exemplo

Usuário:

> Pesquise datasheet do motor WEG W22.

Plano:

```json
{
  "intent": "technical_document_search",
  "preferredDomains": ["weg.net"],
  "queries": [
    "WEG W22 datasheet PDF",
    "site:weg.net W22 motor datasheet"
  ],
  "requiredSourceType": "official_or_pdf",
  "language": "pt-BR"
}
```

---

# 10. Estratégias de query

## Fonte oficial

Usar quando a confiabilidade importa.

Exemplos:

- `site:weg.net CFW500 manual`
- `site:gov.br NR-10`
- `site:abnt.org.br norma cabos`

## Datasheet

- `[produto] datasheet pdf`
- `[produto] manual técnico`
- `[fabricante] [modelo] specification`

## Notícias

- `[empresa] notícias recentes`
- `[tema] 2026`
- `[empresa] press release`

## Comparação

- `[produto A] vs [produto B]`
- `[categoria] melhores práticas`
- `[fabricante A] [fabricante B] comparação`

## Inglês técnico

Quando o termo em português não retorna bons resultados, tentar inglês:

- `terminal crimp datasheet`
- `heat shrink tubing specifications`
- `electrical connector catalog`

---

# 11. Avaliação de fontes

## Prioridade de fontes

1. Site oficial do fabricante.
2. Órgão público ou regulador.
3. Norma/documentação oficial.
4. Distribuidor reconhecido.
5. Artigos técnicos confiáveis.
6. Notícias de veículos reconhecidos.
7. Blogs e fóruns, apenas como apoio.
8. Sites desconhecidos, evitar.

## Classificação sugerida

```json
{
  "sourceQuality": {
    "official": 1.0,
    "government": 0.95,
    "manufacturer": 0.95,
    "recognized_distributor": 0.8,
    "technical_article": 0.7,
    "news": 0.65,
    "forum": 0.4,
    "unknown": 0.2
  }
}
```

---

# 12. Resposta com pesquisa web

Formato recomendado:

```md
Pesquisei fontes externas e encontrei o seguinte:

## Resumo
...

## Principais achados
- ...
- ...

## Fontes consultadas
- Fonte 1
- Fonte 2

## Observação
[limitações, data, fonte não oficial, etc.]
```

---

# 13. Transparência

Sempre informar:

- se pesquisou na web;
- quantas fontes usou;
- se a fonte é oficial;
- se os dados podem estar desatualizados;
- se não encontrou fonte confiável;
- se usou fonte alternativa.

## Exemplo

> Encontrei principalmente fontes de distribuidores, mas não encontrei uma página oficial do fabricante confirmando essa informação.

---

# 14. Quando a busca falhar

Resposta recomendada:

```md
Não encontrei uma fonte confiável suficiente para responder com segurança.

Posso tentar:
- buscar em inglês;
- restringir a sites oficiais;
- pesquisar por modelo/código;
- usar um arquivo anexado;
- procurar em outro fabricante.
```

Chips:

- Buscar em inglês.
- Só fontes oficiais.
- Tentar por modelo.
- Ampliar busca.
- Usar anexo.

---

# 15. Pesquisa web + dados internos

Algumas respostas precisam cruzar fonte externa com dados internos.

## Exemplo

Usuário:

> Consulte nosso produto 10080001 e pesquise se há datasheet público equivalente.

Fluxo:

1. Consultar produto interno.
2. Extrair descrição, fabricante, modelo se houver.
3. Pesquisar na web.
4. Comparar.
5. Informar incertezas.

## Regra

Nunca substituir dado interno por dado web sem avisar.

---

# 16. Pesquisa web + anexos

Exemplo:

> Compare esse datasheet anexado com informações do site oficial.

Fluxo:

1. Ler anexo.
2. Pesquisar site oficial.
3. Comparar especificações.
4. Destacar divergências.
5. Informar fonte.

---

# 17. Pesquisa web + textos administrativos

Exemplo:

> Pesquise sobre esse tema e escreva um comunicado.

Fluxo:

1. Pesquisar.
2. Resumir fontes.
3. Gerar rascunho.
4. Indicar que é rascunho.
5. Sugerir revisão.

---

# 18. UI recomendada

## Painel de pesquisa

Mostrar:

- status da pesquisa;
- queries tentadas;
- sites encontrados;
- fontes usadas;
- fontes descartadas;
- tempo de pesquisa.

## Activity log

Etapas:

- Planejando busca.
- Pesquisando fontes.
- Lendo resultados.
- Avaliando confiabilidade.
- Sintetizando resposta.

## Cards de fontes

Cada fonte pode mostrar:

- título;
- domínio;
- tipo de fonte;
- selo de confiança;
- data, se disponível;
- botão abrir.

---

# 19. Botões pós-pesquisa

Após resposta com web:

- Abrir fontes.
- Buscar só em fontes oficiais.
- Buscar em inglês.
- Comparar fontes.
- Gerar resumo executivo.
- Criar comunicado.
- Colocar na lousa.
- Salvar fontes.
- Atualizar pesquisa.
- Pesquisar mais.

---

# 20. Pesquisa com modo rápido e modo profundo

## Modo rápido

- 1 a 3 fontes.
- Resposta curta.
- Ideal para perguntas simples.

## Modo profundo

- múltiplas queries;
- comparação de fontes;
- classificação de confiabilidade;
- síntese estruturada;
- mais tempo.

Usuário pode pedir:

- “pesquisa rápida”
- “pesquisa profunda”
- “valide com fontes oficiais”
- “faça uma investigação completa”

---

# 21. Recência

Para temas temporais, o sistema deve considerar data.

## Perguntas temporais

- notícias recentes;
- preço;
- legislação;
- norma;
- versão de produto;
- disponibilidade;
- fornecedor ativo;
- lançamento.

## Resposta

Informar:

> A pesquisa considera resultados encontrados agora, mas a disponibilidade pode mudar. Recomendo validar no site oficial antes de decisão crítica.

---

# 22. Citações e fontes

A resposta deve evitar “segundo a internet”.

Usar:

- “No site oficial...”
- “Em documentação do fabricante...”
- “Em fontes públicas consultadas...”
- “Não encontrei fonte oficial...”

## Regra

Para afirmações importantes, citar fonte.

---

# 23. Segurança

A pesquisa web não deve:

- acessar sites inseguros sem necessidade;
- baixar arquivos automaticamente sem validação;
- usar fonte desconhecida como verdade;
- expor dados internos na query;
- pesquisar informações confidenciais da DELPI;
- enviar códigos internos sensíveis para buscadores;
- misturar dado interno com web sem aviso.

## Regra crítica

Não enviar para web:

- dados confidenciais;
- nomes de clientes sensíveis;
- preços internos;
- pedidos internos;
- documentos privados;
- código de produto se ele revelar informação estratégica, sem avaliação.

---

# 24. Redação segura de queries

Se a pergunta envolve dado interno, sanitizar.

Usuário:

> Pesquise na web sobre o cliente X e nosso preço interno.

Não pesquisar o preço interno.

Resposta:

> Posso pesquisar informações públicas sobre a empresa, mas não devo enviar preços internos para a web.

---

# 25. Integração com agentes

## Agente Engenharia

Usos:

- datasheets;
- normas;
- manuais;
- equivalentes;
- especificações técnicas.

## Agente Compras

Usos:

- fornecedores públicos;
- catálogos;
- disponibilidade pública;
- notícias de fornecedor;
- comparação de fabricantes.

## Agente Comercial

Usos:

- notícias de clientes;
- mercado;
- concorrentes públicos;
- tendências.

## Agente Administrativo

Usos:

- pesquisa para textos;
- comunicados;
- resumo de notícias;
- tradução com contexto.

---

# 26. Templates de resposta

## Pesquisa técnica

```md
## Resumo técnico

...

## Especificações encontradas

| Campo | Valor | Fonte |
|---|---:|---|

## Pontos de atenção

...

## Fontes

...
```

## Pesquisa de notícia

```md
## Resumo das notícias

...

## Linha do tempo

...

## Impacto possível

...

## Fontes

...
```

## Pesquisa comparativa

```md
## Comparação

| Critério | Opção A | Opção B |
|---|---|---|

## Conclusão

...

## Fontes

...
```

---

# 27. Testes

## Testes mínimos

- Pergunta com “pesquise na web”.
- Pergunta sem necessidade de web.
- Pedido de fonte oficial.
- Datasheet técnico.
- Notícia recente.
- Comparação de fontes.
- Busca falha.
- Busca em inglês.
- Web + anexo.
- Web + dado interno.
- Sanitização de query.
- Fonte oficial versus blog.
- Resultado sem fonte confiável.

---

# 28. Métricas

- número de pesquisas web;
- tempo médio;
- fontes por resposta;
- taxa de busca sem resultado;
- taxa de fonte oficial;
- taxa de feedback positivo;
- feedback “fonte ruim”;
- feedback “desatualizado”;
- pesquisas por agente;
- queries mais comuns;
- domínios mais usados;
- buscas canceladas.

---

# 29. Feedback específico

Adicionar motivos:

- Fonte não confiável.
- Fonte desatualizada.
- Faltou fonte oficial.
- Não respondeu à pesquisa.
- Pesquisa superficial.
- Precisava pesquisar e não pesquisou.
- Pesquisou sem necessidade.
- Misturou dado interno com web.
- Resultado muito longo.
- Faltou comparação.

---

# 30. Admin debug

Registrar:

```json
{
  "webSearch": {
    "enabled": true,
    "reason": "user_requested_web_search",
    "queries": [],
    "provider": "web",
    "sourceCount": 5,
    "usedSources": [],
    "discardedSources": [],
    "durationMs": 3200,
    "confidence": "medium",
    "warnings": []
  }
}
```

---

# 31. Playbook de decisão

## Usuário pede “pesquise”

Pesquisar.

## Informação recente

Pesquisar, mesmo que usuário não diga “pesquise”, se necessário.

## Dado interno

Não pesquisar; usar action/RAG interno.

## Texto puro

Não pesquisar, a menos que peça contexto externo.

## Fonte interna suficiente

Não pesquisar, a menos que peça validação externa.

## Baixa confiança

Pesquisar ou dizer limitação.

---

# 32. Roadmap

## Fase 1 — Transparência

- Exibir queries tentadas.
- Exibir fontes consultadas.
- Exibir status da pesquisa.
- Registrar `webSearchResearch`.

## Fase 2 — Planejamento de busca

- [x] `ChatWebSearchPlanningService` — modo `quick` / `deep`, `plannedQueries`, `site:weg.net` quando aplicável.
- [x] `WebSearchHttpGateway` prioriza queries planejadas antes do retry EN.
- [x] Metadata `searchMode`, `preferOfficial`, `searchIntent` em `webSearchResearch`.
- [ ] Classificação automática de domínios oficiais além da lista fixa de marcas.

## Fase 3 — Avaliação de fonte

- [x] `ChatWebSearchSourceEvaluationService` — classifica `sourceType`, `qualityScore`, `isOfficial`.
- [x] `enrich_payload` no `WebSearchTool` — reordena resultados; omite fontes fracas quando `preferOfficial`.
- [x] `sourceEvaluation` (`confidence`, `warnings`, `excludedSources`) em payload e `webSearchResearch`.
- [x] Resposta direta com bloco «Observação sobre as fontes» quando há avisos.
- [x] MFE `ChatWebSearchResearchPanel` — badge «oficial», confiança e lista de avisos.

## Fase 4 — Integração avançada

- [x] `ChatWebSearchIntegrationService` — modos `attachment_compare`, `internal_product`, `source_compare`, `technical_table`.
- [x] Queries extras no planejamento; `integrationMode` no payload e painel.
- [x] Híbrido produto interno não bloqueia actions DELPI no mesmo turno (`blocks_external_action_selection`).
- [x] Contexto de anexo repassado ao `ToolSelectionService` / `resolve` da web.
- [x] Síntese e resposta direta com notas de integração (não substituir dado interno).
- [x] `ChatWebSearchErpCrossReferenceService` — bloco «Cruzamento ERP × web» quando ERP + web no mesmo turno.

## Fase 5 — UX

- [x] Cards de fontes (`ChatSources` — grid com host, título, oficial/confiança).
- [x] Chips pós-pesquisa (`webSearchFollowUpSuggestions` via `ChatWebSearchFollowUpService` + playbook).
- [x] Painel de etapas (`ChatWebSearchResearchPanel` — Fase 1–3).
- [x] Atalho «Colocar na lousa» no chip pós-pesquisa (query com intent de canvas).
- [x] Salvar fontes no projeto (`ChatWebSearchSaveSourcesService` + chip «Salvar fontes»).

---

# 33. Anti-padrões

Evitar:

1. Pesquisar web para dados internos de ERP.
2. Responder com fonte desconhecida como se fosse verdade.
3. Não mostrar fontes.
4. Usar resultados antigos sem aviso.
5. Enviar dados confidenciais para buscador.
6. Confundir RAG interno com web.
7. Fazer busca superficial quando usuário pediu pesquisa profunda.
8. Responder “não encontrei” sem sugerir alternativa.
9. Misturar várias fontes sem explicar divergência.
10. Usar blog como fonte oficial.

---

# 34. Exemplo de resposta ideal

Usuário:

> Pesquise o manual do inversor WEG CFW500.

Resposta:

```md
Pesquisei fontes externas e priorizei fontes oficiais.

Encontrei referências ao manual do CFW500 no domínio da WEG.

## O que encontrei
- Manual técnico do CFW500.
- Materiais de suporte relacionados.
- Documentação em PDF.

## Próximos passos
Posso abrir a fonte, resumir o manual, extrair parâmetros principais ou comparar com outro modelo.
```

Chips:

- Abrir fontes.
- Resumir manual.
- Extrair parâmetros.
- Comparar com outro modelo.
- Colocar na lousa.

---

# 35. Resumo executivo

A funcionalidade de pesquisa web deve evoluir de uma busca simples para um fluxo de pesquisa confiável, transparente e auditável.

A base do projeto já prevê metadata para `webSearchResearch`, etapas, sites e status. A melhoria principal é implementar planejamento de busca, avaliação de fontes, resposta com fontes, botões pós-pesquisa e integração com dados internos, anexos e lousa.

A regra principal é:

> Web para informação externa e atual; RAG para conhecimento interno; actions para dados operacionais; LLM para síntese e escrita.
