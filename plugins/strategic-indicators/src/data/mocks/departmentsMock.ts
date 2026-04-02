export type DepartmentIndicator = {
  id: string;
  name: string;
  weightPct: number;
  goal2026: string;
  strategicDescription: string;
};

export type DepartmentDetails = {
  id: string;
  name: string;
  shortName: string;
  weightInIgd: number;
  score: number;
  classification: string;
  strategicSummary: string;
  indicators: DepartmentIndicator[];
};

export const departmentsMock: DepartmentDetails[] = [
  {
    id: "financial",
    name: "Financeiro",
    shortName: "FIN",
    weightInIgd: 15,
    score: 7.8,
    classification: "Satisfatório com Alertas",
    strategicSummary:
      "O IDD Financeiro mede geração de resultado operacional, eficiência estrutural e fluxo de caixa.",
    indicators: [
      {
        id: "ebitda",
        name: "EBITDA / Receita Operacional",
        weightPct: 40,
        goal2026: "13,0%",
        strategicDescription:
          "Mede a capacidade de geração de resultado operacional.",
      },
      {
        id: "fixed-costs",
        name: "% Custos Fixos / Receita Operacional",
        weightPct: 30,
        goal2026: "14,0%",
        strategicDescription:
          "Indica eficiência e estrutura enxuta.",
      },
      {
        id: "pmr",
        name: "Prazo Médio de Recebimento (PMR)",
        weightPct: 30,
        goal2026: "39 dias",
        strategicDescription:
          "Indica eficiência de recebimentos e fluxo de caixa.",
      },
    ],
  },
  {
    id: "hr",
    name: "RH",
    shortName: "RH",
    weightInIgd: 15,
    score: 8.0,
    classification: "Alto Desempenho",
    strategicSummary:
      "O IDD RH mede engajamento, retenção, desenvolvimento individual e capacitação contínua.",
    indicators: [
      {
        id: "absenteeism",
        name: "Absenteísmo",
        weightPct: 20,
        goal2026: "2,0%",
        strategicDescription: "Mede engajamento e bem-estar.",
      },
      {
        id: "turnover",
        name: "Turnover (Rotatividade)",
        weightPct: 20,
        goal2026: "1,5% ao mês",
        strategicDescription: "Mede retenção e estabilidade.",
      },
      {
        id: "satisfaction",
        name: "Satisfação Interna (Clima/Engajamento)",
        weightPct: 20,
        goal2026: "85% de satisfação",
        strategicDescription: "Reputação interna da cultura.",
      },
      {
        id: "pdi",
        name: "% de PDIs Ativos",
        weightPct: 20,
        goal2026: "100%",
        strategicDescription:
          "Estruturação de desenvolvimento individual.",
      },
      {
        id: "training",
        name: "Horas de Treinamento/Colaborador/mês",
        weightPct: 20,
        goal2026: "2 horas/mês",
        strategicDescription: "Investimento em formação e capacitação.",
      },
    ],
  },
  {
    id: "commercial",
    name: "Comercial",
    shortName: "COM",
    weightInIgd: 17,
    score: 8.2,
    classification: "Alto Desempenho",
    strategicSummary:
      "O IDD Comercial mede receita, conversão de negócios e expansão da base de clientes.",
    indicators: [
      {
        id: "rol-matrix",
        name: "ROL Matriz / Meta",
        weightPct: 25,
        goal2026: "100%",
        strategicDescription:
          "Atingimento da receita da unidade matriz.",
      },
      {
        id: "rol-branch",
        name: "ROL Filial / Meta",
        weightPct: 25,
        goal2026: "100%",
        strategicDescription:
          "Atingimento da receita da unidade filial.",
      },
      {
        id: "closing-rate",
        name: "Taxa de Fechamento de Negócios",
        weightPct: 20,
        goal2026: "30%",
        strategicDescription: "Conversão de propostas em vendas.",
      },
      {
        id: "new-clients",
        name: "Número de Novos Clientes (média mensal)",
        weightPct: 15,
        goal2026: "10 novos/mês",
        strategicDescription: "Capacidade de abertura de mercado.",
      },
      {
        id: "new-rol",
        name: "% ROL de Novos Clientes",
        weightPct: 15,
        goal2026: "12%",
        strategicDescription:
          "Participação dos novos no total da receita.",
      },
    ],
  },
  {
    id: "production",
    name: "Produção",
    shortName: "PRD",
    weightInIgd: 17,
    score: 7.8,
    classification: "Satisfatório com Alertas",
    strategicSummary:
      "O IDD Produção mede eficiência produtiva, uso dos ativos e cumprimento do prazo ao cliente.",
    indicators: [
      {
        id: "direct-labor",
        name: "Custo Mão de Obra Direta / ROL",
        weightPct: 25,
        goal2026: "10,0%",
        strategicDescription: "Eficiência da mão de obra direta.",
      },
      {
        id: "production-costs",
        name: "Custos de Produção / ROL",
        weightPct: 20,
        goal2026: "32,0%",
        strategicDescription:
          "Controle de desperdícios e produtividade.",
      },
      {
        id: "depreciation",
        name: "Depreciação / ROL",
        weightPct: 10,
        goal2026: "1,5%",
        strategicDescription:
          "Uso racional da capacidade instalada.",
      },
      {
        id: "oee",
        name: "OEE (Eficiência Global dos Equip.)",
        weightPct: 20,
        goal2026: "70%",
        strategicDescription:
          "Utilização real dos ativos produtivos.",
      },
      {
        id: "otd",
        name: "OTD (Entrega no Prazo)",
        weightPct: 25,
        goal2026: "92%",
        strategicDescription:
          "Cumprimento do prazo prometido ao cliente.",
      },
    ],
  },
  {
    id: "quality",
    name: "Qualidade",
    shortName: "QLD",
    weightInIgd: 14,
    score: 7.4,
    classification: "Satisfatório com Alertas",
    strategicSummary:
      "O IDD Qualidade mede falhas internas e externas, disciplina operacional e ganhos com melhoria contínua.",
    indicators: [
      {
        id: "ppm-internal",
        name: "PPM Interno",
        weightPct: 20,
        goal2026: "1.400 PPM",
        strategicDescription:
          "Indicador de falhas detectadas internamente.",
      },
      {
        id: "ppm-external",
        name: "PPM Externo",
        weightPct: 30,
        goal2026: "1.100 PPM",
        strategicDescription:
          "Indicador de falhas detectadas pelo cliente.",
      },
      {
        id: "kaizen-ideas",
        name: "Ideias Aprovadas para Kaizen/mês",
        weightPct: 15,
        goal2026: "8 ideias/mês",
        strategicDescription:
          "Cultura de melhoria e participação.",
      },
      {
        id: "audit-5s",
        name: "Nota Auditoria 5S",
        weightPct: 15,
        goal2026: "80%",
        strategicDescription:
          "Padronização, organização e disciplina.",
      },
      {
        id: "kaizen-financial",
        name: "Ganhos Financeiros Kaizen/mês",
        weightPct: 20,
        goal2026: "R$ 4.500 (1º S), R$ 9.000 (2º S)",
        strategicDescription:
          "Impacto financeiro direto das melhorias Kaizen.",
      },
    ],
  },
  {
    id: "supplies",
    name: "Suprimentos",
    shortName: "SUP",
    weightInIgd: 12,
    score: 7.1,
    classification: "Satisfatório com Alertas",
    strategicSummary:
      "O IDD Suprimentos mede eficiência em compras, estoque e negociações com fornecedores.",
    indicators: [
      {
        id: "cpv",
        name: "CPV Consolidado (matriz e filial)",
        weightPct: 30,
        goal2026: "50,5%",
        strategicDescription:
          "Eficiência nas compras totais.",
      },
      {
        id: "otd-purchases",
        name: "OTD Consolidado de Compras",
        weightPct: 20,
        goal2026: "92%",
        strategicDescription:
          "Entregas dentro do prazo pelos fornecedores.",
      },
      {
        id: "stock-turnover",
        name: "Giro de Estoque Consolidado",
        weightPct: 20,
        goal2026: "1,95 mês",
        strategicDescription:
          "Rotatividade do estoque total.",
      },
      {
        id: "total-stock",
        name: "Valor Total do Estoque Consolidado",
        weightPct: 15,
        goal2026: "R$ 13.500.000,00",
        strategicDescription:
          "Estoque como capital parado.",
      },
      {
        id: "purchase-savings",
        name: "Economia em Negociações de Compras",
        weightPct: 15,
        goal2026: "R$ 20.000/mês",
        strategicDescription:
          "Eficiência em negociações e renegociações com fornecedores.",
      },
    ],
  },
  {
    id: "engineering",
    name: "Engenharia",
    shortName: "ENG",
    weightInIgd: 10,
    score: 7.9,
    classification: "Satisfatório com Alertas",
    strategicSummary:
      "O IDD Engenharia mede entrega no prazo e geração de valor via inovação e digitalização.",
    indicators: [
      {
        id: "projects-on-time",
        name: "% de Projetos Concluídos no Prazo",
        weightPct: 60,
        goal2026: "95%",
        strategicDescription:
          "Compromisso com entregas e gestão eficiente de escopo.",
      },
      {
        id: "transforma-more",
        name: "Ganhos Financeiros do TRANSFORMA+ DELPI",
        weightPct: 40,
        goal2026: "R$ 15.000/mês",
        strategicDescription:
          "Valor gerado por inovações e digitalização.",
      },
    ],
  },
];

export function getDepartmentById(departmentId: string) {
  return departmentsMock.find((department) => department.id === departmentId) ?? null;
}