import type { ReactNode } from "react";

import { PpActionButton } from "../../app/productionPulseUi";
import { branchLabel } from "../../constants/branches";
import { PRODUCTION_PULSE_BASE_PATH } from "../../constants/routes";
import { PP_HELP } from "../../content/helpTooltips";
import { navigateProductionPulse } from "../../utils/navigation";

type OperatorBrandBarProps = {
  branch: string;
  title: string;
  subtitle?: string;
  trailing?: ReactNode;
  showAdminLink?: boolean;
};

export function OperatorBrandBar({
  branch,
  title,
  subtitle,
  trailing,
  showAdminLink,
}: OperatorBrandBarProps) {
  return (
    <header className="pp-operator-brand-bar">
      <div className="pp-operator-brand-bar__main">
        <p className="pp-operator-brand-bar__eyebrow">
          PULSO · Filial {branchLabel(branch)}
        </p>
        <h1 className="pp-operator-brand-bar__title">{title}</h1>
        {subtitle ? <p className="pp-operator-brand-bar__subtitle">{subtitle}</p> : null}
      </div>
      <div className="pp-operator-brand-bar__actions">
        {trailing}
        {showAdminLink ? (
          <PpActionButton
            variant="ghost"
            className="pp-operator-brand-bar__btn"
            onClick={() => navigateProductionPulse(`${PRODUCTION_PULSE_BASE_PATH}?branch=${branch}`)}
            title={PP_HELP.operator.adminLink}
          >
            Painel admin
          </PpActionButton>
        ) : null}
      </div>
    </header>
  );
}
