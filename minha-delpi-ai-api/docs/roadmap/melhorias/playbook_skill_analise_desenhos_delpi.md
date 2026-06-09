# Playbook — Skill de Análise de Desenhos Técnicos DELPI

> **Status (30/05/2026):** Backlog — implementação na [Onda 12](../inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md).  
> **Projeto:** Minha DELPI Chat IA  
> **Arquitetura:** inteligência transversal no [chat base](../../architecture/chat-intelligence-base.md); agente só habilita skill/actions/RAG.

| Campo | Valor |
|-------|-------|
| `skillKey` (canônico) | `drawing-analysis-delpi` |
| `skillKey` (alias Onda 12 / legado) | `drawing-analyser` — unificar na Fase 1 |
| Nome amigável | Análise de Desenhos DELPI |
| `policyFile` (proposto) | `drawing-analysis-delpi-skill.md` |
| Action principal | `get_product_analyser` → `GET /products/{code}/analyser` |

**Paridade:** ChatGPT DELPI legado (`drawing_analyser_instructions.md`) e fluxo `PDF × API × Normas × Checklist`.

---

## 1. Objetivo da skill

A skill **Análise de Desenhos DELPI** deve analisar desenhos técnicos em PDF, confrontando o conteúdo do desenho com:

- PDF do desenho;
- API DELPI / Protheus;
- Normas Técnicas DELPI;
- Checklist Oficial de Revisão;
- Regras de validação de desenhos;
- Regras de códigos intermediários 50xx.

A finalidade é detectar divergências **antes da liberação** do desenho, principalmente em:

- código;
- revisão;
- cliente;
- BOM / estrutura;
- componentes;
- cotas;
- decapes;
- terminais;
- isoladores;
- roteiro;
- inspeções;
- padronização gráfica.

A lógica central da análise é:

```text
PDF do desenho
  × API DELPI / Protheus
  × Normas Técnicas DELPI
  × Checklist Oficial de Revisão
```

---

## 2. Regra principal

O PDF **não é soberano** quando contradiz o Protheus.

Se houver divergência entre o desenho e a API DELPI, a skill deve registrar o erro.

A comparação principal deve ser:

```text
PDF × API DELPI × Normas DELPI
```

A skill **não** deve suavizar divergências com expressões como:

- provavelmente;
- aparentemente;
- parece;
- talvez;
- possivelmente;
- deve estar correto.

Deve usar linguagem objetiva:

| Status | Uso |
|--------|-----|
| OK | Item conforme |
| Pendente | Informação ausente, parcial ou ilegível |
| Erro | Divergência que precisa correção |
| Erro crítico | Divergência que impede liberação |
| Não aplicável | Item não exigido para aquele desenho |

**Mapeamento na apresentação rica (Onda 9 / paridade GPT):** OK → ✅ · Pendente → ⚠️ · Erro / Erro crítico → ❌.

---

## 3. Nome da skill

| Campo | Valor |
|-------|-------|
| Nome técnico | `drawing-analysis-delpi` |
| Nome amigável | Análise de Desenhos DELPI |
| Descrição | Analisa desenhos técnicos DELPI em PDF, validando o documento contra dados reais do Protheus e normas internas. |

Registro previsto: catálogo global de skills (`catalog.json`), bootstrap admin, `metadata.skills` em agentes de engenharia/qualidade.

---

## 4. Quando acionar a skill

### 4.1 Pedidos explícitos

A skill deve ser acionada quando o usuário pedir:

- analisar desenho;
- validar PDF;
- conferir desenho com Protheus;
- revisar desenho técnico;
- validar BOM;
- validar cotas;
- conferir decapes;
- validar código intermediário;
- verificar desenho antes de liberar;
- gerar relatório técnico de desenho.

**Exemplos de comando:**

- Analise este desenho.
- Verifique se este PDF está conforme.
- Confira o desenho com o Protheus.
- Valide as cotas e decapes.
- Gere relatório técnico do desenho.
- Verifique se posso liberar este desenho.

### 4.2 Anexo PDF + vocabulário técnico

Também deve ser acionada quando o usuário **anexar um PDF** e usar termos como:

- desenho; revisão; carimbo; BOM; tabela de materiais;
- cota; decape; intermediário 50xx; SG1010;
- roteiro; inspeção; QP6; QP7; QP8.

