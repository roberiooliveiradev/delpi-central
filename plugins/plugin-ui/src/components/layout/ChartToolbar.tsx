import { Download } from "lucide-react";
import type { ReactNode } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { FieldLabel } from "../help/FieldLabel";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type ChartGranularityOption<T extends string = string> = {
  value: T;
  label: string;
};

export type ChartGranularityToggleClassNames = {
  root: string;
  button: string;
  buttonActive: string;
};

export type ChartGranularityToggleLabels = {
  groupAriaLabel: string;
};

export type ChartGranularityToggleProps<T extends string = string> = {
  value: T;
  onChange: (value: T) => void;
  options: readonly ChartGranularityOption<T>[];
  idPrefix?: string;
  classNames: ChartGranularityToggleClassNames;
  labels: ChartGranularityToggleLabels;
};

export type ChartToolbarClassNames = {
  toolbar: string;
  granularity?: string;
  granularityHelp?: string;
  group?: string;
  actions: string;
  action?: string;
  actionHelp?: string;
  exportButton: string;
  fieldLabel?: string;
};

export type ChartToolbarLabels = {
  exportSeries: string;
  exportSeriesAriaLabel: string;
};

export type ChartToolbarProps<T extends string = string> = {
  granularity: T;
  onGranularityChange: (value: T) => void;
  options: readonly ChartGranularityOption<T>[];
  idPrefix?: string;
  onExportCsv?: () => void;
  exportDisabled?: boolean;
  exportActions?: ReactNode;
  extra?: ReactNode;
  granularityHelp?: string;
  exportHelp?: string;
  granularityField?: {
    label: string;
    hint?: string;
  };
  classNames: ChartToolbarClassNames;
  labels: ChartToolbarLabels;
  granularityToggleClassNames: ChartGranularityToggleClassNames;
  granularityToggleLabels: ChartGranularityToggleLabels;
};

export type DashboardChartToolbarLabels = ChartToolbarLabels & ChartGranularityToggleLabels;

/** Monta classNames BEM `{prefix}-chart-toolbar*` + `.delpi-ui-chart-toolbar*`. */
export function chartToolbarBemClasses(prefix: string) {
  const tb = `${prefix}-chart-toolbar`;
  const ui = "delpi-ui-chart-toolbar";
  const seg = `${prefix}-segment-toggle`;
  const uiSeg = "delpi-ui-segment-toggle";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    toolbar: pair(tb, ui),
    granularity: pair(`${tb}__granularity`, `${ui}__granularity`),
    granularityHelp: pair(`${tb}__granularity-help`, `${ui}__granularity-help`),
    group: pair(`${tb}__group`, `${ui}__group`),
    actions: pair(`${tb}__actions`, `${ui}__actions`),
    action: pair(`${tb}__action`, `${ui}__action`),
    actionHelp: pair(`${tb}__action-help`, `${ui}__action-help`),
    exportButton: pair(
      `${prefix}-ghost-btn ${tb}__export`,
      `delpi-ui-ghost-btn ${ui}__export`,
    ),
    fieldLabel: `${prefix}-field__label`,
    segmentToggle: pair(seg, uiSeg),
    segmentButton: pair(`${seg}__btn`, `${uiSeg}__btn`),
    segmentButtonActive: pair(
      `${seg}__btn ${seg}__btn--active`,
      `${uiSeg}__btn ${uiSeg}__btn--active`,
    ),
  };
}

