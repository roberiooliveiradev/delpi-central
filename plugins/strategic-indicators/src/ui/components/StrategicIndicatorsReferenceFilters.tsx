import {
  STRATEGIC_INDICATORS_BRANCH_OPTIONS,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
import "./StrategicIndicatorsReferenceFilters.css";

type StrategicIndicatorsReferenceFiltersProps = {
  referenceMonth: string;
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  onReferenceMonthChange: (value: string) => void;
  onViewModeChange: (value: StrategicIndicatorsViewMode) => void;
  onBranchChange: (value: string) => void;
};

export function StrategicIndicatorsReferenceFilters({
  referenceMonth,
  viewMode,
  branch,
  onReferenceMonthChange,
  onViewModeChange,
  onBranchChange,
}: StrategicIndicatorsReferenceFiltersProps) {
  return (
    <div className="si-form-grid">
      <label className="si-field">
        <span className="si-field__label">Mês de referência</span>
        <input
          type="month"
          className="si-input"
          value={referenceMonth}
          onChange={(event) => onReferenceMonthChange(event.target.value)}
        />
      </label>

      <label className="si-field">
        <span className="si-field__label">Visão</span>
        <select
          className="si-input"
          value={viewMode}
          onChange={(event) =>
            onViewModeChange(event.target.value as StrategicIndicatorsViewMode)
          }
        >
          <option value="consolidated">Consolidado</option>
          <option value="branch">Por filial</option>
        </select>
      </label>

      {viewMode === "branch" ? (
        <label className="si-field">
          <span className="si-field__label">Filial</span>
          <select
            className="si-input"
            value={branch}
            onChange={(event) => onBranchChange(event.target.value)}
          >
            {STRATEGIC_INDICATORS_BRANCH_OPTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      ) : null}
    </div>
  );
}