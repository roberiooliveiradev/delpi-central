export type TrendDirection = "up" | "down" | "stable";

export type IgdTrendPoint = {
  period: string;
  value: number;
};

export type DepartmentTrendItem = {
  id: string;
  name: string;
  current: number;
  previous: number;
  direction: TrendDirection;
};

export type TrendsDashboardData = {
  currentIgd: number;
  previousIgd: number;
  currentClassification: string;
  igdSeries: IgdTrendPoint[];
  departments: DepartmentTrendItem[];
};

function getDirection(current: number, previous: number): TrendDirection {
  const diff = current - previous;

  if (diff > 0.09) return "up";
  if (diff < -0.09) return "down";
  return "stable";
}

export const trendsMock: TrendsDashboardData = {
  currentIgd: 7.8,
  previousIgd: 7.6,
  currentClassification: "Satisfatório com Alertas",
  igdSeries: [
    { period: "Out/25", value: 7.1 },
    { period: "Nov/25", value: 7.3 },
    { period: "Dez/25", value: 7.2 },
    { period: "Jan/26", value: 7.4 },
    { period: "Fev/26", value: 7.6 },
    { period: "Mar/26", value: 7.8 },
  ],
  departments: [
    {
      id: "financial",
      name: "Financeiro",
      current: 7.8,
      previous: 7.6,
      direction: getDirection(7.8, 7.6),
    },
    {
      id: "hr",
      name: "RH",
      current: 8.0,
      previous: 7.9,
      direction: getDirection(8.0, 7.9),
    },
    {
      id: "commercial",
      name: "Comercial",
      current: 8.2,
      previous: 8.0,
      direction: getDirection(8.2, 8.0),
    },
    {
      id: "production",
      name: "Produção",
      current: 7.8,
      previous: 7.7,
      direction: getDirection(7.8, 7.7),
    },
    {
      id: "quality",
      name: "Qualidade",
      current: 7.4,
      previous: 7.2,
      direction: getDirection(7.4, 7.2),
    },
    {
      id: "supplies",
      name: "Suprimentos",
      current: 7.1,
      previous: 7.3,
      direction: getDirection(7.1, 7.3),
    },
    {
      id: "engineering",
      name: "Engenharia",
      current: 7.9,
      previous: 7.8,
      direction: getDirection(7.9, 7.8),
    },
  ],
};