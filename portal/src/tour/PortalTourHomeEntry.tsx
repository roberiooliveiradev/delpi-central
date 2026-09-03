import { motion } from "framer-motion";
import { ArrowRight, Trophy } from "lucide-react";
import {
  openPortalTourPanel,
  resumePortalTour,
  usePortalTourSession,
} from "./portalTourSession";
import type { PortalTourHomeProgress } from "./usePortalTourHomeProgress";

type Props = {
  home: PortalTourHomeProgress;
};

export function PortalTourHomeEntry({ home }: Props) {
  const session = usePortalTourSession();

  if (!home.visible) return null;

  const valueLabel =
    home.requiredTotal > 0
      ? `${home.requiredDone}/${home.requiredTotal}`
      : home.loading
        ? "···"
        : "Explorar";
  const subLabel = home.loading
    ? home.progressPercent > 0 || home.requiredTotal > 0
      ? `${home.progressPercent}% · ${home.explorerLevel}`
      : "Carregando…"
    : home.newQuestCount > 0
      ? `${home.progressPercent}% · ${home.newQuestCount} novo${home.newQuestCount === 1 ? "" : "s"}`
      : `${home.progressPercent}% · ${home.explorerLevel}`;

  const handleOpen = () => {
    if (home.loading) return;

    if (session.sessionActive) {
      openPortalTourPanel();
      return;
    }
    resumePortalTour();
  };

  return (
    <motion.button
      type="button"
      className={[
        "home-summary-card",
        "portal-tour-home-entry",
        home.loading ? "portal-tour-home-entry--loading" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-tour="home-portal-tour-resume"
      aria-busy={home.loading}
      disabled={home.loading}
      onClick={handleOpen}
      initial={false}
      whileHover={home.loading ? undefined : { y: -2 }}
      whileTap={home.loading ? undefined : { scale: 0.98 }}
    >
      <span className="home-summary-icon">
        <Trophy size={18} aria-hidden />
      </span>

      <span className="home-summary-main">
        <span className="home-summary-title">Descubra o portal</span>
        <span className="home-summary-value">{valueLabel}</span>
        <span className="home-summary-sub">{subLabel}</span>
      </span>

      <span className="home-summary-arrow">
        <ArrowRight size={16} aria-hidden />
      </span>
    </motion.button>
  );
}
