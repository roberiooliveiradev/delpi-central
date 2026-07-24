import type { ReactNode } from "react";
import { X } from "lucide-react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type StateBoxVariant = "loading" | "error" | "empty";

export type StateBoxClassNames = {
  root: string;
  rootLoading: string;
  rootError: string;
  rootEmpty: string;
  icon: string;
  dismiss: string;
  dismissible: string;
};

export type StateBoxPanelProps = {
  variant: StateBoxVariant;
  title: string;
  message?: string;
  action?: ReactNode;
  icon: ReactNode;
  iconClassName?: string;
  classNames: StateBoxClassNames;
  /** Se definido, exibe X — erro/aviso só somem com fechar (ou ação do pai). */
  onDismiss?: () => void;
  dismissAriaLabel?: string;
};

/** Dual `{prefix}-state-box*` + `.delpi-ui-state-box*` (+ card shell). */
export function stateBoxBemClasses(prefix: string): StateBoxClassNames {
  const base = `${prefix}-state-box`;
  const card = `${prefix}-card`;
  const ui = "delpi-ui-state-box";
  const uiCard = "delpi-ui-card";
  const shell = delpiUiClass(`${card} ${base}`, `${uiCard} ${ui}`);

  return {
    root: shell,
    rootLoading: delpiUiClass(
      `${card} ${base} ${base}--loading`,
      `${uiCard} ${ui} ${ui}--loading`,
    ),
    rootError: delpiUiClass(
      `${card} ${base} ${base}--error`,
      `${uiCard} ${ui} ${ui}--error`,
    ),
    rootEmpty: delpiUiClass(
      `${card} ${base} ${base}--empty`,
      `${uiCard} ${ui} ${ui}--empty`,
    ),
    icon: delpiUiClass(`${base}__icon`, `${ui}__icon`),
    dismiss: delpiUiClass(`${base}__dismiss`, `${ui}__dismiss`),
    dismissible: delpiUiClass(`${base}--dismissible`, `${ui}--dismissible`),
  };
}

/** Placeholder de gráfico/lista (sem card) — dual `--empty`. */
export function stateBoxPlaceholderBemClasses(prefix: string): string {
  return delpiUiClass(
    `${prefix}-state-box`,
    "delpi-ui-state-box delpi-ui-state-box--empty",
  );
}

/** Placeholder compacto (listas inline) — dual `--empty --compact`. */
export function stateBoxCompactPlaceholderBemClasses(prefix: string): string {
  return delpiUiClass(
    `${prefix}-state-box ${prefix}-state-box--empty ${prefix}-state-box--compact`,
    "delpi-ui-state-box delpi-ui-state-box--empty delpi-ui-state-box--compact",
  );
}

/** Estado de erro inline (sem card) — dual `--error`. */
export function stateBoxErrorBemClasses(prefix: string): string {
  return delpiUiClass(
    `${prefix}-state-box ${prefix}-state-box--error`,
    "delpi-ui-state-box delpi-ui-state-box--error",
  );
}

function resolveRootClass(variant: StateBoxVariant, classNames: StateBoxClassNames): string {
  if (variant === "error") return classNames.rootError;
  if (variant === "empty") return classNames.rootEmpty;
  return classNames.rootLoading;
}

export function StateBoxPanel({
  variant,
  title,
  message,
  action,
  icon,
  iconClassName,
  classNames,
  onDismiss,
  dismissAriaLabel = "Fechar aviso",
}: StateBoxPanelProps) {
  const iconClass = [classNames.icon, iconClassName].filter(Boolean).join(" ");
  const rootClass = [
    resolveRootClass(variant, classNames),
    onDismiss ? classNames.dismissible : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      role={variant === "error" ? "alert" : "status"}
    >
      <span className={iconClass} aria-hidden="true">
        {icon}
      </span>
      <div>
        <h2>{title}</h2>
        {message ? <p>{message}</p> : null}
      </div>
      {action}
      {onDismiss ? (
        <button
          type="button"
          className={classNames.dismiss}
          onClick={onDismiss}
          aria-label={dismissAriaLabel}
        >
          <X size={16} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
}

export type DashboardStateBoxPanelProps = Omit<StateBoxPanelProps, "classNames" | "icon">;

export function createStateBoxPanel(config: {
  prefix: string;
  renderIcon: (variant: StateBoxVariant) => ReactNode;
  iconClassName?: (variant: StateBoxVariant) => string | undefined;
}) {
  const classNames = stateBoxBemClasses(config.prefix);

  return function DashboardStateBoxPanel(props: DashboardStateBoxPanelProps) {
    return (
      <StateBoxPanel
        icon={config.renderIcon(props.variant)}
        iconClassName={config.iconClassName?.(props.variant)}
        classNames={classNames}
        {...props}
      />
    );
  };
}
