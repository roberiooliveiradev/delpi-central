import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type HubChipRowClassNames = {
  root: string;
  label: string;
  chips: string;
};

export type HubChipRowProps = {
  label: ReactNode;
  children: ReactNode;
  classNames: HubChipRowClassNames;
  className?: string;
  "aria-label"?: string;
};

export function hubChipRowBemClasses(prefix: string): HubChipRowClassNames {
  const base = `${prefix}-hub-chip-row`;
  const ui = "delpi-ui-hub-chip-row";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    label: pair(`${base}__label`, `${ui}__label`),
    chips: pair(`${base}__chips`, `${ui}__chips`),
  };
}

/**
 * Faixa rotulada de chips do hub (Favoritos / Últimos acessos).
 * CSS: `styles/hub-route-chips.css`.
 */
export function HubChipRow({
  label,
  children,
  classNames,
  className,
  "aria-label": ariaLabel,
}: HubChipRowProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} role="group" aria-label={ariaLabel}>
      <span className={classNames.label}>{label}</span>
      <div className={classNames.chips}>{children}</div>
    </div>
  );
}

export type DashboardHubChipRowProps = Omit<HubChipRowProps, "classNames">;

export function createDashboardHubChipRow(config: { prefix: string }) {
  const classNames = hubChipRowBemClasses(config.prefix);
  return function DashboardHubChipRow(props: DashboardHubChipRowProps) {
    return <HubChipRow classNames={classNames} {...props} />;
  };
}
