export type SettingsWeightItem = {
  id: string;
  departmentName: string;
  weightPct: number;
  note: string;
};

export type SettingsGoalItem = {
  id: string;
  departmentName: string;
  headlineGoal: string;
  supportingFocus: string;
};

export type SettingsGovernanceItem = {
  id: string;
  label: string;
  value: string;
  observation: string;
};

export type SettingsParameterItem = {
  id: string;
  label: string;
  value: string;
  observation: string;
};

export type SettingsReadinessItem = {
  id: string;
  title: string;
  status: "ready" | "planned" | "mock";
  description: string;
};

export type SettingsDashboardData = {
  weights: SettingsWeightItem[];
  goals: SettingsGoalItem[];
  governance: SettingsGovernanceItem[];
  parameters: SettingsParameterItem[];
  readiness: SettingsReadinessItem[];
};

export const settingsMock: SettingsDashboardData = {
  weights: [
    {
      id: "financial",
      departmentName: "Financeiro",
      weightPct: 15,
      note: "Peso oficial do IGD para geração de resultado e fluxo de caixa.",
    },
    {
      id: "hr",
      departmentName: "RH",
      weightPct: 15,
      note: "Peso oficial do IGD para engajamento, retenção e capacitação.",
    },
    {
      id: "commercial",
      departmentName: "Comercial",
      weightPct: 17,
      note: "Peso oficial do IGD para receita, conversão e expansão comercial.",
    },
    {
      id: "production",
      departmentName: "Produção",
      weightPct: 17,
      note: "Peso oficial do IGD para eficiência produtiva e entrega.",
    },
    {
      id: "quality",
      departmentName: "Qualidade",
      weightPct: 14,
      note: "Peso oficial do IGD para falhas, disciplina operacional e Kaizen.",
    },
    {
      id: "supplies",
      departmentName: "Suprimentos",
      weightPct: 12,
      note: "Peso oficial do IGD para compras, estoque e eficiência de suprimentos.",
    },
    {
      id: "engineering",
      departmentName: "Engenharia",
      weightPct: 10,
      note: "Peso oficial do IGD para entrega no prazo e inovação.",
    },
  ],
  goals: [
    {
      id: "financial-goal",
      departmentName: "Financeiro",
      headlineGoal: "EBITDA 13,0%",
      supportingFocus: "Eficiência estrutural e PMR de 39 dias.",
    },
    {
      id: "hr-goal",
      departmentName: "RH",
      headlineGoal: "Turnover 1,5% ao mês",
      supportingFocus: "Satisfação interna de 85% e PDIs ativos em 100%.",
    },
    {
      id: "commercial-goal",
      departmentName: "Comercial",
      headlineGoal: "Fechamento 30%",
      supportingFocus: "ROL matriz/filial em 100% e novos clientes em 10/mês.",
    },
    {
      id: "production-goal",
      departmentName: "Produção",
      headlineGoal: "OEE 70%",
      supportingFocus: "OTD em 92% e controle dos custos de produção.",
    },
    {
      id: "quality-goal",
      departmentName: "Qualidade",
      headlineGoal: "PPM Externo 1.100",
      supportingFocus: "5S em 80% e ganhos Kaizen crescentes.",
    },
    {
      id: "supplies-goal",
      departmentName: "Suprimentos",
      headlineGoal: "OTD Compras 92%",
      supportingFocus: "CPV em 50,5% e estoque consolidado sob controle.",
    },
    {
      id: "engineering-goal",
      departmentName: "Engenharia",
      headlineGoal: "Projetos no prazo 95%",
      supportingFocus: "Ganhos do TRANSFORMA+ em R$ 15.000/mês.",
    },
  ],
  governance: [
    {
      id: "governance-1",
      label: "Modo do módulo",
      value: "Microfrontend federado",
      observation: "A governança do plugin segue o contrato oficial do manifesto e o shell da MinhaDelpi.",
    },
    {
      id: "governance-2",
      label: "Rota administrativa",
      value: "/apps/strategic-indicators/settings",
      observation: "A rota está declarada no manifesto e protegida por permissão administrativa.",
    },
    {
      id: "governance-3",
      label: "Permissão requerida",
      value: "strategic-indicators.settings.manage",
      observation: "Somente perfis com governança do módulo devem editar parâmetros futuramente.",
    },
    {
      id: "governance-4",
      label: "Persistência",
      value: "Mock nesta fase",
      observation: "A tela prepara a futura persistência real sem introduzir save em banco nesta etapa.",
    },
  ],
  parameters: [
    {
      id: "parameter-1",
      label: "Periodicidade do painel",
      value: "Mensal",
      observation: "O IGD é apresentado mensalmente no Painel Estratégico de Indicadores.",
    },
    {
      id: "parameter-2",
      label: "Escala do índice",
      value: "0 a 10",
      observation: "A leitura executiva do IGD segue a escala consolidada oficial.",
    },
    {
      id: "parameter-3",
      label: "Faixa atual do exemplo",
      value: "Satisfatório com Alertas",
      observation: "O exemplo consolidado do documento fecha em 7,8.",
    },
    {
      id: "parameter-4",
      label: "Renderização do módulo",
      value: "Federated",
      observation: "O módulo é entregue como microfrontend federado na MinhaDelpi.",
    },
  ],
  readiness: [
    {
      id: "readiness-1",
      title: "Manifesto e rota administrativa",
      status: "ready",
      description: "Contrato do plugin já contempla rota e permissão administrativa.",
    },
    {
      id: "readiness-2",
      title: "Base de pesos e metas",
      status: "ready",
      description: "Estrutura oficial do IGD/IDD já está consolidada para futura persistência.",
    },
    {
      id: "readiness-3",
      title: "Persistência real de configuração",
      status: "planned",
      description: "Próxima evolução natural após o fechamento do MVP visual e administrativo.",
    },
    {
      id: "readiness-4",
      title: "Edição salva em banco",
      status: "mock",
      description: "Ainda não entra nesta fase para manter o escopo disciplinado.",
    },
  ],
};