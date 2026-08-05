# 01 — Especificação funcional consolidada

**Fonte:** materiais 2027 (e referência TI 2026), Carta extraída, escopo declarado na solicitação da Fase 0.  
**Regra:** inconsistências **não** foram “corrigidas” — constam como decisões necessárias.

---

## 1. Visão do produto

Aplicativo na Minha DELPI para o **ciclo anual** de planejamento orçamentário, cobrindo:

- orientações e Mensagem da Diretoria (Carta);
- confirmação obrigatória de leitura;
- projeção de receita;
- orçamento de pessoal;
- orçamento de investimentos (CAPEX);
- workflows de aprovação;
- consolidação gerencial;
- auditoria;
- exportações Excel e PDF;
- integração com ERP (leitura / referência);
- autorização por unidade, área e centro de custo.

---

## 2. Análise dos materiais

### 2.1 Carta do Orçamento (`Carta Orcamento - 2027.doc`)

**Conteúdo extraído (resumo):**

- Abertura do ciclo de orçamento (**texto fala em 2026**, não 2027 — inconsistência com o nome do arquivo).
- Foco em otimização de recursos, produtividade, eliminação de gargalos, reforma/substituição de equipamentos.
- Análise crítica da **capacidade real de execução** do orçamento por departamento.
- Volumes de produção: usar **orçamento de produção** (documento/processo externo — não fornecido).
- Prazos: exemplo na carta — previsões até **04/11/2025** (ciclo anterior).

**Orientações CAPEX citadas na Carta:**

| Orientação | Campo implícito |
|------------|-----------------|
| Projeção por centro de custo | C.Custo / Centro de Custo |
| Provável fornecedor | Fornecedor |
| Nacional ou importado | **Campo citado na Carta; não aparece nas colunas da planilha CAPEX analisada** |
| Classificação (capacitação, reposição, reforma, retrofitting) | Classif. |
| Uso (produção, segurança, meio ambiente…) | Possível sobreposição com Classificação / Observações — **ambíguo** |
| Valor em R$ sem impostos (ICMS, PIS, COFINS) | Valor TOTAL |
| Reforma: indicar patrimônio na descrição | Texto livre em Descrição |
| Bens usados / outras áreas | Identificar na descrição/observações |

**Orientações Pessoal citadas na Carta:**

| Orientação | Impacto |
|------------|---------|
| Prever MO com ganhos de produtividade | Regra de negócio / narrativa |
| Previsão por **seção/centro de custo e cargo** | **Não refletido** na planilha Pessoal 2027 (só agregados por área) |
| Projeção mês a mês visando posição 31/12 | Planilha tem colunas pontuais (dez/out/previsto), **não** grade mensal |
| Estagiários/temporários **fora** do quadro; orçar só em despesas por CC | Fora do escopo da planilha Pessoal |

### 2.2 Orçamento de Pessoal 2027 (`.xlsx`)

| Item | Valor |
|------|-------|
| Abas | `DELPI` (única) |
| Título | `ORÇAMENTO PESSOAL 2027` |
| Unidade (exemplos) | `DELPI JARAGUA - CHICOTES`, `DELPI ESPIRITO SANTO`, `TOTAL DELPI` |
| Áreas | PRODUCAO (com sublinhas MAO OBRA DIRETA / INDIRETA), VENDAS, ADMINISTRACAO, TOTAL |
| Colunas | 2025 DEZEMBRO; 2026 OUTUBRO; PREVISTO DEZEMBRO; Var. 26/25; 2027 DEZEMBRO; Var. 27/26 |
| Valores no arquivo | Todos **0** (template) |
| Fórmulas | Totais por soma de linhas; variações `E/C` e `G/E` (hoje `#DIV/0!` com zeros) |

**Campos digitáveis vs calculados:**

- Digitáveis: headcount por linha de área/unidade nas colunas C/D/E/G (conforme hierarquia).
- Calculados: totais PRODUCAO, TOTAL unidade, TOTAL Delpi, variações percentuais.

**Regras implícitas:**

- Unidade SC (Jaraguá) e ES são blocos separados + consolidado.
- Produção decompõe MOD + MOI; vendas e administração são linhas únicas.
- Comparação temporal usa três âncoras (dez/25, out/26, previsto dez, dez/27) — **não** série mensal completa.

**Riscos de interpretação:**

1. “PREVISTO DEZEMBRO” é 2026 ou outra competência? Cabeçalho agrupa sob 2026.
2. Var. 26/25 = previsto/dez25 — não usa a coluna OUTUBRO 2026.
3. Carta pede cargo/CC; planilha não tem — **decisão de modelo**.
4. Sem validação de inteiros positivos, tetos ou justificativa de variação.

