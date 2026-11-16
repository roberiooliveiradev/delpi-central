# Doc 126 — Portal Engenharia / Ficha do Produto — Wireframe da aba Roteiro

**Data:** 2026-11-16  
**Classificação:** `TARGET / UX PROPOSAL` — protótipo discutido no ChatGPT; não constitui implementação, aprovação final de arquitetura ou evidência de deploy.  
**Owner da experiência:** Portal Engenharia.  
**Fontes e autoridade:** Domain APIs / API-DELPI para roteiro; domínio determinístico existente da EVA para balanceamento; Engenharia aprova decisões de processo.  
**Origem visual:** captura fornecida pelo usuário da ficha real do produto 90260148 (`/apps/engineering/products/90260148`) + wireframe interativo elaborado na conversa. A captura e a interação do chat não são anexos deste arquivo; esta especificação registra seu conteúdo, sem fingir equivalência pixel-perfect.  
**Referências:** Doc 61 (UX de Produtos), Docs 122–125 (roteiro, line balancing, knowledge guiado e UX readiness), `WIREFRAMES.md`.  
**Task associada (proposta):** `EVA-PORTAL-PRODUCT-ROUTING-AND-LINE-BALANCING-UI-01`.

## 1. Estado visual atual observado na captura

- A ficha usa tema escuro e padrões do Portal, hero azul-escuro com título **Ficha do Produto**, identificação/descrição e badges de situação/ação.
- A navegação horizontal existente na captura é: **Visão geral · Estrutura · Onde é usado · Fornecedores · Desenhos · Histórico**.
- Na visão geral existem cartões **Identificação**, **Engenharia** e **Estoque e logística**; **Estoque não aparece como aba própria** na captura. Não presumir que o conjunto de abas seja imutável — conferir o código atual.
- A página está na rota `/apps/engineering/products/:code`. A nova experiência deve continuar dentro dessa rota e preservar as demais abas.
- Manter o design system nativo do Portal, `@delpi/plugin-ui`, contraste, foco, scroll responsivo e paridade light/dark. As cores hex do protótipo são aproximações de estudo, **não tokens para criar tema paralelo**.

## 2. Decisão visual proposta

Adicionar **Roteiro** depois de **Histórico** na navegação principal do detalhe. Dentro da nova aba, utilizar três seções internas:

1. **Operações** — consulta oficial e operações expansíveis com componentes.
2. **Balanceamento** — parâmetros, prévia transparente de takt e resultados do motor determinístico.
3. **Análise visual** — gráfico de tempos por operação e, quando disponível, tempo × takt.

A proposta privilegia uma tela por intenção, não duas colunas permanentes. **Decisão ainda aberta:** o usuário não concluiu a comparação entre subabas e a variante roteiro/calculadora lado a lado; documentar como `UX_DECISION_PENDING`, sem afirmar aprovação final.

### Wireframe estrutural (desktop, não pixel-perfect)

```text
Portal Engenharia › Produtos › [código]
+--------------------------------------------------------------------------------+
| PORTAL ENGENHARIA                                                               |
| Ficha do Produto                                       [Ativo] [Visualizar]      |
| [código] — [descrição oficial]                                                 |
+--------------------------------------------------------------------------------+
| Visão geral | Estrutura | Onde é usado | Fornecedores | Desenhos | Histórico |ROTEIRO|
+--------------------------------------------------------------------------------+
| Roteiro de fabricação                                          [Filial: 01 v] |
| Operações e análises de processo                                                |
| +--------------------+ +----------------------+ +----------------------------+ |
| | Operações únicas   | | Centros de trabalho  | | Registros no retorno       | |
| +--------------------+ +----------------------+ +----------------------------+ |
| [ OPERAÇÕES ] [ BALANCEAMENTO ] [ ANÁLISE VISUAL ]                              |
|                                                                                |
| SEÇÃO OPERAÇÕES:                                                               |
| [Estágio principal — nível 0 v]                                                |
| [01] Cortar etiqueta                  CT-19     tempo/peça        [expandir v] |
|      └ setup | recurso | componentes associados | fonte/unidades               |
| [02] Inserir termorretrátil          CT-54     tempo/peça        [expandir v] |
| [03] Aplicar terminal                CT-72     tempo/peça        [expandir v] |
| ... paginação / carregar mais / estados                                        |
|                                                                                |
| SEÇÃO BALANCEAMENTO:                                                           |
| Demanda [  ]     Duração turno [  ]   Pausas [  ]                              |
| Postos [opcional]   Lote [opcional]   Estágio [v]                              |
| Tempo disponível calculado: turno - pausas                                      |
| Takt (prévia transparente): minutos disponíveis / demanda                     |
| [Calcular balanceamento com EVA via backend autorizado]                        |
| Resultados: conteúdo, min. teórico, gargalo, eficiência, ociosidade, limites    |
|                                                                                |
| SEÇÃO ANÁLISE VISUAL:                                                          |
| Barras de tempo por operação; linha/meta takt quando houver cenário válido     |
| Provenance: OBSERVED | PROVIDED | CALCULATED | SIMULATION | UNKNOWN             |
+--------------------------------------------------------------------------------+
```