export function ChartGranularityToggle<T extends string>({
  value,
  onChange,
  options,
  idPrefix = "chart",
  classNames,
  labels,
}: ChartGranularityToggleProps<T>) {
  return (
    <div className={classNames.root} role="group" aria-label={labels.groupAriaLabel}>
      {options.map((option) => {
        const isActive = value === option.value;
        return (
          <button
            key={option.value}
            id={`${idPrefix}-granularity-${option.value}`}
            type="button"
            className={isActive ? classNames.buttonActive : classNames.button}
            onClick={() => onChange(option.value)}
            aria-pressed={isActive}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

export function ChartToolbar<T extends string>({
  granularity,
  onGranularityChange,
  options,
  idPrefix,
  onExportCsv,
  exportDisabled = false,
  exportActions,
  extra,
  granularityHelp,
  exportHelp,
  granularityField,
  classNames,
  labels,
  granularityToggleClassNames,
  granularityToggleLabels,
}: ChartToolbarProps<T>) {
  const toggle = (
    <ChartGranularityToggle
      value={granularity}
      onChange={onGranularityChange}
      options={options}
      idPrefix={idPrefix}
      classNames={granularityToggleClassNames}
      labels={granularityToggleLabels}
    />
  );

  const granularityNode = granularityField ? (
    <div className={classNames.group}>
      <FieldLabel
        label={granularityField.label}
        hint={granularityField.hint}
        className={classNames.fieldLabel ?? ""}
      />
      {toggle}
    </div>
  ) : granularityHelp && classNames.granularity ? (
    <div className={classNames.granularity}>
      {toggle}
      <HelpTooltip
        content={granularityHelp}
        ariaLabel={`Ajuda: ${granularityToggleLabels.groupAriaLabel.toLowerCase()}`}
        className={classNames.granularityHelp}
      />
    </div>
  ) : (
    toggle
  );

  const builtInExport =
    !exportActions && onExportCsv ? (
      exportHelp && classNames.action ? (
        <div className={classNames.action}>
          <button
            type="button"
            className={classNames.exportButton}
            onClick={onExportCsv}
            disabled={exportDisabled}
            aria-label={labels.exportSeriesAriaLabel}
          >
            <Download size={16} aria-hidden />
            <span>{labels.exportSeries}</span>
          </button>
          <HelpTooltip
            content={exportHelp}
            ariaLabel="Ajuda: exportar CSV"
            className={classNames.actionHelp}
          />
        </div>
      ) : (
        <button
          type="button"
          className={classNames.exportButton}
          onClick={onExportCsv}
          disabled={exportDisabled}
          aria-label={labels.exportSeriesAriaLabel}
        >
          <Download size={16} aria-hidden />
          <span>{labels.exportSeries}</span>
        </button>
      )
    ) : null;

  const hasActions = Boolean(extra || exportActions || builtInExport);

  return (
    <div className={classNames.toolbar}>
      {granularityNode}
      {hasActions ? (
        <div className={classNames.actions}>
          {extra}
          {exportActions}
          {builtInExport}
        </div>
      ) : null}
    </div>
  );
}

export type DashboardChartGranularityToggleProps<T extends string> = Omit<
  ChartGranularityToggleProps<T>,
  "classNames" | "labels" | "options"
> & {
  modes?: readonly T[];
  options: readonly ChartGranularityOption<T>[];
};

export type DashboardChartToolbarProps<T extends string> = Omit<
  ChartToolbarProps<T>,
  | "classNames"
  | "labels"
  | "granularityToggleClassNames"
  | "granularityToggleLabels"
  | "options"
> & {
  modes?: readonly T[];
  options: readonly ChartGranularityOption<T>[];
};

export function createDashboardChartToolbarKit(config: {
  prefix: string;
  labels: DashboardChartToolbarLabels;
}) {
  const bem = chartToolbarBemClasses(config.prefix);
  const granularityToggleClassNames: ChartGranularityToggleClassNames = {
    root: bem.segmentToggle,
    button: bem.segmentButton,
    buttonActive: bem.segmentButtonActive,
  };
  const toolbarClassNames: ChartToolbarClassNames = {
    toolbar: bem.toolbar,
    granularity: bem.granularity,
    granularityHelp: bem.granularityHelp,
    group: bem.group,
    actions: bem.actions,
    action: bem.action,
    actionHelp: bem.actionHelp,
    exportButton: bem.exportButton,
    fieldLabel: bem.fieldLabel,
  };

  function resolveOptions<T extends string>(
    options: readonly ChartGranularityOption<T>[],
    modes?: readonly T[],
  ) {
    if (!modes?.length) return options;
    return options.filter((option) => modes.includes(option.value));
  }

  function DashboardChartGranularityToggle<T extends string>({
    modes,
    options,
    ...props
  }: DashboardChartGranularityToggleProps<T>) {
    return (
      <ChartGranularityToggle
        classNames={granularityToggleClassNames}
        labels={config.labels}
        options={resolveOptions(options, modes)}
        {...props}
      />
    );
  }

  function DashboardChartToolbar<T extends string>({
    modes,
    options,
    ...props
  }: DashboardChartToolbarProps<T>) {
    return (
      <ChartToolbar
        classNames={toolbarClassNames}
        labels={config.labels}
        granularityToggleClassNames={granularityToggleClassNames}
        granularityToggleLabels={config.labels}
        options={resolveOptions(options, modes)}
        {...props}
      />
    );
  }

  return {
    ChartGranularityToggle: DashboardChartGranularityToggle,
    ChartToolbar: DashboardChartToolbar,
  };
}
