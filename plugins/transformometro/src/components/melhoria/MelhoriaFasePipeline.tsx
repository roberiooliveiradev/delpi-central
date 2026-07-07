import { MELHORIA_FASE_OPTIONS } from "../../constants/melhoriaForm";
import { FieldLabel } from "@delpi/plugin-ui";

type Props = {
  currentFase?: string | null;
  hint?: string;
};

export function MelhoriaFasePipeline({ currentFase, hint }: Props) {
  const normalized = (currentFase?.trim() || "planejado").toLowerCase();
  const activeIndex = MELHORIA_FASE_OPTIONS.findIndex((item) => item.value === normalized);

  return (
    <div className="tm-fase-pipeline-block">
      {hint ? (
        <p className="tm-fase-pipeline-block__label">
          <FieldLabel className="tm-field__label" label="Fase da melhoria" hint={hint} />
        </p>
      ) : null}
      <div className="tm-fase-pipeline" role="list" aria-label="Progresso da melhoria">
        {MELHORIA_FASE_OPTIONS.map((fase, index) => {
          const isActive = fase.value === normalized;
          const isPast = activeIndex >= 0 && index < activeIndex;
          const stateClass = isActive
            ? " tm-fase-pipeline__step--active"
            : isPast
              ? " tm-fase-pipeline__step--past"
              : "";

          return (
            <div
              key={fase.value}
              className={`tm-fase-pipeline__step${stateClass}`}
              role="listitem"
              aria-current={isActive ? "step" : undefined}
            >
              <span className="tm-fase-pipeline__dot" aria-hidden="true" />
              <span className="tm-fase-pipeline__label">{fase.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