### 4.3 Intent (chat base)

Implementação prevista: `ChatDrawingIntentService` — não confundir com busca de catálogo, estoque ou ficha resumida (`/summary`).

| Sinal | Ação |
|-------|------|
| PDF + intent drawing | Pipeline modo drawing; desliga fast path genérico incorreto |
| Código na mensagem ou carimbo (OCR) | Dispara `get_product_analyser` |
| Sem PDF | Resposta fixa: pedir anexo |
| Agente sem skill | Orientar habilitar skill ou negar pipeline drawing |

---

## 5. Fonte principal da API

A rota principal deve ser:

```http
GET /products/{code}/analyser?page=1&page_size=50&max_depth=10
```

Essa rota deve retornar dados como:

- produto (SB1010);
- descrição;
- estrutura / BOM (SG1010);
- componentes;
- roteiro (SG2010);
- inspeções (QP6 / QP7 / QP8);
- dados técnicos relacionados.

**Action no catálogo:** `get_product_analyser` (api-delpi / api-externa conforme provider do agente).

Se a API não encontrar o produto, a análise deve classificar como **erro crítico**:

> Erro crítico: produto não encontrado na API DELPI.

Apresentação humana do payload `/analyser` já existe em `ExternalActionResultPresenter` (roteiro, inspeção, estrutura) — a skill deve **reutilizar** esse presenter e acrescentar camada de validação PDF × API.

---

## 6. Fontes obrigatórias

A skill deve usar as fontes **nesta ordem de autoridade** para divergências:

| # | Fonte | Caminho no repositório |
|---|--------|-------------------------|
| 1 | API DELPI / Protheus | `GET /products/{code}/analyser` |
| 2 | PDF do desenho | Anexo da sessão + extração OCR/visão |
| 3 | Checklist Oficial de Revisão | Seções em `drawing_analyser_instructions` / `drawing_analyser_instructions_full` |
| 4 | Fluxo rígido de análise | [`drawing_analyser_instructions.md`](../../knowledge/sources/gpt-instructions/drawing_analyser_instructions.md) · domínio [`gpt-drawing-analyser-instructions.md`](../../knowledge/domains/gpt-instructions/gpt-drawing-analyser-instructions.md) |
| 5 | Requisitos obrigatórios | [`drawing_requirements_delpi.md`](../../knowledge/sources/gpt-instructions/drawing_requirements_delpi.md) |
| 6 | Padrões gráficos | [`drawing_rules_delpi.md`](../../knowledge/sources/gpt-instructions/drawing_rules_delpi.md) |
| 7 | Critérios automáticos | [`drawing-validation-rules-delpi.md`](../../knowledge/domains/agents/minha-delpi-chat/drawing-validation-rules-delpi.md) |
| 8 | Normas técnicas por grupo | [`normas-tecnicas-delpi.md`](../../knowledge/domains/global/normas-tecnicas-delpi.md) (`company-knowledge`) |
| 9 | Códigos intermediários 50xx | [`Understanding DELPI Intermediate Product Codes.md`](../../knowledge/sources/gpt-instructions/Understanding%20DELPI%20Intermediate%20Product%20Codes.md) |
| 10 | Rotas Product API | `product_api_instructions` (RAG agente / gpt-instructions) |

Ingestão: [`scripts/sync_gpt_instructions_knowledge.py`](../../../scripts/sync_gpt_instructions_knowledge.py) · mapa: [`gpt-instructions-coverage-map.md`](../../knowledge/gpt-instructions-coverage-map.md).

---

## 7. Fluxo completo da análise

### 7.1 Receber e validar o PDF

A skill deve verificar:

- se existe PDF anexado;
- se o arquivo é PDF;
- número de páginas;
- legibilidade;
- orientação;
- presença de carimbo;
- presença de tabela de materiais;
- presença de cotas;
- presença de vistas;
- qualidade visual.

| Resultado | Ação |
|-----------|------|
| PDF válido | continuar análise |
| PDF válido com restrições | continuar e registrar alerta (Pendente) |
| PDF ilegível | marcar análise incompleta |
| Sem PDF | pedir anexo |

**Resposta sem PDF:**

> Para analisar o desenho, preciso que você anexe o PDF.

