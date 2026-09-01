import type { PropsWithChildren, ReactNode } from "react";
import "./IndicatorGoalForm.css";

export type SiAdminFormPanelShellConfig = {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  backLabel?: string;
};

type SiAdminFormPanelShellProps = PropsWithChildren<{
  shell: SiAdminFormPanelShellConfig;
  footer?: ReactNode;
}>;

export function SiAdminFormPanelShell({
  shell,
  footer,
  children,
}: SiAdminFormPanelShellProps) {
  const backLabel = shell.backLabel ?? "← Voltar";

  return (
    <div className="si-goal-form-panel">
      <header className="si-goal-form-panel__header">
        <div className="si-goal-form-panel__header-main">
          {shell.onBack ? (
            <button
              type="button"
              className="si-goal-form-panel__back"
              onClick={shell.onBack}
            >
              {backLabel}
            </button>
          ) : null}
          <div className="si-goal-form-panel__title-row">
            <h3 className="si-goal-form-panel__title">{shell.title}</h3>
            {shell.subtitle ? (
              <span className="si-goal-form-panel__cycle">{shell.subtitle}</span>
            ) : null}
          </div>
        </div>
      </header>

      <div className="si-goal-form-panel__body">{children}</div>

      {footer ? <div className="si-goal-form-panel__footer">{footer}</div> : null}
    </div>
  );
}
