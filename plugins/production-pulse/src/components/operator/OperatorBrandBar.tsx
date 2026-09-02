import type { ReactNode } from "react";

import { PpActionButton, PpPageHero, ppShellIcon } from "../../app/productionPulseUi";
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
  const hasActions = Boolean(trailing) || showAdminLink;

  return (
    <PpPageHero
      eyebrow={`${PP_HELP.operator.brandEyebrowPrefix} · Filial ${branchLabel(branch)}`}
      title={title}
      description={subtitle}
      badge={ppShellIcon}
      actions={
        hasActions ? (
          <>
            {trailing}
            {showAdminLink ? (
              <PpActionButton
                variant="ghost"
                className="pp-operator-hero-btn"
                onClick={() =>
                  navigateProductionPulse(`${PRODUCTION_PULSE_BASE_PATH}?branch=${branch}`)
                }
                title={PP_HELP.operator.adminLink}
              >
                Painel admin
              </PpActionButton>
            ) : null}
          </>
        ) : undefined
      }
    />
  );
}