**Serviço previsto:** `ChatDrawingPdfExtractionService` (Onda 12.2). Evolução **OCR hierárquico** (carimbo base-direita, BOM/cotas por região, resolução de código sem prefixo `902`): [Onda 14](../inteligencia-chat-onda-14-ocr-hierarquico-desenhos.md) · [playbook](./playbook_ocr_hierarquico_desenhos_delpi.md).

---

### 7.2 Extrair dados do PDF

A skill deve extrair (schema estruturado para merge com API) — ver contrato `DrawingHierarchicalExtract` no [playbook OCR hierárquico](./playbook_ocr_hierarquico_desenhos_delpi.md) §5:

- código DELPI;
- revisão;
- cliente;
- código cliente;
- descrição;
- data;
- LMP;
- executado;
- verificado;
- liberado;
- tabela de materiais;
- componentes;
- quantidades;
- cotas;
- decapes;
- lado A/B;
- observações técnicas;
- códigos intermediários 50xx.

---

### 7.3 Consultar a API DELPI

Após identificar o código, consultar obrigatoriamente:

```http
GET /products/{code}/analyser?page=1&page_size=50&max_depth=10
```

A resposta valida:

- cadastro do produto;
- descrição;
- revisão;
- estrutura;
- componentes;
- roteiro;
- inspeções.

**Orquestração prevista:** `ChatDrawingValidationOrchestrationService` (Onda 12.3).

---

### 7.4 Validar cabeçalho e carimbo

| Campo | Regra |
|-------|-------|
| Código DELPI | Deve existir e bater com API |
| Descrição | Deve bater com cadastro ou regra técnica |
| Revisão | Deve bater com revisão atual (`B1_REVATU` / equivalente) |
| Cliente | Completo e coerente |
| Data | Formato válido |
| LMP | Obrigatória |
| Executado | Obrigatório |
| Verificado | Obrigatório quando aplicável |
| Liberado | Obrigatório |
| Escala | Indicada |
| Unidade | mm |
| Logo DELPI | Correto |
| Resumo de modificações | Coerente com a revisão |

**Erros críticos no cabeçalho:**

- código divergente;
- revisão divergente;
- cliente divergente;
- ausência de carimbo;
- dois códigos conflitantes;
- código do arquivo diferente do cabeçalho.

---

### 7.5 Validar BOM / tabela de materiais

Comparar:

```text
Tabela de materiais do PDF  ×  Estrutura SG1010 da API
```

Validar:

- todos os componentes da API aparecem no PDF;
- todos os componentes do PDF existem na API;
- código; descrição; quantidade; unidade; posição; balão;
- duplicidade; componente extra; componente faltante.

| Caso | Severidade |
|------|------------|
| Componente da API ausente no PDF | Erro crítico |
| Componente do PDF ausente na API | Erro crítico |
| Quantidade divergente | Erro ou erro crítico |
| Descrição divergente | Pendente ou erro |
| Item sem balão | Erro |
| Balão sem item | Erro |

---

### 7.6 Validar cotas e dimensões

Validar:

- comprimento total;
- comprimentos secundários;
- decape esquerdo;
- decape direito;
- tolerâncias;
- unidade;
- cotas ilegíveis;
- cotas ausentes;
- coerência com código intermediário.

Comparar:

```text
Cota PDF  ×  API DELPI  ×  Código intermediário  ×  Norma DELPI
```

**Tolerâncias (validation_rules):** comprimento ±5%; decape ±1 mm quando aplicável.

Classificar como **erro** quando:

- cota principal ausente;
- cota ilegível;
- unidade ≠ mm;
- comprimento divergente;
- decape divergente;
- tolerância ausente quando obrigatória.

---

### 7.7 Validar código intermediário 50xx

Estrutura esperada:

```text
50xx xxxx xx xxx xxxx-xx/xx-xxxx-xxxx
```

Validar:

- família 50xx; tipo de cabo; bitola; cor; comprimento;
- decape esquerdo/direito; terminal e isolador A/B; formatação.

| Divergência | Severidade |
|-------------|------------|
| Cor divergente | Erro crítico |
| Bitola divergente | Erro crítico |
| Comprimento divergente | Erro crítico |
| Decape divergente | Erro ou erro crítico |
| Terminal invertido | Erro crítico |
| Isolador divergente | Erro crítico |
| Código mal formatado | Erro crítico |

