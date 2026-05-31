export type SimulateSummary = {
  agentCount: number;
  sessionCount: number;
  hasResult: boolean;
};

export function computeSimulateSummary(
  agentCount: number,
  sessionCount: number,
  hasResult: boolean,
): SimulateSummary {
  return {
    agentCount: Math.max(0, agentCount),
    sessionCount: Math.max(0, sessionCount),
    hasResult,
  };
}
