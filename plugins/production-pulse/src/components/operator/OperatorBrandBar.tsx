import type { ReactNode } from "react";
import { LayoutDashboard, MapPinned } from "lucide-react";

import { PpActionButton, PpHintAction, PpPageHero, ppShellIcon } from "../../app/productionPulseUi";
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
              <PpHintAction hint={PP_HELP.operator.adminLink} ariaLabel="Ajuda: Painel admin">
                <PpActionButton
                  className="pp-operator-hero-btn"
                  aria-label="Painel admin"
                  onClick={() =>
                    navigateProductionPulse(`${PRODUCTION_PULSE_BASE_PATH}?branch=${branch}`)
                  }
                >
                  <LayoutDashboard size={16} aria-hidden />
                  Painel admin
                </PpActionButton>
              </PpHintAction>
            ) : null}
          </>
        ) : undefined
      }
    />
  );
}

/** Shared “trocar posto” hero control for operator surfaces — ícone + texto. */
export function OperatorChangePlacementButton({ onClick }: { onClick: () => void }) {
  return (
    <PpHintAction hint={PP_HELP.operator.changePlacement} ariaLabel="Ajuda: Trocar posto">
      <PpActionButton className="pp-operator-hero-btn" aria-label="Trocar posto" onClick={onClick}>
        <MapPinned size={16} aria-hidden />
        Trocar posto
      </PpActionButton>
    </PpHintAction>
  );
}
