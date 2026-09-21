import type { OverviewKpiStrategic } from "../../api/overview";
import { HelpTooltip } from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { buildStrategicUnitRows } from "./overviewStrategicBreakdown";

type OverviewStrategicUnitsProps = {
  strategic: OverviewKpiStrategic | null;
};

export function OverviewStrategicUnits({ strategic }: OverviewStrategicUnitsProps) {
  const rows = buildStrategicUnitRows(strategic);
  if (rows.length === 0) return null;
  return (
    <ul className="sp-overview__units" aria-label="Realizado e meta por unidade">
      {rows.map((row) => (
        <li key={row.key} className="sp-overview__unit">
          <span className="sp-overview__unit-label">{row.label}</span>
          <span>
            Realizado {row.realizedLabel}{" "}
            <HelpTooltip content={SP_HELP.overviewUnitRealized} ariaLabel="Ajuda: realizado por unidade" />
          </span>
          <span>
            {row.goalCaption} {row.goalLabel}{" "}
            <HelpTooltip content={SP_HELP.overviewUnitGoal} ariaLabel="Ajuda: meta do período" />
          </span>
        </li>
      ))}
    </ul>
  );
}
