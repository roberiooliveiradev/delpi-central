import { Clock, Compass } from "lucide-react";
import { HelpTooltip } from "../components/HelpTooltip";
import { Button } from "../ui-kit";
import {
  dismissPortalTour,
  openPortalTourPanel,
  resumePortalTour,
  usePortalTourSession,
} from "./portalTourSession";
import type { PortalTourHomeProgress } from "./usePortalTourHomeProgress";
import "./PortalTourHomeBanner.css";

type Props = {
  home: PortalTourHomeProgress;
};

export function PortalTourHomeBanner({ home }: Props) {
  const session = usePortalTourSession();

  if (!home.visible) return null;

  const valueLabel =
    home.requiredTotal > 0
      ? `${home.requiredDone}/${home.requiredTotal}`
      : home.loading
        ? "···"
        : "0/6";

  const handleExplore = () => {
    if (home.loading) return;
    if (session.sessionActive) {
      openPortalTourPanel();
      return;
    }
    resumePortalTour();
  };

  const handleDismiss = () => {
    if (home.loading) return;
    dismissPortalTour();
  };

  return (
    <section
      className={[
        "portal-tour-home-banner",
        home.loading ? "portal-tour-home-banner--loading" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-tour="home-portal-tour-banner"
      aria-label="Descubra o portal"
    >
      <div className="portal-tour-home-banner__icon" aria-hidden>
        <Compass size={20} />
      </div>

      <div className="portal-tour-home-banner__copy">
        <div className="portal-tour-home-banner__title-row">
          <h2 className="portal-tour-home-banner__title">Descubra o portal</h2>
          <HelpTooltip
            content="Checklist opcional para conhecer apps, avisos e sua conta. Não é um chat — explore no seu ritmo ou escolha Agora não."
            ariaLabel="Ajuda: Descubra o portal"
          />
          <span className="portal-tour-home-banner__count">{valueLabel}</span>
          {home.newQuestCount > 0 ? (
            <span className="portal-tour-home-banner__new">
              {home.newQuestCount}{" "}
              {home.newQuestCount === 1 ? "novo" : "novos"}
            </span>
          ) : null}
        </div>
        <p className="portal-tour-home-banner__subtitle">
          {home.loading
            ? "Carregando…"
            : "Seis passos para conhecer apps, avisos e sua conta."}
        </p>
      </div>

      <div className="portal-tour-home-banner__actions">
        <Button
          variant="primary"
          size="md"
          icon={<Compass size={16} />}
          onClick={handleExplore}
          disabled={home.loading}
        >
          Explorar
        </Button>
        <Button
          variant="secondary"
          size="md"
          icon={<Clock size={16} />}
          onClick={handleDismiss}
          disabled={home.loading}
        >
          Agora não
        </Button>
      </div>
    </section>
  );
}