## 3. Componentes e comportamento

### 3.1 Cabeçalho e filtros

- Reutilizar hero/identificação do produto existente; não duplicar código/descrição dentro da aba.
- Seleção contextual de **filial 01, 02 ou todas** somente se o contrato e permissões suportarem.
- Seleção de **estágio**: produto principal (nível 0) e componentes fabricados por `product_code × bom_level`.
- Troca de produto/filial/estágio invalida apenas os dados e cenários pertinentes, sem misturar resultados anteriores.
- Lazy loading das seções; não buscar todo o roteiro na listagem geral do catálogo.

### 3.2 Indicadores rápidos

Cards discretos de **operações únicas**, **centros de trabalho distintos** e **registros retornados**. Número de registros **não é** número de operações. Tempo padrão total só quando a consolidação e escopo do estágio estiverem corretos; nunca somar BOM inteira como linha única. Preferir valores retornados por domínio, não lógica paralela de negócio no MFE.

### 3.3 Operações expansíveis

- Linha compacta: sequência/código, descrição da operação, CT/recurso, tempo padrão por peça com unidade.
- Expansão: setup em horas, recurso, tipo/obrigatoriedade quando houver significado conhecido e lista de componentes associados.
- Consolidar linhas duplicadas por componentes pela identidade oficial da operação, preservando os vínculos de componentes e a paginação.
- Paginação completa da fonte: **não contar somente a primeira página**; verificar `total`, `total_pages`, `page_size`, campos e limites.
- Acessibilidade: botão expansível com estado, foco, tabela/lista semântica, teclado e alternativa mobile.

### 3.4 Calculadora

Entradas propostas: demanda (peças/turno ou período declarado), duração de turno (min), pausas (min), postos atuais (opcional), tamanho de lote (opcional), estágio e filial.

Prévia do takt: `available_minutes = shift_minutes - break_minutes`; `takt = available_minutes / demand` somente com demanda positiva e tempo produtivo positivo. Isto é apenas **prévia aritmética de interface**; os resultados oficiais de balanceamento (conteúdo de trabalho, gargalos, postos, FFD, setup amortizado, eficiência, ociosidade) vêm do motor determinístico já existente, nunca reimplementado em JS.

- Exemplo **PROVIDED / DEMO**: demanda 500, turno 480 min, pausas 60 min, tempo disponível 420 min, takt 0,84 min/peça (50,4 s/peça). **Não são demanda/turno reais do produto.**
- Não amortizar `setup_hours` sem lote explícito.
- Postos e tamanho do lote opcionais; não inventar disponibilidade, restrição física, precedência ou operadores.
- Cenários FFD são `SIMULATION`, não plano aprovado.
- Se o contrato backend de análise não estiver aprovado, a UI deve documentar o bloqueio/estado em vez de simular uma chamada bem-sucedida.

### 3.5 Análise visual

Gráfico de barras por operação do **estágio selecionado**, com rótulo de unidade e vínculo com o roteiro. O takt só pode aparecer como comparação quando o cenário tiver parâmetros válidos. As operações acima do takt podem ser destacadas sem afirmar inviabilidade total (paralelismo/recursos não comprovados).

### 3.6 Estados e UX

Loading/skeleton; empty genuíno; 401/403; upstream 502/unavailable; filtros inválidos; partial; paginação; ausência de tempo; modo sem cenário calculado. Não converter `unavailable` em `sem roteiro`.

