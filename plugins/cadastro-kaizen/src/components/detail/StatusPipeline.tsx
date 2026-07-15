import { Check } from "lucide-react";

import type { KaizenStatus } from "../../types/kaizen";

const FLOW: Array<{ value: KaizenStatus; label: string }> = [
  { value: "recebido", label: "Recebido" },
  { value: "aprovado", label: "Aprovado" },
  { value: "implantado", label: "Implantado" },
];

const TERMINALS: Record<string, { label: string; tone: "danger" | "muted" }> = {
  descontinuado: { label: "Descontinuado", tone: "muted" },
  cancelado: { label: "Cancelado", tone: "danger" },
};

type StatusPipelineProps = {
  status: KaizenStatus;
};

export function StatusPipeline({ status }: StatusPipelineProps) {
  const terminal = TERMINALS[status];

  if (terminal) {
    return (
      <div className="kz-pipeline">
        <div className={`kz-pipeline__terminal kz-pipeline__terminal--${terminal.tone}`}>
          {terminal.label}
        </div>
      </div>
    );
  }

  const currentIndex = FLOW.findIndex((step) => step.value === status);

  return (
    <ol className="kz-pipeline">
      {FLOW.map((step, index) => {
        const isDone = index < currentIndex;
        const isCurrent = index === currentIndex;
        const stateClass = isCurrent
          ? "kz-pipeline__step--current"
          : isDone
            ? "kz-pipeline__step--done"
            : "kz-pipeline__step--todo";
        return (
          <li key={step.value} className={`kz-pipeline__step ${stateClass}`}>
            <span className="kz-pipeline__marker" aria-hidden="true">
              {isDone ? <Check size={14} /> : index + 1}
            </span>
            <span className="kz-pipeline__label">{step.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
