import {
  STRATEGIC_INDICATORS_BRANCH_OPTIONS,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
import "./StrategicIndicatorsReferenceFilters.css";

type StrategicIndicatorsReferenceFiltersProps = {
  referenceMonth: string;
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  monthsToCompare?: number;
  showMonthsToCompare?: boolean;
  onReferenceMonthChange: (value: string) => void;
  onViewModeChange: (value: StrategicIndicatorsViewMode) => void;
  onBranchChange: (value: string) => void;
  onMonthsToCompareChange?: (value: number) => void;
};

export function StrategicIndicatorsReferenceFilters({
  referenceMonth,
  viewMode,
  branch,
  monthsToCompare = 3,
  showMonthsToCompare = false,
  onReferenceMonthChange,
  onViewModeChange,
  onBranchChange,
  onMonthsToCompareChange,
}: StrategicIndicatorsReferenceFiltersProps) {
  return (
    <div
      className={`si-reference-filters ${
        showMonthsToCompare ? "si-reference-filters--with-comparison" : ""
      }`}
    >
      <label className="si-reference-filters__field">
        <span className="si-reference-filters__label">Mês de referência</span>
        <input
          type="month"
          className="si-reference-filters__input"
          value={referenceMonth}
          onChange={(event) => onReferenceMonthChange(event.target.value)}
        />
      </label>

      <label className="si-reference-filters__field">
        <span className="si-reference-filters__label">Visão</span>
        <select
          className="si-reference-filters__input"
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
        <label className="si-reference-filters__field">
          <span className="si-reference-filters__label">Filial</span>
          <select
            className="si-reference-filters__input"
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

      {showMonthsToCompare ? (
        <label className="si-reference-filters__field">
          <span className="si-reference-filters__label">
            Meses de comparação
          </span>

          <select
            className="si-reference-filters__input"
            value={monthsToCompare}
            onChange={(event) =>
              onMonthsToCompareChange?.(Number(event.target.value))
            }
          >
            <option value={2}>2 meses</option>
            <option value={3}>3 meses</option>
            <option value={4}>4 meses</option>
            <option value={6}>6 meses</option>
            <option value={12}>12 meses</option>
          </select>
        </label>
      ) : null}
    </div>
  );
}