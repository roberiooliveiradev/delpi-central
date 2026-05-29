# Smoke operacional — checklist manual

Checklist de perguntas para validar o chat operacional após deploy ou alterações no pipeline de inteligência.

**Dica:** para testes multi-turno, use a **mesma conversa** — o histórico importa.

Se algo falhar após deploy, reinicie a API:

```bash
docker compose -f infra/docker-compose.dev.yml restart minha-delpi-ai-api
```

---

## Smoke operacional (6/6)

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 1 | estoque do produto | Pede o código; não chama API de estoque/ROL |
| 2 | estouque do produto | Mesmo comportamento (corrige typo) |
| 3 | estoque do produto 10080022 | Consulta estoque; tabela/gráfico com dados |
| 4 | quem te criou? | Resposta canônica sobre Minha DELPI; rápida, sem RAG |
| 5 | olá | Saudação normal (pode usar LLM) |
| 6 | *(após #3)* filtre filial 02 | Refina estoque da filial 02 do produto anterior |
| 6b | *(após KPI estoque empresa)* filial 01 | Refina `/supplies/stock-value` na filial 01; **sem** SQL/agentic |

---

## E2E HTTP — estoque + drill-down

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 7 | estoque do produto 10080022 | Tabela com filiais/armazéns |
| 8 | *(mesma sessão)* filtre filial 02 | Só filial 02; não erro «API não retornou registros» |
| 9 | *(alternativa)* clique numa linha da tabela (tooltip «Clique para detalhar») | Envia algo como `filtre filial 02 armazém 01 do produto 10080022` |

---

## Multi-turn operacional (9 passos)

### Cenário A — estoque → filial → completo

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 10 | estoque do produto 10080047 | Estoque completo (todas filiais) |
| 11 | filtre filial 02 | Só filial 02 |
| 12 | completo de novo | Estoque completo de novo, sem filtro |
| 13 | estoque completo | Idem — remove filtro de filial |

### Cenário B — dois produtos + filial

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 14 | estoque dos produtos 10080047 e 10080055 | Dois estoques (dois produtos) |
| 15 | filtre filial 01 | Ambos filtrados na filial 01 |
| 16 | mostre completo | Remove filtro de filial nos dois |

### Cenário C — contexto sem repetir código

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 17 | resumo dos produtos 10080047 e 10080055 | Dois resumos |
| 18 | estoque do produto | Estoque do último produto citado (10080055) |

---

## Regressão de intenção (roteamento)

| # | Pergunta | Rota esperada |
|---|----------|---------------|
| 19 | descrição do produto 10080047 | Descrição do produto |
| 20 | busque o estoque desse produto | Estoque (após citar produto antes) |
| 21 | informações completas do produto 10080055 | Analyser/ficha completa |
| 22 | resumo do produto 10080047 | Summary (não analyser) |
| 23 | ficha completa do produto 10080047 | Analyser (não summary) |
| 24 | qual o valor total de estoque da empresa | KPI suprimentos (não produto individual) |
| 25 | faturamento do produto 10080047 | Faturamento do produto |
| 26 | detalhe da LMP da OV 123456 | LMP por OV |
| 27 | kpis do painel de LMPs | Dashboard LMP |
| 28 | pmr da filial 02 | PMR com filial 02 |
| 29 | colunas da tabela SB1 | Metadados da tabela SB1 |

---

## Comparação / insights (não deve disparar nova consulta operacional)

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 30 | compare as duas estruturas e traga insights | Análise comparativa, sem nova action de estrutura |
| 31 | estrutura do produto 90260088 | Consulta estrutura normalmente (não é comparação) |

---

## Datas automáticas (11.1.2)

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 32 | cpv de 01/04/2026 a 30/04/2026 | CPV com intervalo de datas |
| 33 | listar ov de 01/04/2026 a 30/04/2026 | OVs no período |

---

## Refinamento KPI / métricas (11.1.1)

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 34 | qual o cpv → filtre filial 02 | CPV refinado na filial 02 |
| 35 | faturamento comercial → filtre filial 02 | KPI comercial filtrado |

---

## Follow-up de sub-rota produto (11.1.1)

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 36 | estrutura do produto 10080047 → e os pais desse produto | Consulta parents do mesmo produto |
| 37 | resumo do produto 10080047 → ultimas compras | Compras do mesmo produto |

---

## Drill-down frontend (11.4.2)

| # | Ação | Mensagem gerada ao clicar |
|---|------|---------------------------|
| 38 | Clique em linha com filial + armazém + produto | `filtre filial 02 armazém 01 do produto 10080022` |
| 39 | Clique só com filial + produto | `filtre filial 01 do produto 10080022` |
| 40 | Clique em linha só com código/descrição | `Detalhe do item 90260077 (Parafuso)` |

---

## Identidade e capacidades (não são perguntas de produto)

| # | Como testar | O que esperar |
|---|-------------|---------------|
| 41 | Login rober / 1234 → portal carrega | `/core-api/me` retorna 200 |
| 42 | DevTools → `GET /apps/minha-delpi-ai/api/chat/capabilities` | `knowledgeDocumentMaxChars: 2000000` |

---

## Apresentação rica (11.4.3 — UI)

| # | Pergunta | O que observar |
|---|----------|----------------|
| 43 | estoque do produto 10080022 | Tabela/gráfico aparece antes do texto markdown |
| 44 | Na resposta com tabela | Toolbar Texto / Gráfico / Tabela / Expandir no topo |
| 45 | Expandir tabela → clique na linha | Drill-down funciona também no modal expandido |

---

## Parents / árvore / paginação (onda 11 — apresentação rica)

Use o agente **Especialista em Produtos** (ou agente com actions `api-delpi`).

### Consulta inicial + apresentação

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 46 | onde é usado o 10080022 | Comentário curto + banner parcial **uma vez** + toggle Árvore/Tabela (sem aba Texto redundante) |
| 47 | *(na resposta #46)* | Banner âmbar com página X de Y; **sem** bloco duplicado «Cobertura dos dados:» no texto |
| 48 | estrutura do produto 90260047 | Árvore PA→MPs; **sem** banner de profundidade se a estrutura estiver completa |

### Follow-up de paginação (mesma conversa)

| # | Pergunta | O que esperar |
|---|----------|---------------|
| 49 | *(após #46)* aumente para 50 linhas | Reconsulta rápida; mais linhas; **sem** RAG irrelevante; resposta **não** fica vazia |
| 50 | *(após #46 ou #49)* proxima pagina | Página 2 da mesma consulta; árvore/tabela atualizados |
| 51 | *(após #50)* pagina anterior | Volta à página anterior |
| 52 | *(alternativa)* botões **Anterior** / **Próxima** no card | Mesmo efeito de #50/#51; indicador «Página X de Y» |

### Profundidade hierárquica

| # | Pergunta / ação | O que esperar |
|---|-----------------|---------------|
| 53 | *(se houver aviso de max_depth)* clique **Ampliar níveis** | Reconsulta com profundidade maior; mais níveis na árvore |
| 54 | *(alternativa)* aumente a profundidade para 99 | Idem ao botão Ampliar níveis |

### Regressão de resposta vazia

| # | Sequência | O que esperar |
|---|-----------|---------------|
| 55 | #46 → #49 ou #50 | Conteúdo visível ao concluir o stream; **não** precisa dar F5 para ver texto/árvore |

---

## Referência — testes automatizados

Estes cenários têm cobertura em pytest / scripts do repositório:

| Área | Onde rodar |
|------|------------|
| Smoke operacional | `scripts/smoke_operational_questions.py` |
| Refinamento paginação | `tests/unit/domain/services/test_chat_operational_refinement_service.py` |
| Turn preparation paginação | `tests/unit/application/services/test_chat_turn_preparation_pagination_refinement.py` |
| Apresentação frontend | `plugins/minha-delpi-chat/scripts/verify-pagination-presentation.ts` |

```bash
# Backend (no container)
docker exec delpi-minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_operational_refinement_service.py \
  tests/unit/application/services/test_chat_turn_preparation_pagination_refinement.py -q

# Frontend (script de verificação)
docker run --rm -v "$(pwd)/plugins/minha-delpi-chat:/app" -w /app node:22-alpine \
  npx tsx scripts/verify-pagination-presentation.ts
```

---

## Anotações do teste

Use esta seção para marcar o que passou/falhou durante a validação manual.

| # | OK | Observação |
|---|:--:|------------|
| 1 | ☐ | |
| 2 | ☐ | |
| … | ☐ | |
