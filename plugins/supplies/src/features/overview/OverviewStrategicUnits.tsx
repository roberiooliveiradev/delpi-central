import type { OverviewKpiStrategic } from "../../api/overview";
import { HelpTooltip } from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  buildActiveStrategicScopeRow,
  type StrategicUnitKey,
} from "./overviewStrategicBreakdown";

type OverviewStrategicUnitsProps = {
  strategic: OverviewKpiStrategic | null;
  scopeKey: StrategicUnitKey | null;
};

export function OverviewStrategicUnits({ strategic, scopeKey }: OverviewStrategicUnitsProps) {
  const row = buildActiveStrategicScopeRow(strategic, scopeKey);
  if (!row) return null;
  return (
    <ul className="sp-overview__units" aria-label="Realizado e meta do escopo ativo">
      <li className="sp-overview__unit">
        <span className="sp-overview__unit-label">{row.label}</span>
        <span>
          Realizado {row.realizedLabel}{" "}
          <HelpTooltip content={SP_HELP.overviewUnitRealized} ariaLabel="Ajuda: realizado do escopo" />
        </span>
        <span>
          {row.goalCaption} {row.goalLabel}{" "}
          <HelpTooltip content={SP_HELP.overviewUnitGoal} ariaLabel="Ajuda: meta do período" />
        </span>
      </li>
    </ul>
  );
}