---

### 7.8 Validar roteiro de produção

Validar via API:

- existência de roteiro;
- sequência de operações;
- centro de trabalho;
- recurso;
- operação final;
- operação de inspeção;
- CT-99 quando aplicável;
- coerência com observações do desenho.

Se o roteiro obrigatório estiver ausente:

> Erro crítico: roteiro de produção ausente.

---

### 7.9 Validar inspeções QP6 / QP7 / QP8

Validar:

- QP6 vinculado;
- QP7 para características mensuráveis;
- QP8 para observações;
- vínculo com operação correta;
- coerência com notas técnicas;
- inspeção de cabo, crimpagem, decape e montagem.

| Caso | Severidade |
|------|------------|
| Inspeção obrigatória ausente | Erro crítico |
| QP7 ausente para item mensurável | Erro |
| Observação divergente | Erro |
| Inspeção sem vínculo claro | Pendente |

---

### 7.10 Validar regras gráficas

Validar conforme `drawing_rules_delpi`:

- formato A4; margens; moldura; logo DELPI; carimbo; título;
- legibilidade; tabela de materiais; balões; linhas de chamada;
- vistas; cortes; lado A/B; notas técnicas; cores; cotas;
- ausência de sobreposição.

---

## 8. Classificação dos resultados

Cada item do checklist recebe um dos status da seção 2.

**Status geral do desenho:**

| Status geral | Condição |
|--------------|----------|
| Aprovado | Sem erro crítico; sem erro bloqueante |
| Aprovado com ressalvas | Apenas Pendente / Erro não crítico |
| Reprovado | ≥1 erro crítico |
| Análise incompleta | PDF ilegível ou extração falhou em área crítica |

---

## 9. Erros críticos (consolidado)

Classificar como **erro crítico** quando houver:

- produto inexistente na API;
- código divergente;
- revisão divergente;
- cliente divergente;
- componente faltante ou extra;
- terminal ou isolador divergente;
- bitola, cor ou comprimento divergente;
- código 50xx mal formatado;
- roteiro obrigatório ausente;
- inspeção obrigatória ausente;
- PDF ilegível em área crítica (carimbo, cota principal, BOM).

---

## 10. Modelo de relatório técnico

```markdown
# Relatório de Análise de Desenho DELPI

## 1. Status geral
Reprovado | Aprovado | Aprovado com ressalvas | Análise incompleta

## 2. Dados identificados no PDF
| Campo | Valor |
|-------|-------|
| Código | ... |
| Revisão | ... |
| Cliente | ... |
| LMP | ... |

## 3. Dados retornados pela API
| Campo | Valor |
|-------|-------|
| Código | ... |
| Descrição | ... |
| Revisão | ... |
| Estrutura | ... |
| Roteiro | ... |
| Inspeção | ... |

## 4. Divergências críticas
| Seção | Item | PDF | API | Regra | Ação |
|-------|------|-----|-----|-------|------|

## 5. Checklist completo
| Seção | Item avaliado | Status | Observação |
|-------|---------------|--------|------------|

## 6. Conclusão
O desenho pode ou não pode ser liberado.
```

Apresentação: markdown + tabelas ricas (Onda 9); opcional export PDF/XLSX (Onda 12.4).

---

## 11. Metadata JSON recomendada

```json
{
  "drawingAnalysis": {
    "status": "rejected",
    "productCode": "90264130",
    "revisionPdf": "00",
    "revisionApi": "01",
    "criticalErrors": 2,
    "errors": 4,
    "warnings": 3,
    "items": [
      {
        "section": "Cabeçalho",
        "item": "Revisão",
        "status": "critical_error",
        "pdfEvidence": "REV.00",
        "apiEvidence": "REV.01",
        "rule": "Revisão deve bater com SB1010",
        "recommendation": "Atualizar revisão do desenho"
      }
    ]
  }
}
```

**Consumidores:** `adminDebug`, cards de erro no MFE, histórico de análises, dashboard de qualidade, exportação, filtros por erro crítico.

Espelhar em `message.metadata` / stream activities (`ChatStreamActivityService`).

---

## 12. Integração com UI

### 12.1 Após upload do PDF

