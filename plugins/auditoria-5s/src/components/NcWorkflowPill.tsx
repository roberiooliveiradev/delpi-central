import { workflowStepLabel } from "../utils/ncDueSla";

type Props = {
  planStarted: boolean;
  workflowStep: 1 | 2 | 3;
  status: string;
};

export function NcWorkflowPill({ planStarted, workflowStep, status }: Props) {
  const label = workflowStepLabel(workflowStep, planStarted);
  const variant = status === "closed" ? "done" : planStarted ? "active" : "idle";

  return (
    <span className={`a5s-nc-board-workflow a5s-nc-board-workflow--${variant}`}>
      <span className="a5s-nc-board-workflow__step">{status === "closed" ? "✓" : workflowStep}</span>
      <span>{label}</span>
    </span>
  );
}
