import { PLAN_STATUSES } from "../../constants/actionPlans";

type StatusPipelineProps = {
  currentStatus: string;
};

export function StatusPipeline({ currentStatus }: StatusPipelineProps) {
  const activeIndex = PLAN_STATUSES.findIndex((item) => item.value === currentStatus);
  const visibleStatuses = PLAN_STATUSES.filter((item) => item.value !== "cancelled");

  return (
    <div className="pac-status-pipeline" role="list" aria-label="Progresso do plano">
      {visibleStatuses.map((status, index) => {
        const isActive = status.value === currentStatus;
        const isPast = activeIndex >= 0 && index < activeIndex;
        const stateClass = isActive
          ? " pac-status-pipeline__step--active"
          : isPast
            ? " pac-status-pipeline__step--past"
            : "";

        return (
          <div
            key={status.value}
            className={`pac-status-pipeline__step${stateClass}`}
            role="listitem"
            aria-current={isActive ? "step" : undefined}
          >
            <span className="pac-status-pipeline__dot" aria-hidden="true" />
            <span className="pac-status-pipeline__label">{status.label}</span>
          </div>
        );
      })}
    </div>
  );
}