Chips / botões:

- Analisar desenho
- Ver checklist
- Validar cabeçalho
- Validar BOM
- Validar cotas
- Validar código 50xx
- Gerar relatório

### 12.2 Durante a análise

Estágios no stream:

1. Lendo PDF…
2. Identificando código…
3. Consultando API DELPI…
4. Validando cabeçalho…
5. Conferindo BOM…
6. Conferindo cotas…
7. Validando roteiro…
8. Validando inspeções…
9. Aplicando normas…
10. Gerando relatório…

### 12.3 Após relatório

- Ver só erros críticos
- Ver checklist completo
- Exportar relatório
- Colocar na lousa
- Gerar plano de correção
- Reanalisar outro PDF
- Comparar com revisão anterior

**MFE:** alinhar a Playbook 07 (anexos) e Playbook 06 (lousa).

---

## 13. Integração com lousa

Comandos suportados (`ChatCanvasIntentService`):

- Coloque o relatório na lousa.
- Gere plano de ação na lousa.
- Crie checklist de correção.
- Gere resumo executivo.
- Transforme em e-mail para engenharia.
- Transforme em ata de revisão.

---

## 14. Ações corretivas sugeridas

| Erro encontrado | Ação recomendada |
|-----------------|------------------|
| Revisão divergente | Atualizar revisão do PDF ou cadastro |
| Componente faltante | Corrigir BOM do desenho ou estrutura |
| Terminal divergente | Revisar terminal lado A/B |
| Comprimento divergente | Corrigir cota ou estrutura |
| Decape divergente | Revisar código intermediário e desenho |
| Roteiro ausente | Cadastrar roteiro ou bloquear liberação |
| Inspeção ausente | Cadastrar QP6/QP7/QP8 |
| Carimbo incompleto | Preencher campos obrigatórios |
| PDF ilegível | Regerar PDF em melhor qualidade |

---

## 15. Prompt interno recomendado

Policy `drawing-analysis-delpi-skill.md` (registrar em `PromptPolicyService`):

```text
Você é a skill de Análise de Desenhos Técnicos DELPI.

Sua função é analisar desenhos técnicos em PDF, confrontando as informações
extraídas do PDF com dados reais da API DELPI e normas internas.

Regras obrigatórias:
1. Não invente dados ausentes.
2. Não aprove desenho com divergência crítica.
3. Use a API DELPI como fonte primária.
4. Compare PDF × API × Normas.
5. Classifique cada item como OK, PENDENTE, ERRO ou ERRO CRÍTICO.
6. Sempre informe evidência PDF e evidência API quando houver divergência.
7. Se o PDF estiver ilegível em área crítica, interrompa e marque análise incompleta.
8. Se o produto não existir na API, marque erro crítico.
9. Use o checklist oficial como base mínima.
10. Gere relatório técnico objetivo e auditável.
```

---

## 16. Testes de regressão

| Artefato | Caminho |
|----------|---------|
| Unit intent | `tests/unit/domain/services/test_chat_drawing_intent_service.py` |
| Unit orquestração | `tests/unit/domain/services/test_chat_drawing_validation_orchestration_service.py` |
| Regressão chat | `tests/fixtures/chat_intelligence_regression_cases.py` |
| Smoke | `scripts/smoke_drawing_analyser.py` |
| Fixtures PDF | `tests/fixtures/drawings/` (anonimizados) |

### Casos mínimos (`test_drawing_analysis_skill.py`)

| Caso | Entrada | Esperado |
|------|---------|----------|
| D1 | PDF válido + produto existente | Extrai código, consulta API, relatório |
| D2 | Produto não existe | Erro crítico |
| D3 | Revisão divergente | Erro crítico |
| D4 | Componente faltante | Erro crítico |
| D5 | Componente extra | Erro crítico |
| D6 | Comprimento divergente | Erro crítico |
| D7 | Decape divergente | Erro ou erro crítico |
| D8 | Código 50xx mal formatado | Erro crítico |
| D9 | PDF ilegível | Análise incompleta |
| D10 | Roteiro ausente | Erro crítico |
| D11 | Inspeção ausente | Erro crítico ou erro |
| D12 | Relatório completo | Evidência PDF, API, norma e recomendação |

---

## 17. Métricas da skill

Medir (admin / observabilidade):