### 2.3 Orçamento de Investimentos / CAPEX 2027 (`.xls`)

| Item | Valor |
|------|-------|
| Abas | `Instruções de Preenchimento`, `2027` |
| Título (SST) | `Orçamento de Investimentos - 2027` |

**Colunas (alinhadas às instruções + planilha TI 2026 de referência):**

| Campo | Lista / regra |
|-------|----------------|
| Prioridade | 1 Compra aprovada/em andamento; 2 Maior necessidade; 3 Média; 4 Menor |
| C.Custo | Código |
| Centro de Custo | Descrição |
| Responsável | Nome do responsável pela aquisição |
| Conta | Lista fechada (ex.: COMPUT.E PERIFÉRICOS, FERRAMENTAS, INSTALAÇÕES, INSTRUMENTOS…, MÁQUINAS…, MÓVEIS…, OBRAS…, SOFTWARES…, VEÍCULOS). TI 2026 também usou valores **fora** da lista (SERVIÇOS, VISITA TECNICA, CAPACITAÇÃO) |
| Descrição | Texto detalhado (modelo, referência) |
| Fornecedor | Provável fornecedor |
| Turno | 1, 2 ou 3 |
| Valor TOTAL | Sem impostos |
| Data Rcbto | Data recebimento / NF |
| Classif. | 1 Capacitação produção; 2 Reforma/Retrofiting; 3 Reposição/Substituição; 4 Segurança/Ergonomia; 5 Melhorias Q&P; 6 Outros |
| Observações | Texto livre |

**Exemplos preenchidos (SST 2027 / TI 2026):** metrologia Mitutoyo; reforma laboratório; notebooks; CC `205` INFORMÁTICA; responsáveis Jose/João/Pedro/Michael; valores e datas diversas.

**Dados que parecem mestres (ERP ou cadastro):** código/descrição CC, lista de contas contábeis/imobilizado, fornecedor.  
**Dados manuais:** prioridade, descrição, valor, data, classificação, observações, turno, responsável.

**Campo na Carta ausente na planilha:** nacional/importado.

### 2.4 Previsão de Receita

**Não localizada.** Escopo funcional declarado (linhas por cliente, prospects, projetos) permanece como requisito a detalhar com o negócio + material faltante.

### 2.5 Protótipo legado `Projeto-orcamento`

Formulário de **solicitação de orçamento interno** (solicitante, departamento, prioridade, itens). **Não** modela exercício anual, CAPEX, pessoal nem Carta. Usar apenas como lição negativa (auth/UI ad hoc fora do portal).

---

## 3. Requisitos funcionais consolidados (por módulo)

| ID | Módulo | Requisito |
|----|--------|-----------|
| RF-EX | Exercício | Abrir/configurar exercício anual (ex.: 2027); prazos; status global |
| RF-OR | Orientações | Publicar Mensagem da Diretoria + documentos; versionar |
| RF-CL | Confirmação | Bloquear edição até confirmação de leitura (por usuário/exercício) |
| RF-SC | Escopo | Usuário vê/edita só unidade/área/CC autorizados |
| RF-RE | Receita | Projetar receita (clientes, prospects, projetos) — detalhe pendente de material |
| RF-PE | Pessoal | Informar headcount por unidade/área (e, se decidido, cargo/CC) |
| RF-CA | CAPEX | Linhas de investimento com validações e listas fechadas |
| RF-WF | Workflow | Submeter, devolver, aprovar, bloquear |
| RF-CO | Consolidação | Visões gerenciais por unidade/área/conta/prioridade |
| RF-AU | Auditoria | Trilha de eventos e snapshots de aprovação |
| RF-EXX | Export | Excel detalhado + PDF executivo |
| RF-ERP | ERP | Importar/referenciar realizados e mestres (ROL, CC, clientes…) sem escrita no Protheus no MVP |

---

## 4. Decisões de negócio necessárias (não resolvidas)

Ver lista completa em `10-riscos-pendencias-e-decisoes.md`. Principais:

1. Alinhar Carta ao exercício **2027** (conteúdo vs nome do arquivo).
2. Pessoal: agregado por área **ou** detalhe cargo/CC?
3. CAPEX: campo nacional/importado obrigatório?
4. Contas CAPEX: lista fechada estrita ou permitir valores livres (como TI 2026)?
5. Modelo de receita e origem ERP.
6. Cadeia de aprovação (gestor CC → diretor área → diretoria) e quem consolida.
7. Fonte oficial do cadastro de centros de custo (view vs CTT vs planilha).
