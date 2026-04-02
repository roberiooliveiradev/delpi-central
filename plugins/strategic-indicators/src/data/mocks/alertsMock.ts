export type AlertSeverity = "high" | "medium" | "low";

export type ExecutiveAlert = {
  id: string;
  title: string;
  severity: AlertSeverity;
  impact: string;
  recommendation: string;
};

export type DepartmentAlert = {
  id: string;
  departmentName: string;
  currentScore: number;
  previousScore: number;
  severity: AlertSeverity;
  reason: string;
  recommendation: string;
};

export type IndicatorAlert = {
  id: string;
  departmentName: string;
  indicatorName: string;
  simulatedScore: number;
  goal2026: string;
  severity: AlertSeverity;
  reason: string;
  recommendation: string;
};

export type AlertsDashboardData = {
  igdClassification: string;
  executiveAlerts: ExecutiveAlert[];
  departmentAlerts: DepartmentAlert[];
  indicatorAlerts: IndicatorAlert[];
};

export const alertsMock: AlertsDashboardData = {
  igdClassification: "Satisfatório com Alertas",
  executiveAlerts: [
    {
      id: "igd-alert-band",
      title: "IGD em faixa de atenção",
      severity: "medium",
      impact:
        "O índice global permanece em faixa satisfatória, porém ainda com alertas.",
      recommendation:
        "Priorizar departamentos com queda recente e indicadores abaixo da meta crítica.",
    },
    {
      id: "trend-alert-supplies",
      title: "Suprimentos apresentou queda no período",
      severity: "high",
      impact:
        "A redução recente impacta a estabilidade do IGD e aumenta risco operacional.",
      recommendation:
        "Revisar estoque consolidado, desempenho de compras e eficiência das negociações.",
    },
    {
      id: "quality-risk-external-ppm",
      title: "Qualidade com risco em falhas externas",
      severity: "high",
      impact:
        "Indicadores de falha percebida pelo cliente afetam imagem e confiabilidade.",
      recommendation:
        "Atacar PPM Externo com plano de contenção e reforço de análise de causa.",
    },
  ],
  departmentAlerts: [
    {
      id: "supplies",
      departmentName: "Suprimentos",
      currentScore: 7.1,
      previousScore: 7.3,
      severity: "high",
      reason:
        "Queda no período e presença de indicadores com necessidade de atenção.",
      recommendation:
        "Atuar em estoque consolidado, OTD de compras e economia em negociações.",
    },
    {
      id: "quality",
      departmentName: "Qualidade",
      currentScore: 7.4,
      previousScore: 7.2,
      severity: "medium",
      reason:
        "Apesar da melhora, o departamento ainda permanece em faixa com alertas.",
      recommendation:
        "Priorizar PPM Externo e acelerar ações ligadas a disciplina operacional e Kaizen.",
    },
    {
      id: "production",
      departmentName: "Produção",
      currentScore: 7.8,
      previousScore: 7.7,
      severity: "medium",
      reason:
        "Área está estável, mas depende de sustentação em OTD e eficiência operacional.",
      recommendation:
        "Acompanhar OEE e OTD para evitar regressão no próximo fechamento.",
    },
  ],
  indicatorAlerts: [
    {
      id: "quality-ppm-external",
      departmentName: "Qualidade",
      indicatorName: "PPM Externo",
      simulatedScore: 6.8,
      goal2026: "1.100 PPM",
      severity: "high",
      reason:
        "Indicador com pior nota do recorte analítico e impacto direto no cliente.",
      recommendation:
        "Abrir plano de ação prioritário com contenção e análise de causa raiz.",
    },
    {
      id: "supplies-total-stock",
      departmentName: "Suprimentos",
      indicatorName: "Valor Total do Estoque Consolidado",
      simulatedScore: 6.9,
      goal2026: "R$ 13.500.000,00",
      severity: "high",
      reason:
        "Capital parado acima do desejado pressiona eficiência financeira e operacional.",
      recommendation:
        "Revisar curva de estoque, giro e itens com baixa movimentação.",
    },
    {
      id: "supplies-cpv",
      departmentName: "Suprimentos",
      indicatorName: "CPV Consolidado (matriz e filial)",
      simulatedScore: 7.0,
      goal2026: "50,5%",
      severity: "medium",
      reason:
        "Desempenho limítrofe em indicador central de compras e custo.",
      recommendation:
        "Intensificar renegociações e controle de composição de custos.",
    },
    {
      id: "production-costs",
      departmentName: "Produção",
      indicatorName: "Custos de Produção / ROL",
      simulatedScore: 7.2,
      goal2026: "32,0%",
      severity: "medium",
      reason:
        "Indicador ainda exige disciplina para não comprometer margem operacional.",
      recommendation:
        "Atuar em desperdícios, produtividade e aderência ao padrão operacional.",
    },
  ],
};