- desenhos analisados;
- taxa de aprovação / reprovação;
- erros críticos por tipo;
- componentes e revisões divergentes;
- cotas divergentes;
- desenhos ilegíveis;
- tempo médio de análise;
- uso de `/products/{code}/analyser`;
- relatórios exportados;
- planos de ação gerados;
- feedback do usuário.

---

## 18. Roadmap de implementação

Alinhado à [Onda 12](../inteligencia-chat-onda-12-skill-analise-desenhos-pdf.md).

| Fase | Escopo | IDs Onda 12 |
|------|--------|-------------|
| **1 — MVP técnico** | PDF; extrair código; `/analyser`; relatório básico; cabeçalho + BOM | 12.1, 12.3 (parcial), 12.4.1 |
| **2 — Validação normativa** | Checklist + requirements + rules + validation_rules no RAG/policy | 12.1.2, RAG global |
| **3 — Dimensional e 50xx** | Cotas; decapes; intermediários; terminais/isoladores | 12.2, 12.3.2 → **[Onda 13 / visão OCR](./playbook_skill_visao_documentos_ocr_delpi.md)** |
| **4 — Relatório avançado** | Evidências por página; severidade; plano de ação; export; lousa | 12.4 |
| **5 — UI interativa** | Progresso; chips filtro; seções; reanálise; comparar revisões | 12.4.2, MFE |
| **6 — Qualidade e auditoria** | Métricas; histórico; dashboard; feedback; testes D1–D12 | 12.5 |

### Pipeline (referência implementação)

```text
Anexo PDF + mensagem
  → ChatDrawingIntentService
  → ChatIntelligencePipelineService (modo drawing)
  → ChatDrawingPdfExtractionService
  → ChatToolContextService → get_product_analyser
  → ChatDrawingValidationOrchestrationService
  → RAG (drawing_* + normas)
  → PromptPolicyService → drawing-analysis-delpi-skill.md
  → LLM + ExternalActionResultPresenter + relatório
```

---

## 19. Anti-padrões

Evitar:

1. Aprovar desenho sem consultar API.
2. Usar norma no lugar da API quando houver cadastro.
3. Inventar campo ausente.
4. Ignorar cota ilegível.
5. Tratar divergência crítica como observação.
6. Não mostrar evidência.
7. Misturar dados de outro produto.
8. Usar «parece correto».
9. Não validar revisão.
10. Não validar BOM completa.
11. Não validar componentes extras.
12. Não registrar erro quando PDF estiver ruim.
13. Relatório só textual sem tabela.
14. Não sugerir ação corretiva.
15. Não separar erro crítico de pendência.
16. Implementar lógica **só** no `system_prompt` do agente (viola chat base).
17. Duplicar presenter `/analyser` — estender validação, não reformatar dump bruto.

---

## 20. Resumo executivo

A skill **Análise de Desenhos DELPI** é uma ferramenta **rígida, auditável e integrada à API DELPI**.

Ela recebe um PDF, extrai informações, consulta o Protheus, aplica normas internas e gera relatório com evidências.

**Regra central:**

```text
PDF × API × Normas — divergência relevante vira erro.
```

O chat passa a atuar como **verificador técnico de engenharia**, reduzindo liberação de desenhos com revisão errada, BOM divergente, códigos 50xx incorretos e falhas dimensionais.

---

## 21. O que já existe (não reimplementar)

- Documentação GPT de desenho sincronizada no RAG.
- Action `get_product_analyser` no catálogo.
- Presenter humanizado de `/analyser` (`external_action_result_presenter.py`).
- Pipeline de anexos (`session_source`) — Playbook 07.
- Normas técnicas globais (`company-knowledge`).

---

## 22. Critérios de aceite (playbook)

- [ ] PDF + código (ou OCR) → relatório com checklist e status por item.
- [ ] Divergências críticas impedem «Aprovado».
- [ ] Agente sem skill não entra no pipeline drawing.
- [ ] `adminDebug`: intent, extração, analyser, validações.
- [ ] Smokes D1–D12 e regressão estoque/busca intactos.

---

## Histórico

| Data | Alteração |
|------|-----------|
| 2026-05-30 | Criação do playbook a partir da especificação de produto; alinhamento Onda 12 e chat base. |
