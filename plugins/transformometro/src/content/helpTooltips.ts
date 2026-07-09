/**
 * Textos dos balões explicativos (HelpTooltip) do Transformômetro.
 * Centralizados por tela/domínio — não vêm da API. Mesmo padrão do Kaizen.
 */
export const TM_HELP_TOOLTIPS = {
  /** Cabeçalhos de coluna reutilizados em várias tabelas. */
  columns: {
    codigo: "Identificador curto do registro (código de negócio ou ERP).",
    codigoTotvs: "Código da unidade no ERP (TOTVS), ex.: 01, 02.",
    nome: "Nome exibido nas telas, relatórios e filtros.",
    unidade: "Unidade operacional (filial) associada ao registro.",
    unidades: "Unidades em que o departamento ou vínculo está ativo.",
    setor: "Departamento operacional dentro da unidade.",
    setores: "Departamentos vinculados à melhoria.",
    status: "Situação do cadastro — ativos entram nos formulários e no dashboard.",
    rotulo: "Título curto da melhoria (opcional), para reconhecê-la na listagem.",
    versao: "Número ou rótulo da revisão do processo (ex.: 1.0.0, 2.1).",
    cenario: "Tipo de cenário: linha de base, melhoria, automação ou correção.",
    referenciaComparacao:
      "Revisão usada como referência para calcular economia e diffs desta versão.",
    inicio: "Data de início da vigência da revisão ou período de custo.",
    implantacao: "Data em que a melhoria entrou em operação.",
    fim: "Data de encerramento da vigência. Revisões encerradas deixam de ser ativas.",
    ativa: "Revisão marcada como vigente na instância — usada como referência operacional.",
    competencia: "Mês de referência dos dados consolidados (YYYY-MM).",
    mesesComDados: "Quantidade de competências com medição registrada na revisão.",
    economiaBruta: "Ganho bruto estimado antes de descontar investimentos e recursos.",
    economiaLiquida: "Ganho após descontar investimentos e rateio de recursos compartilhados.",
    investimentoTotal: "Soma dos investimentos apropriados no período da revisão.",
    recursosComp: "Custo mensal de recursos compartilhados rateados para a revisão.",
    horasMes: "Horas de trabalho economizadas por mês na revisão.",
    rateio: "Critério de divisão do custo do recurso entre vínculos.",
    escopo: "Alcance geográfico/organizacional do rateio do recurso.",
    custoMesVigente: "Valor mensal vigente na data atual — vem do histórico de custos.",
    vigenciaRecurso: "Período em que o recurso está cadastrado como ativo no catálogo.",
    tipo: "Classificação do item (investimento, recurso, etc.).",
    descricao: "Descrição textual do item ou evidência.",
    quantidade: "Quantidade de unidades do investimento.",
    valorUnitario: "Valor por unidade — total = quantidade × unitário.",
    valorMes: "Valor mensal do custo ou reajuste.",
    recorrencia: "Periodicidade do custo ou investimento (único, mensal, anual…).",
    categoria: "Agrupador opcional para relatórios e filtros.",
    data: "Data de referência do investimento ou evento.",
    mesesVigencia: "Quantos meses o investimento único é diluído no cálculo.",
    processo: "Processo operacional vinculado ao recurso ou instância.",
    revisao: "Revisão do processo onde o vínculo ou medição se aplica.",
    usoRevisao: "Período em que o recurso é usado nesta revisão específica.",
    peso: "Peso no rateio quando o critério é «por peso».",
    ativoVinculo: "Vínculo considerado no rateio mensal quando marcado como ativo.",
    familia: "Agrupador de processos no dashboard (ex.: ia, automação).",
    processos: "Quantidade de processos no agrupador ou recorte.",
    implantacaoProcesso: "Data de implantação da solução no processo.",
    economiaDia: "Economia bruta média por dia no recorte filtrado.",
    investVigentes: "Investimentos ainda vigentes no período analisado.",
    recursosVigentes: "Custos de recursos compartilhados vigentes no período.",
    liquidaRecorte: "Economia líquida acumulada no recorte de datas.",
    brutaRecorte: "Economia bruta acumulada no recorte de datas.",
    fornecedor: "Fornecedor ou editor da licença/ferramenta.",
    observacoes: "Notas livres complementares ao cadastro.",
    total: "Valor total do item (quantidade × unitário).",
    baseCompetencia: "Forma de apropriar o custo no mês: valor cheio ou proporcional aos dias.",
    unitario: "Valor unitário em R$.",
    mesesVigenciaCurto: "Meses em que um investimento único é diluído no cálculo.",
    acoes: "Comandos da linha: abrir cadastro, editar, excluir ou outras opções conforme a tela.",
  },
  dashboard: {
    view:
      "Alterna o recorte da análise: Consolidado (todas as unidades), por Unidade ou por Departamento (unidade × departamento). No Consolidado, instâncias multi-unidade multiplicam economia bruta, líquida e horas pelo nº de unidades ativas; nas visões Unidade/Departamento o fator é 1.",
    competencia:
      "Escolhe um mês (competência) e preenche o período automaticamente. Ao ajustar as datas para meses diferentes, a competência fica em branco.",
    dateStart: "Início do período analisado (competência mensal). Filtra economias, custos e horas.",
    dateEnd: "Fim do período analisado. O recorte considera as competências entre a data inicial e a final.",
    unidade:
      "Restringe a análise a uma ou mais unidades operacionais. Habilitado nas visões Unidade e Departamento.",
    setor:
      "Restringe a análise a um ou mais departamentos das unidades selecionadas. Disponível apenas na visão Departamento.",
    alerts:
      "Processos com pelo menos 3 meses consecutivos de economia líquida negativa no recorte filtrado — sinal de atenção.",
    kpis: {
      economiaLiquida:
        "Economia líquida do recorte: economia bruta menos os custos (investimentos e rateio de recursos) no período. Instâncias «todas as unidades ativas» multiplicam só a economia operacional no Consolidado (não investimento nem recursos).",
      economiaBruta:
        "Ganho bruto estimado no período, antes de descontar custos. No Consolidado, instâncias multi-unidade contam uma vez por unidade ativa cadastrada.",
      solucoes:
        "Melhorias (instâncias) com revisão comparável ativa (melhoria, automação ou correção) no recorte de visão — snapshot do cadastro, independente do período filtrado.",
      horas:
        "Total de horas de trabalho economizadas no período no recorte. Instâncias multi-unidade multiplicam horas no Consolidado pelo nº de unidades ativas.",
      roi:
        "Retorno sobre o investimento: economia líquida dividida pelo investimento total do recorte.",
      investimento:
        "Investimento total do recorte: aportes e custos de recursos apropriados no período.",
    },
    charts: {
      savings:
        "Série por competência: economia bruta e investimento no recorte (ou horas economizadas, conforme o seletor do gráfico).",
      topGross:
        "Processos com maior economia bruta diária no período — ranking dos principais contribuintes.",
      topHours:
        "Processos que mais economizaram horas por dia no período selecionado.",
      familia:
        "Consolida a economia e o investimento por família de processo (agrupador) no recorte.",
      processos:
        "Lista dos processos que compõem os números do recorte, com economia, custo e ROI por processo.",
    },
  },
  filiais: {
    codigo:
      "Código da unidade no ERP (TOTVS), ex.: 01, 02. Não muda após criado — identifica a unidade nas integrações.",
    nome: "Nome exibido da unidade nas telas e relatórios (ex.: Santa Catarina).",
    status:
      "Unidades ativas aparecem nos formulários de departamentos, processos e no filtro do dashboard. Inativas ficam ocultas.",
    incluirInativas: "Mostra também unidades desativadas na listagem do catálogo.",
  },
  setores: {
    codigo: "Identificador do departamento (ex.: engenharia, qualidade). Não muda após criado.",
    nome: "Nome exibido do departamento nas telas e relatórios.",
    unidadesVinculadas:
      "Unidades em que este departamento existe. Um departamento só pode ser usado em processos das unidades vinculadas.",
    status: "Departamentos ativos e vinculados à unidade aparecem nos formulários de processo.",
    filtroUnidade: "Filtra o catálogo para exibir apenas departamentos vinculados à unidade escolhida.",
  },
  processos: {
    codigo: "Código gerado automaticamente ao criar o processo (PROC-XXXX).",
    nome: "Nome do processo-mestre monitorado no Transformômetro.",
    familia:
      "Agrupador do processo (ex.: ferramenta ou tema). Usado para consolidar a economia por família no dashboard.",
    agrupadorFerramenta: "Ferramenta ou plataforma principal (ex.: ChatGPT, Power Automate).",
    gestor: "Responsável pelo processo ou pela iniciativa de transformação.",
    objetivo: "Objetivo de negócio do processo — contexto para relatórios.",
    descricao: "Descrição livre do processo e do escopo operacional.",
    unidade:
      "Unidades onde o processo-mestre se aplica. Marque uma ou mais, ou «Todas as unidades ativas».",
    setor: "Departamentos envolvidos no escopo do processo-mestre.",
    status:
      "Processos ativos entram no dashboard. Descontinuado e Em implantação ajudam a controlar o ciclo de vida.",
    filtroUnidade: "Filtra a lista de processos por unidade (aplicado na API).",
    filtroStatus: "Filtra processos pelo status operacional.",
    busca: "Busca por código, nome, família ou agrupador de ferramenta.",
    timeline:
      "Histórico auditado de alterações neste processo e entidades vinculadas (mapeamento WBS, diagramas, melhorias, revisões, medições, investimentos e recursos).",
    timelineFilter: "Restringe a linha do tempo por tipo de entidade alterada.",
    diagramaMacro:
      "Mapa canônico do fluxo end-to-end do processo-mestre. Nós com ID estável são reutilizados nas melhorias e revisões.",
    arquivos:
      "Documentos de referência do processo-mestre — POP, instruções, planilhas e links úteis (independente das evidências por revisão).",
    arquivoUrl: "Endereço web externo do documento (SharePoint, drive, repositório…).",
    arquivoDescription: "Rótulo curto para identificar o arquivo na grade.",
    preenchimento:
      "Checklist do cadastro completo: dados mestre, melhorias, diagrama macro, baseline, melhoria comparável e medição com competências registradas.",
    preenchimentoLista:
      "Mesmo checklist do detalhe do processo: dados mestre, melhorias, mapeamento, diagrama macro, baseline, melhoria e medição.",
    modosVisualizacao:
      "Alterne entre ícones grandes (só título), ícones médios (+ código e meta), lista (+ status e preenchimento) e tabela detalhada.",
    ordenacaoCampo: "Campo usado para ordenar a lista em todos os modos de visualização.",
    ordenacaoDirecao: "Menor → maior (A–Z, 0–100) ou Maior → menor (Z–A, 100–0).",
  },
  decomposition: {
    mapeamento:
      "Árvore WBS do macroprocesso — processos-chave, tarefas e sub-tarefas. Fonte da planilha de mapeamento e export CSV.",
    escopoInstancia:
      "Selecione quais processos-chave desta melhoria executa ou aprimora.",
    contextoInstancia:
      "Metadados operacionais extras — responsável local, rollout e observações complementares.",
    contextoResponsavel:
      "Ponto focal operacional desta instância para rollout, dúvidas e acompanhamento local.",
    contextoContato: "Telefone, e-mail ou canal preferencial do responsável local.",
    contextoObservacoesRollout:
      "Notas sobre implantação, dependências, restrições locais ou plano de comunicação.",
    mapeamentoRevisao:
      "Overlay textual as-is/to-be sobre o escopo WBS — rótulos e descrições da revisão.",
    arvoreVazia:
      "Nenhum processo-chave cadastrado. Use + Processo-chave ou «Sugerir do fluxo» para começar.",
  },
  instancias: {
    escopo:
      "Cada melhoria aplica o processo a unidades e departamentos. Várias melhorias podem compartilhar a mesma unidade e os mesmos departamentos — cada cadastro é um foco distinto de transformação.",
    resumo: "Oportunidade ou objetivo desta melhoria neste recorte do processo.",
    responsavel: "Gestor ou patrocinador local responsável pela implantação.",
    fase: "Fase de rollout: planejado, piloto, implantado ou encerrado.",
    dataAlvo: "Data-alvo de go-live (planejamento). A data efetiva fica na revisão.",
    prioridade: "Prioridade operacional para acompanhamento e ranking.",
    todasUnidades:
      "Melhoria multi-unidade: uma única timeline válida para todas as unidades ativas (ex.: mesmo processo idêntico em SC e ES).",
    multiplicadorConsolidado:
      "No dashboard (visão Consolidado), economia bruta, economia líquida e horas desta instância são multiplicadas pelo número de unidades ativas cadastradas. Investimento único, custo recorrente e recursos compartilhados não multiplicam. Na visão por Unidade ou Departamento, o fator é sempre 1.",
    colunaUnidade:
      "Unidade operacional da instância. «Todas as unidades ativas» indica instância multi-unidade — ver balão para o efeito no dashboard consolidado.",
    unidades:
      "Marque as unidades da instância. No cadastro, criamos uma instância por unidade marcada; na edição, unidades extras viram novas instâncias.",
    setores:
      "Departamentos envolvidos nesta melhoria. Podem repetir entre melhorias — use o título e o resumo para diferenciá-las.",
    status: "Melhorias inativas deixam de contribuir para os números do dashboard.",
    rotulo:
      "Título curto da melhoria, exibido na listagem, na linha do tempo e nos relatórios. Use para distinguir melhorias no mesmo par unidade × departamento (ex.: «Automação do fechamento — Q2/2026»).",
    diagramaEscopo:
      "Selecione quais nós do diagrama macro desta instância são relevantes neste ambiente operacional.",
  },
  revisao: {
    versao: "Identificador da revisão (ex.: 1.0.0). Deve ser único dentro da instância.",
    cenario:
      "Linha de base = as-is (sem referência). Demais cenários exigem escolher contra qual revisão comparar.",
    referenciaComparacao:
      "Revisão anterior usada como referência para economia, payback e diffs de diagrama/WBS. A baseline não precisa deste campo.",
    inicioVigencia: "Data a partir da qual a revisão passa a valer para medições e dashboard.",
    implantacao: "Data em que a solução foi implantada — usada em relatórios de implantação.",
    fimVigencia: "Encerra a revisão. Revisões com fim não podem ser marcadas como ativas.",
    revisaoAtiva: "Indica qual revisão é a vigente na instância (exceto baseline).",
    descricao: "Resumo do que a revisão representa (ex.: automação do fechamento).",
    motivo: "Motivo da criação ou alteração (ex.: nova ferramenta, mudança de escopo).",
    observacoes: "Notas complementares sobre a revisão.",
    volumeMensal: "Volume de execuções ou transações por mês usado no cálculo de economia.",
    tempoMedio: "Tempo médio de execução por unidade, em minutos.",
    tempoRetrabalho: "Tempo médio de retrabalho por unidade, em minutos.",
    custoHoraMo: "Custo hora da mão de obra usado para converter tempo em R$.",
    percentualRetrabalho: "Percentual do volume que exige retrabalho.",
    percentualErro: "Percentual de erros ou refugos no volume.",
    quantidadeErros: "Quantidade absoluta de erros por mês (alternativa ao percentual).",
    custoUnitarioErro: "Custo médio para corrigir um erro.",
    custoUnitarioRetrabalho: "Custo médio de uma unidade de retrabalho.",
    outrosDesperdicios: "Outros custos mensais de desperdício não cobertos acima (R$/mês).",
    mesReferencia: "Competência de referência da medição (mês/ano).",
    medicaoObservacoes: "Notas sobre a origem ou qualidade dos dados de medição.",
    rateioDiag:
      "Verifica se o rateio de recursos compartilhados não excede a economia bruta da revisão.",
    evidencias:
      "Anexos (PDF, imagem, planilha) ou links que comprovam a melhoria desta revisão.",
    diagramaRevisao:
      "Estado visual as-is (baseline) ou to-be (melhoria) sobre o escopo da instância — overlay sobre o diagrama macro.",
    evidenceUrl: "Endereço web externo da evidência (documento, vídeo, repositório…).",
    evidenceDescription: "Texto curto que identifica a evidência na lista.",
    comparativoChart:
      "Compara economia bruta, líquida, investimentos, recursos compartilhados e horas entre as revisões desta instância.",
    comparativoTable:
      "Tabela com os mesmos indicadores do gráfico, incluindo competência e meses com dados.",
  },
  matriz: {
    titulo:
      "Posiciona a revisão em impacto (benefício) versus esforço (custo/complexidade) frente às demais revisões comparáveis da mesma melhoria.",
    modo:
      "Automático usa medição, investimentos e comparativo; Híbrido combina dados com percepção qualitativa; Manual prioriza os ajustes informados.",
    confianca:
      "Indica a robustez do score automático conforme completude de medição, referência, investimentos e recursos.",
    quadrantes:
      "Ganho rápido = alto impacto e baixo esforço; Estratégico = alto em ambos; Complementar = baixo em ambos; Reavaliar = baixo impacto e alto esforço.",
    modoLabel: "Modo de cálculo",
    confiancaLabel: "Confiança do score",
    posicaoAtual:
      "Impacto e esforço (0–100) desta revisão e quadrante correspondente na matriz.",
    liquidaAnualResumo:
      "Economia líquida anualizada com base na medição, investimentos e recursos rateados.",
    rateioExcedeGanho:
      "O rateio de recursos compartilhados excede a economia bruta desta revisão.",
    impactoScore: "Score de benefício (0–100) — quanto a revisão gera de ganho.",
    esforcoScore: "Score de esforço (0–100) — custo/complexidade de implantação e adoção.",
    quadranteColuna: "Classificação na matriz impacto × esforço.",
    liquidaAnualColuna: "Economia líquida projetada para 12 meses.",
    revisaoAtivaColuna: "Revisão marcada como vigente na melhoria.",
    rankingTabela: "Ranking das revisões por prioridade (impacto alto e esforço baixo primeiro).",
    ajustesManuais:
      "Campos qualitativos e observações usados nos modos Híbrido e Manual. No Automático ficam colapsados.",
    impactoQualitativo: "Percepção de benefício quando a economia ainda não está consolidada (escala 1–5).",
    esforcoQualitativo: "Percepção de esforço de implantação e adoção (escala 1–5).",
    alinhamentoEstrategico: "Quão alinhada a revisão está às prioridades estratégicas (escala 1–5).",
    dependenciasExternas: "Dependência de TI, fornecedor ou fatores externos (escala 1–5).",
    pessoasAfetadas: "Estimativa de colaboradores impactados pela mudança.",
    observacao: "Contexto adicional para priorização — visível só na revisão.",
    bannerBaixaConfianca:
      "Complete medição, referência de comparação e investimentos ou recursos para elevar a confiança do score automático.",
    semDados: "Sem revisões comparáveis para exibir nesta melhoria.",
    graficoAria: "Matriz impacto por esforço das revisões da melhoria",
    resumoEconomia: "Economia líquida anual",
    modoAutomaticoHint: "Selecione Híbrido ou Manual para salvar ajustes qualitativos.",
    instanciaPriorizacao:
      "Compara todas as revisões desta melhoria no mesmo gráfico impacto × esforço e ranking por prioridade.",
    graficoInstanciaAria: "Matriz impacto por esforço de todas as revisões da melhoria",
    processoPriorizacao:
      "Visão consolidada do processo-mestre: todas as melhorias e revisões comparáveis no mesmo scatter (normalização entre melhorias).",
    semDadosProcesso: "Sem revisões comparáveis em nenhuma melhoria deste processo.",
    graficoProcessoAria: "Matriz impacto por esforço de todas as melhorias do processo",
    rankingTabelaProcesso: "Ranking global das revisões do processo (impacto alto e esforço baixo primeiro).",
    melhoriaColuna: "Melhoria operacional (instância) à qual a revisão pertence.",
    exportarPng: "Baixa o gráfico da matriz como imagem PNG.",
  },
  investimentos: {
    tipo: "Natureza do investimento (software, equipamento, horas, etc.).",
    descricao: "Descrição do item investido.",
    quantidade: "Quantidade de unidades.",
    valorUnitario: "Valor unitário em R$.",
    recorrencia: "Único ou recorrente — define como o custo entra no ROI.",
    categoria: "Agrupador opcional para relatórios.",
    data: "Data do investimento ou início da vigência.",
    mesesVigencia: "Meses em que um investimento único é diluído no cálculo mensal.",
    total: "Valor total do item (quantidade × unitário).",
  },
  recursos: {
    nome: "Nome da licença, assinatura ou ferramenta compartilhada.",
    categoria: "Agrupador opcional (ex.: IA, ERP, infraestrutura).",
    fornecedor: "Fornecedor ou editor (ex.: OpenAI, Microsoft).",
    recorrencia: "Periodicidade de cobrança cadastrada (mensal, anual…).",
    status: "Recursos inativos não aparecem para novos vínculos.",
    centroCusto: "Centro de custo contábil opcional.",
    inicioVigencia: "Data em que o recurso passa a existir no catálogo.",
    fimVigencia: "Data de encerramento — vínculos posteriores não são permitidos.",
    escopo:
      "Alcance do custo do recurso: Empresa (pool global), Unidade (mesma unidade da instância) ou Departamento (unidade × departamento).",
    criterioRateio:
      "Como o custo do recurso é dividido entre os vínculos: igualitário, por revisões ativas ou por peso do vínculo.",
    baseCompetencia:
      "Como o custo é apropriado no mês: cheio (valor integral) ou proporcional aos dias de vigência.",
    tipoCusto: "Natureza do custo do recurso: fixo, variável, assinatura ou licença.",
    peso: "Peso do vínculo no rateio quando o critério é 'por peso'. Valores maiores absorvem mais custo.",
    custosHistorico:
      "Histórico de valores mensais por período. O dashboard usa o vigente em cada competência.",
    reajusteValor: "Novo valor mensal a partir da data informada.",
    reajusteDesde: "Competência a partir da qual o novo valor passa a valer.",
    vinculoInicio: "Data em que o processo passou a usar o recurso nesta revisão.",
    vinculoFim: "Data em que o uso do recurso nesta revisão encerrou.",
    vinculoObservacoes: "Contexto do uso do recurso nesta revisão específica.",
    catalogoVinculo: "Recurso do catálogo global a ser associado à revisão.",
    novoRecursoCatalogo: "Cadastra um recurso novo no catálogo e seleciona para vínculo.",
    vinculoAtivo: "Vínculo considerado no rateio mensal quando marcado como ativo.",
  },
  diagramEditor: {
    usoGeral:
      "Adicione nós pela paleta (entram na faixa ativa). Selecione vários elementos arrastando na área de desenho para desenhar a caixa de seleção, ou Ctrl+clique para acrescentar à seleção. Use os ícones empilhados no canto inferior direito (excluir, copiar, colar, duplicar, tipo de conexão). Copiar grava na memória do editor; Colar insere a cópia com deslocamento (Ctrl+V). Duplicar copia e cola de uma vez. Atalhos: Ctrl+C copiar, Ctrl+V colar, Ctrl+D duplicar, Delete excluir. Setas ← ↑ → ↓ reposicionam a seleção em passos finos. Duplo clique no texto do nó, faixa ou rótulo da seta para editar inline (Enter confirma, Esc cancela). Use Layout automático para reorganizar o fluxo.",
    nodes: {
      start: "Evento de início do fluxo (círculo). Todo diagrama deve ter ao menos um início.",
      process: "Atividade ou tarefa manual/automática (retângulo). Representa trabalho executado no processo.",
      decision: "Desvio exclusivo (losango). Use duas ou mais saídas rotuladas (ex.: Sim/Não).",
      document: "Documento ou artefato produzido ou consumido na etapa.",
      data: "Armazenamento ou registro persistente (cilindro BPMN) referenciado no fluxo.",
      subprocess: "Subprocesso encapsulado — etapa composta por fluxo interno.",
      end: "Evento de fim (círculo duplo). Todo caminho deve terminar em um fim.",
      comment: "Nota explicativa — não participa da lógica do fluxo.",
    },
    addLane:
      "Adiciona uma faixa horizontal para separar papéis ou áreas (ex.: Comercial, Engenharia). Novos nós entram na faixa selecionada.",
    autoLayout:
      "Reorganiza automaticamente nós e setas em grade legível, respeitando as faixas. Útil após adicionar muitos elementos.",
    templateLinear: "Substitui o diagrama por um fluxo linear simples (início → atividades → fim) para começar rápido.",
    templateDecision:
      "Modelo com bifurcação: início, atividade, decisão Sim/Não e dois caminhos convergindo no fim.",
    templateSwimlanes:
      "Exemplo BPMN com duas faixas (Comercial e Engenharia), transferência entre áreas e desvios — ponto de partida para processos entre departamentos.",
    laneSelect:
      "Faixa ativa para inserir novos nós da paleta. Clique no cabeçalho da faixa na área de desenho, use os chips aqui ou arraste o cabeçalho para reordenar faixas.",
    laneRename:
      "Duplo clique no nome da faixa na área de desenho para editar inline (Enter confirma, Esc cancela), como nos demais nós.",
    laneRemove:
      "Remove a faixa ativa. Com mais de uma faixa, os nós são realocados na restante; removendo a última, o diagrama volta ao desenho simples (sem faixas).",
    canvasTab: "Editor visual interativo — arraste, conecte e edite o diagrama.",
    mermaidTab:
      "Edite o código Mermaid ou visualize o diagrama renderizado. Use «Aplicar ao desenho» para converter em editor visual, ou «Atualizar do desenho» para sincronizar com o desenho atual.",
    fullscreen:
      "Abre o editor em tela cheia com paleta, ferramentas e ações de salvamento. Pressione Esc ou use «Sair da tela cheia» para voltar.",
    selectionDelete:
      "Remove nós e setas selecionados. Sem seleção na área de desenho, exclui a faixa ativa (com confirmação). Atalho: Delete ou Backspace para nós/setas.",
    selectionMove:
      "Selecione um ou mais nós (caixa de seleção na área de desenho ou Ctrl+clique) e arraste para reposicionar em grupo. Teclas ← ↑ → ↓ ajustam a posição em passos finos (8 px).",
    selectionCopy:
      "Copia os nós selecionados (e setas entre eles) para a memória interna do editor. Use Colar ou Ctrl+V para inserir na área de desenho. Atalho: Ctrl+C.",
    selectionPaste:
      "Insere a última cópia na área de desenho, com deslocamento automático a cada colagem. Atalho: Ctrl+V. Só fica disponível após Copiar.",
    selectionDuplicate:
      "Copia e cola de uma vez os nós selecionados, com deslocamento automático e conexões internas preservadas. Atalho: Ctrl+D.",
    selectionEdgeKind:
      "Com setas selecionadas, alterna o tipo BPMN: sequência → fluxo de mensagem → associação.",
  },
  dataTransfer: {
    export:
      "Gera um pacote .tmbackup.zip com cadastro, diagramas, mapeamento WBS, metadados e arquivos de evidência. O JSON inclui só dados estruturados (sem anexos binários).",
    importFormat:
      "A importação detecta automaticamente backup legado (unidade/departamento nos processos) ou Playbook 18 (instâncias). Arquivos fora desse padrão são rejeitados.",
    previewEntidade: "Tipo de registro no backup (unidades, processos, revisões…).",
    previewNoArquivo: "Quantidade de registros deste tipo no arquivo importado.",
    previewInserir: "Registros novos que serão criados no banco.",
    previewAtualizar: "Registros existentes que serão sobrescritos pelo backup.",
  },
} as const;
