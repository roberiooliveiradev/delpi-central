export type ExecutiveDepartmentSummary = {
  id: string;
  name: string;
  shortName: string;
  weightPct: number;
  score: number;
  contribution: number;
  trend: "up" | "down" | "stable";
  strategicSummary: string;
  keyIndicators: string[];
  executiveGoal: string;
  variation: {
    value: number;
    direction: "up" | "down" | "stable";
  };
};