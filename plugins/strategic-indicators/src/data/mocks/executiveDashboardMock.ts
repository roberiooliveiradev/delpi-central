export type DepartmentSummary = {
  id: string;
  name: string;
  shortName: string;
  weightPct: number;
  score: number;
  contribution: number;
  strategicSummary: string;
  keyIndicators: string[];
  executiveGoal: string;
};

export type ExecutiveDashboardData = {
  igd: number;
  igdExact: number;
  classification: string;
  departments: DepartmentSummary[];
};

export const executiveDashboardMock: ExecutiveDashboardData = {
  igd: 7.8,
  igdExact: 7.768,
  classification: "Satisfatório com Alertas",
  departments: [
    {
      id: "financial",
      name: "Financeiro",
      shortName: "FIN",
      weightPct: 15,
      score: 7.8,
      contribution: 1.17,
      strategicSummary:
        "Geração de resultado operacional, eficiência da estrutura e fluxo de caixa.",
      keyIndicators: [
        "EBITDA / Receita Operacional",
        "% Custos Fixos / Receita Operacional",
        "Prazo Médio de Recebimento (PMR)",
      ],
      executiveGoal: "Meta-chave 2026: EBITDA 13,0%",
    },
    {
      id: "hr",
      name: "RH",
      shortName: "RH",
      weightPct: 15,
      score: 8.0,
      contribution: 1.2,
      strategicSummary:
        "Engajamento, retenção, desenvolvimento individual e capacitação contínua.",
      keyIndicators: [
        "Absenteísmo",
        "Turnover",
        "Satisfação Interna",
      ],
      executiveGoal: "Meta-chave 2026: Turnover 1,5% ao mês",
    },
    {
      id: "commercial",
      name: "Comercial",
      shortName: "COM",
      weightPct: 17,
      score: 8.2,
      contribution: 1.394,
      strategicSummary:
        "Receita, conversão de negócios e expansão da base de clientes.",
      keyIndicators: [
        "ROL Matriz / Meta",
        "Taxa de Fechamento de Negócios",
        "Número de Novos Clientes",
      ],
      executiveGoal: "Meta-chave 2026: Fechamento 30%",
    },
    {
      id: "production",
      name: "Produção",
      shortName: "PRD",
      weightPct: 17,
      score: 7.8,
      contribution: 1.326,
      strategicSummary:
        "Eficiência produtiva, uso dos ativos e cumprimento do prazo ao cliente.",
      keyIndicators: [
        "Custo MOD / ROL",
        "OEE",
        "OTD",
      ],
      executiveGoal: "Meta-chave 2026: OEE 70%",
    },
    {
      id: "quality",
      name: "Qualidade",
      shortName: "QLD",
      weightPct: 14,
      score: 7.4,
      contribution: 1.036,
      strategicSummary:
        "Falhas internas e externas, disciplina operacional e ganhos com melhoria contínua.",
      keyIndicators: [
        "PPM Interno",
        "PPM Externo",
        "Nota Auditoria 5S",
      ],
      executiveGoal: "Meta-chave 2026: PPM Externo 1.100",
    },
    {
      id: "supplies",
      name: "Suprimentos",
      shortName: "SUP",
      weightPct: 12,
      score: 7.1,
      contribution: 0.852,
      strategicSummary:
        "Eficiência em compras, estoque e negociações com fornecedores.",
      keyIndicators: [
        "CPV Consolidado",
        "OTD Compras",
        "Giro de Estoque",
      ],
      executiveGoal: "Meta-chave 2026: OTD Compras 92%",
    },
    {
      id: "engineering",
      name: "Engenharia",
      shortName: "ENG",
      weightPct: 10,
      score: 7.9,
      contribution: 0.79,
      strategicSummary:
        "Entrega no prazo e geração de valor via inovação e digitalização.",
      keyIndicators: [
        "% Projetos Concluídos no Prazo",
        "Ganhos Financeiros do TRANSFORMA+ DELPI",
      ],
      executiveGoal: "Meta-chave 2026: 95% no prazo",
    },
  ],
};