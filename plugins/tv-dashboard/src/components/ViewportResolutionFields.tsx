import { useEffect, useState } from "react";
import { NativeTextControl, ToolbarSelectField } from "@delpi/plugin-ui/index";

import {
  formatViewportDimensionFromPx,
  isCustomViewportProfile,
  listViewportProfileSelectOptions,
  parseViewportDimensionToPx,
  readStoredViewportLengthUnit,
  VIEWPORT_LENGTH_UNIT_LABELS,
  VIEWPORT_LENGTH_UNITS,
  writeStoredViewportLengthUnit,
  type ViewportLengthUnit,
} from "../utils/viewportPixelSize";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

export type ViewportSettingsValue = {
  viewportProfile: string;
  viewportWidth?: number | null;
  viewportHeight?: number | null;
};

type Props = {
  value: ViewportSettingsValue;
  onChange: (next: ViewportSettingsValue) => void;
  compact?: boolean;
};

/**
 * Select de resolução (presets + Personalizado) com L×A e unidade CSS.
 * Sempre emite width/height em px quando custom.
 */
export function ViewportResolutionFields({ value, onChange, compact = false }: Props) {
  const [unit, setUnit] = useState<ViewportLengthUnit>(() => readStoredViewportLengthUnit());
  const custom = isCustomViewportProfile(value.viewportProfile);
  const widthPx = value.viewportWidth ?? 1920;
  const heightPx = value.viewportHeight ?? 1080;
  const [widthDraft, setWidthDraft] = useState(() =>
    formatViewportDimensionFromPx(widthPx, unit),
  );
  const [heightDraft, setHeightDraft] = useState(() =>
    formatViewportDimensionFromPx(heightPx, unit),
  );

  useEffect(() => {
    if (!custom) return;
    setWidthDraft(formatViewportDimensionFromPx(value.viewportWidth ?? 1920, unit));
    setHeightDraft(formatViewportDimensionFromPx(value.viewportHeight ?? 1080, unit));
  }, [custom, value.viewportWidth, value.viewportHeight, unit]);

  function commitCustom(nextWidthDraft: string, nextHeightDraft: string) {
    const w = parseViewportDimensionToPx(nextWidthDraft, unit);
    const h = parseViewportDimensionToPx(nextHeightDraft, unit);
    if (w == null || h == null) return;
    onChange({
      viewportProfile: "custom",
      viewportWidth: w,
      viewportHeight: h,
    });
  }

  function changeUnit(next: ViewportLengthUnit) {
    const w = parseViewportDimensionToPx(widthDraft, unit) ?? widthPx;
    const h = parseViewportDimensionToPx(heightDraft, unit) ?? heightPx;
    setUnit(next);
    writeStoredViewportLengthUnit(next);
    setWidthDraft(formatViewportDimensionFromPx(w, next));
    setHeightDraft(formatViewportDimensionFromPx(h, next));
  }

  const selectClass = compact ? "delpi-ui-select--compact" : undefined;
  const nativeClass = compact ? "delpi-ui-native-control--compact" : undefined;

  return (
    <div className="td-viewport-resolution-fields">
      <ToolbarSelectField
        label="Resolução alvo"
        title={TV_DASHBOARD_HELP_TOOLTIPS.fields.viewport}
        value={custom ? "custom" : value.viewportProfile}
        allowEmptyOption={false}
        searchable={false}
        className={selectClass}
        options={listViewportProfileSelectOptions()}
        onChange={(next) => {
          if (next === "custom") {
            onChange({
              viewportProfile: "custom",
              viewportWidth: value.viewportWidth ?? 1920,
              viewportHeight: value.viewportHeight ?? 1080,
            });
            return;
          }
          onChange({
            viewportProfile: next,
            viewportWidth: null,
            viewportHeight: null,
          });
        }}
      />
      {custom ? (
        <div className="td-viewport-resolution-fields__custom">
          <label className="td-viewport-resolution-fields__label" htmlFor="td-viewport-width">
            Largura
          </label>
          <NativeTextControl
            id="td-viewport-width"
            className={nativeClass}
            inputMode="decimal"
            value={widthDraft}
            aria-label="Largura da resolução"
            onChange={(value) => setWidthDraft(value)}
            onBlur={() => commitCustom(widthDraft, heightDraft)}
          />
          <label className="td-viewport-resolution-fields__label" htmlFor="td-viewport-height">
            Altura
          </label>
          <NativeTextControl
            id="td-viewport-height"
            className={nativeClass}
            inputMode="decimal"
            value={heightDraft}
            aria-label="Altura da resolução"
            onChange={(value) => setHeightDraft(value)}
            onBlur={() => commitCustom(widthDraft, heightDraft)}
          />
          <ToolbarSelectField
            label="Unidade"
            title={TV_DASHBOARD_HELP_TOOLTIPS.fields.viewportUnit}
            value={unit}
            allowEmptyOption={false}
            searchable={false}
            className={[selectClass, "td-viewport-resolution-fields__unit"].filter(Boolean).join(" ")}
            options={VIEWPORT_LENGTH_UNITS.map((item) => ({
              value: item,
              label: VIEWPORT_LENGTH_UNIT_LABELS[item],
            }))}
            onChange={(next) => changeUnit(next as ViewportLengthUnit)}
          />
          <p className="td-deck-inspector__hint td-viewport-resolution-fields__hint">
            {TV_DASHBOARD_HELP_TOOLTIPS.fields.viewportCustomHint}
          </p>
        </div>
      ) : null}
    </div>
  );
}
