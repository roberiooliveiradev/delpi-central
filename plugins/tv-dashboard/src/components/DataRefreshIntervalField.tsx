import { useState } from "react";
import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  DATA_REFRESH_SEC_MAX,
  DATA_REFRESH_SEC_MIN,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { DeckField } from "./deck/DeckField";

const REFRESH_PRESET_VALUES = new Set(["60", "120", "300", "600"]);

function parseRefreshSecInput(
  raw: string,
): number | undefined | "invalid" {
  if (!raw.trim()) return undefined;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return "invalid";
  return Math.min(
    DATA_REFRESH_SEC_MAX,
    Math.max(DATA_REFRESH_SEC_MIN, Math.round(parsed)),
  );
}

type Props = {
  /** `binding.refreshSec` atual (undefined = herda o padrão global). */
  refreshSec?: number | null;
  /** Intervalo efetivo herdado (playlist/global) para o rótulo «Padrão». */
  inheritedRefreshSec: number;
  /** ribbon — select de presets + custom; pane — input numérico. */
  compact?: boolean;
  id?: string;
  onChange: (sec: number | undefined) => void;
};

/**
 * Campo «Atualizar na TV a cada (s)» — owner compartilhado entre o
 * inspector da fonte e o flyout «Atualização» da ribbon (mesma regra de
 * clamp `DATA_REFRESH_SEC_MIN..MAX`; vazio = herda o global).
 */
export function DataRefreshIntervalField({
  refreshSec,
  inheritedRefreshSec,
  compact = false,
  id = "td-data-refresh",
  onChange,
}: Props) {
  const [custom, setCustom] = useState(false);

  const applyRaw = (raw: string) => {
    const next = parseRefreshSecInput(raw);
    if (next !== "invalid") onChange(next);
  };

  const asStr = refreshSec == null ? "" : String(refreshSec);
  const selectValue =
    refreshSec == null
      ? ""
      : REFRESH_PRESET_VALUES.has(asStr)
        ? asStr
        : "__custom__";
  const showCustom = custom || selectValue === "__custom__";

  return (
    <DeckField
      id={id}
      label="Atualizar na TV a cada (s)"
      hint={TV_DASHBOARD_HELP_TOOLTIPS.fields.dataBlockRefreshInterval}
    >
      {compact ? (
        <>
          <FormSelectControl
            id={id}
            className="delpi-ui-select--compact"
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            ariaLabel="Atualizar a cada (s)"
            value={showCustom ? "__custom__" : selectValue}
            onChange={(value) => {
              if (value === "__custom__") {
                setCustom(true);
                return;
              }
              setCustom(false);
              applyRaw(value);
            }}
            options={[
              { value: "", label: `Padrão (${inheritedRefreshSec}s)` },
              { value: "60", label: "60s" },
              { value: "120", label: "120s" },
              { value: "300", label: "300s" },
              { value: "600", label: "600s" },
              { value: "__custom__", label: "Personalizado…" },
            ]}
          />
          {showCustom ? (
            <NativeTextControl
              id={`${id}-custom`}
              type="number"
              className="delpi-ui-native-control--compact"
              min={DATA_REFRESH_SEC_MIN}
              max={DATA_REFRESH_SEC_MAX}
              placeholder={`${DATA_REFRESH_SEC_MIN}–${DATA_REFRESH_SEC_MAX}`}
              value={refreshSec ?? ""}
              onChange={applyRaw}
            />
          ) : null}
        </>
      ) : (
        <NativeTextControl
          id={id}
          type="number"
          min={DATA_REFRESH_SEC_MIN}
          max={DATA_REFRESH_SEC_MAX}
          placeholder={`Padrão (${inheritedRefreshSec}s)`}
          value={refreshSec ?? ""}
          onChange={applyRaw}
        />
      )}
    </DeckField>
  );
}
