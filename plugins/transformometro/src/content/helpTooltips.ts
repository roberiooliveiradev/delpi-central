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
    unidades: "Unidades em que o setor ou vínculo está ativo.",
    setor: "Setor operacional dentro da unidade.",
    setores: "Setores vinculados à instância operacional.",
    status: "Situação do cadastro — ativos entram nos formulários e no dashboard.",
    rotulo: "Texto livre para identificar a instância (opcional).",
    versao: "Número ou rótulo da revisão do processo (ex.: 1.0.0, 2.1).",
    cenario: "Baseline (referência) ou melhoria (pós-transformação).",
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
      "Alterna o recorte da análise: Consolidado (todas as unidades), por Unidade ou por Departamento (unidade × setor). No Consolidado, instâncias multi-unidade multiplicam economia bruta, líquida e horas pelo nº de unidades ativas; nas visões Unidade/Departamento o fator é 1.",
    competencia:
      "Escolhe um mês (competência) e preenche o período automaticamente. Ao ajustar as datas para meses diferentes, a competência fica em branco.",
    dateStart: "Início do período analisado (competência mensal). Filtra economias, custos e horas.",
    dateEnd: "Fim do período analisado. O recorte considera as competências entre a data inicial e a final.",
    unidade:
      "Restringe a análise a uma ou mais unidades operacionais. Habilitado nas visões Unidade e Departamento.",
    setor:
      "Restringe a análise a um ou mais setores das unidades selecionadas. Disponível apenas na visão Departamento.",
    alerts:
      "Processos com pelo menos 3 meses consecutivos de economia líquida negativa no recorte filtrado — sinal de atenção.",
    kpis: {
      economiaLiquida:
        "Economia líquida do recorte: economia bruta menos os custos (investimentos e rateio de recursos) no período. Instâncias «todas as unidades ativas» multiplicam só a economia operacional no Consolidado (não investimento nem recursos).",
      economiaBruta:
        "Ganho bruto estimado no período, antes de descontar custos. No Consolidado, instâncias multi-unidade contam uma vez por unidade ativa cadastrada.",
      solucoes:
        "Quantidade de soluções implementadas que compõem o recorte.",
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
      "Unidades ativas aparecem nos formulários de setores, processos e no filtro do dashboard. Inativas ficam ocultas.",
    incluirInativas: "Mostra também unidades desativadas na listagem do catálogo.",
  },
  setores: {
    codigo: "Identificador do setor (ex.: engenharia, qualidade). Não muda após criado.",
    nome: "Nome exibido do setor nas telas e relatórios.",
    unidadesVinculadas:
      "Unidades em que este setor existe. Um setor só pode ser usado em processos das unidades vinculadas.",
    status: "Setores ativos e vinculados à unidade aparecem nos formulários de processo.",
    filtroUnidade: "Filtra o catálogo para exibir apenas setores vinculados à unidade escolhida.",
  },
  processos: {
    codigo: "Código gerado automaticamente ao criar o processo (PROC-XXXX).",
    nome: "Nome do processo (mestre). A unidade e o setor entram na instância operacional.",
    familia:
      "Agrupador do processo (ex.: ferramenta ou tema). Usado para consolidar a economia por família no dashboard.",
    agrupadorFerramenta: "Ferramenta ou plataforma principal (ex.: ChatGPT, Power Automate).",
    gestor: "Responsável pelo processo ou pela iniciativa de transformação.",
    objetivo: "Objetivo de negócio do processo — contexto para relatórios.",
    descricao: "Descrição livre do processo e do escopo operacional.",
    unidade: "Unidade da primeira instância operacional criada junto com o processo.",
    setor: "Setor da primeira instância operacional, dentro da unidade escolhida.",
    status:
      "Processos ativos entram no dashboard. Descontinuado e Em implantação ajudam a controlar o ciclo de vida.",
    filtroUnidade: "Filtra a lista de processos por unidade (aplicado na API).",
    filtroStatus: "Filtra processos pelo status operacional.",
    busca: "Busca por código, nome, família ou agrupador de ferramenta.",
    timeline:
      "Histórico auditado de alterações neste processo e entidades vinculadas (instâncias, revisões, medições, investimentos e recursos).",
    timelineFilter: "Restringe a linha do tempo por tipo de entidade alterada.",
  },
  instancias: {
    escopo:
      "Cada instância pertence a uma unidade (ou a todas as ativas, instância multi-unidade) e amarra um ou mais setores. As revisões ficam na instância — baseline e medições são independentes por ambiente.",
    todasUnidades:
      "Instância multi-unidade: uma única timeline válida para todas as unidades ativas (ex.: mesmo processo idêntico em SC e ES). Evita duplicar cadastro por unidade quando baseline, volumes e investimentos são iguais.",
    multiplicadorConsolidado:
      "No dashboard (visão Consolidado), economia bruta, economia líquida e horas desta instância são multiplicadas pelo número de unidades ativas cadastradas. Investimento único, custo recorrente e recursos compartilhados não multiplicam. Na visão por Unidade ou Departamento, o fator é sempre 1.",
    colunaUnidade:
      "Unidade operacional da instância. «Todas as unidades ativas» indica instância multi-unidade — ver balão para o efeito no dashboard consolidado.",
    unidades:
      "Marque as unidades da instância. No cadastro, criamos uma instância por unidade marcada; na edição, unidades extras viram novas instâncias.",
    setores:
      "Setores vinculados à instância. Setores já usados por outra instância na mesma unidade aparecem como 'em uso' e ficam desabilitados.",
    status: "Instâncias inativas deixam de contribuir para os números do dashboard.",
    rotulo: "Texto livre para identificar a instância (ex.: 'Matriz — rollout Q2'). Opcional.",
  },
  revisao: {
    versao: "Identificador da revisão (ex.: 1.0.0). Deve ser único dentro da instância.",
    cenario: "Baseline = referência antes da melhoria; melhoria = cenário pós-transformação.",
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
    evidenceUrl: "Endereço web externo da evidência (documento, vídeo, repositório…).",
    evidenceDescription: "Texto curto que identifica a evidência na lista.",
    comparativoChart:
      "Compara economia bruta, líquida, investimentos, recursos compartilhados e horas entre as revisões desta instância.",
    comparativoTable:
      "Tabela com os mesmos indicadores do gráfico, incluindo competência e meses com dados.",
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
      "Alcance do custo do recurso: Empresa (pool global), Unidade (mesma unidade da instância) ou Departamento (unidade × setor).",
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
  dataTransfer: {
    export:
      "Gera um backup em JSON com todo o cadastro (unidades, setores, processos, instâncias e revisões).",
    importFormat:
      "A importação detecta automaticamente backup legado (unidade/setor nos processos) ou Playbook 18 (instâncias). Arquivos fora desse padrão são rejeitados.",
    previewEntidade: "Tipo de registro no backup (unidades, processos, revisões…).",
    previewNoArquivo: "Quantidade de registros deste tipo no arquivo importado.",
    previewInserir: "Registros novos que serão criados no banco.",
    previewAtualizar: "Registros existentes que serão sobrescritos pelo backup.",
  },
} as const;
