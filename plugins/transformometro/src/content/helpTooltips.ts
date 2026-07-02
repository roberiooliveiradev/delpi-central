/**
 * Textos dos balões explicativos (HelpTooltip) do Transformômetro.
 * Centralizados por tela/domínio — não vêm da API. Mesmo padrão do
 * dashboard-commercial (content/helpTooltips.ts).
 */
export const TM_HELP_TOOLTIPS = {
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
    nome: "Nome do processo (mestre). A unidade e o setor entram na primeira instância operacional.",
    familia:
      "Agrupador do processo (ex.: ferramenta ou tema). Usado para consolidar a economia por família no dashboard.",
    unidade: "Unidade da primeira instância operacional criada junto com o processo.",
    setor: "Setor da primeira instância operacional, dentro da unidade escolhida.",
    status:
      "Processos ativos entram no dashboard. Descontinuado e Em implantação ajudam a controlar o ciclo de vida.",
    filtroUnidade: "Filtra a lista de processos por unidade (aplicado na API).",
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
  recursos: {
    escopo:
      "Alcance do custo do recurso: Empresa (pool global), Unidade (mesma unidade da instância) ou Departamento (unidade × setor).",
    criterioRateio:
      "Como o custo do recurso é dividido entre os vínculos: igualitário, por revisões ativas ou por peso do vínculo.",
    baseCompetencia:
      "Como o custo é apropriado no mês: cheio (valor integral) ou proporcional aos dias de vigência.",
    tipoCusto: "Natureza do custo do recurso: fixo, variável, assinatura ou licença.",
    peso: "Peso do vínculo no rateio quando o critério é 'por peso'. Valores maiores absorvem mais custo.",
  },
  dataTransfer: {
    export:
      "Gera um backup em JSON com todo o cadastro (unidades, setores, processos, instâncias e revisões).",
    importFormat:
      "Escolha o formato do arquivo: automático (a API detecta), legado (JSON antigo) ou Playbook 18 (backup com instâncias).",
  },
} as const;