Produto de demonstração `90260148`: a consulta EVA anterior retornou `items=[]` com `branch=all`; usar como **caso de referência histórica de estado vazio**, não afirmar que o produto permanece sem roteiro no runtime atual.

## 4. Exemplos visuais de demonstração (não fixture canônico)

O protótipo utilizou o produto 90264135 (CHICOTE - P66), filial 01, com **amostra parcial** das operações previamente observadas:

| Seq. | Operação | CT | Tempo padrão por peça (min) |
|---|---|---|---:|
| 01 | CORTAR ETIQUETA | CT-19 | 0,0354 |
| 02 | INSERIR TERMORETRATIL | CT-54 | 2,0664 |
| 03 | APLICAR TERM 10080182 | CT-72 | 4,9290 |
| 04 | APLICAR TERM. 10080972 | CT-72 | 1,9716 |
| 05 | RETRAIR ETIQUETA | CT-54 | 1,7076 |
| 06 | INSERIR CONECTOR | CT-54 | 2,3148 |
| 07 | CORTAR CORRUGADO | CT-54 | 0,4956 |

Na consulta anterior ao MCP foram observados `total=412` **registros** de roteiro para 90264135 (não 412 operações). Os sete itens e três CTs no protótipo são contagens **somente da amostra**. Não usar contagens amostrais como KPIs de produção.

## 5. Contratos e integração: estado e fronteiras

- **Roteiro oficial (PROVEN no Doc 125):** `GET /v1/products/{code}/routing` pelo BFF Engineering API → api-delpi `/products/{code}/guide`; no frontend integrar pelo cliente existente (`features/products/api/productApi.ts`), sujeito à verificação atual.
- **Análise de balanceamento:** `analyze(routing.line_balance)` disponível no MCP EVA. **Não existe REST comprovado no Doc 125**; `POST /v1/products/{code}/line-balance` é **proposta de bounded contract**, não implementação autorizada automaticamente. Decisão de owner/contrato/AuthZ primeiro.
- **Conversa guiada:** `knowledge(routing.guided_analysis)` disponível ao consumidor ChatGPT. O Portal não possuía superfície EVA própria segundo o Doc 125. Qualquer integração conversacional precisa de owner/contrato legítimo e, se alterar fronteira de autoridade, `ARCHITECTURE_DECISION_REQUIRED`.
- **Segurança:** frontend não assume AuthZ, não chama SQL/TOTVS/MCP diretamente, não expõe secrets. A Engenharia mantém a decisão técnica e aprovação de mudanças de roteiro.

## 6. Aceite UX proposto

- **UX-01:** aba Roteiro após Histórico, no mesmo detalhe/rota, sem regressão nas abas anteriores.
- **UX-02:** paridade visual com o Portal real (dark/light, componentes, responsividade, foco/teclado).
- **UX-03:** seleção de filial e estágio sem mistura de dados.
- **UX-04:** operações não duplicadas por componente; expansão preserva os componentes reais.
- **UX-05:** indicadores não confundem `total` de registros com operações únicas.
- **UX-06:** tempo e setup exibidos conforme fonte, unidades corretas.
- **UX-07:** calculadora apresenta prévia válida; resultados complexos apenas do motor oficial.
- **UX-08:** distinção explícita entre OBSERVED, PROVIDED, CALCULATED, SIMULATION, UNKNOWN.
- **UX-09:** empty, forbidden, unavailable, partial e erro tratados diferentemente.
- **UX-10:** análise conversacional não aparece como executável sem integração autorizada.
- **UX-11:** verificação independente, teste visual na rota real, validação mobile e regressão das abas.

## 7. Decisões pendentes / próximo passo

1. **UX_DECISION_PENDING:** três seções internas (wireframe atual) versus operações e calculadora lado a lado.
2. **ARCHITECTURE_DECISION_REQUIRED se material:** aprovar owner/contrato de eventual BFF REST para cálculo, sem duplicar `compute_balance`.
3. **TO_INVENTORY:** definir a melhor experiência de paginação, agrupamento e seleção de estágios com respostas completas do contrato real.
4. **TARGET:** implementar frontend após verificação atual de HEAD/status, contrato, RQ/AC e testes; sem assumir deploy por este documento.

**Registro:** wireframe de referência, não implementação nem aprovação automática de UI final.
