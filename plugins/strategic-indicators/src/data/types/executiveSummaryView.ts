export type ExecutiveDepartmentSummary = {
  id: string;
  name: string;
  shortName: string;
  weightPct: number;
  score: number;
  contribution: number;
  trend: string;
  strategicSummary: string;
  keyIndicators: string[];
  executiveGoal: string;
};