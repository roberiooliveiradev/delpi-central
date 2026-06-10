import { Check, Sparkles, Trophy, X } from "lucide-react";

export type PortalTourLevelUpOverlayState = {
  id: string;
  questTitle: string;
  xp: number;
  categoryLabel: string;
  previousLevelLabel: string;
  levelLabel: string;
  message: string;
  progressPercent: number;
  categoryCompleteLabel?: string;
};

type PortalTourLevelUpOverlayProps = {
  celebration: PortalTourLevelUpOverlayState;
  onClose: () => void;
};

export function PortalTourLevelUpOverlay({
  celebration,
  onClose,
}: PortalTourLevelUpOverlayProps) {
  return (
    <div
      className="portal-tour-level-up-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="portal-tour-level-up-title"
      aria-describedby="portal-tour-level-up-desc"
    >
      <div className="portal-tour-level-up-card">
        <button
          type="button"
          className="portal-tour-level-up-close"
          onClick={onClose}
          aria-label="Fechar celebração"
        >
          <X size={18} aria-hidden />
        </button>

        <div className="portal-tour-level-up-icon" aria-hidden>
          <Sparkles size={22} />
        </div>

        <p className="portal-tour-level-up-kicker">Nova conquista!</p>
        <h2 id="portal-tour-level-up-title" className="portal-tour-level-up-title">
          Você subiu para {celebration.levelLabel}
        </h2>
        <p id="portal-tour-level-up-desc" className="portal-tour-level-up-message">
          {celebration.message}
        </p>

        <div className="portal-tour-level-up-details">
          <div className="portal-tour-level-up-detail">
            <Check size={15} aria-hidden />
            <span>
              Desafio concluído: <strong>{celebration.questTitle}</strong>
            </span>
          </div>
          {celebration.categoryCompleteLabel ? (
            <div className="portal-tour-level-up-detail">
              <Trophy size={15} aria-hidden />
              <span>
                Área «{celebration.categoryCompleteLabel}» concluída
              </span>
            </div>
          ) : null}
          <div className="portal-tour-level-up-detail">
            <span className="portal-tour-level-up-level-shift" aria-hidden>
              {celebration.previousLevelLabel}
            </span>
            <span className="portal-tour-level-up-level-arrow" aria-hidden>
              →
            </span>
            <span className="portal-tour-level-up-level-shift is-next">
              {celebration.levelLabel}
            </span>
          </div>
        </div>

        <div className="portal-tour-level-up-meta">
          <span>+{celebration.xp} XP</span>
          <span aria-hidden>·</span>
          <span>{celebration.categoryLabel}</span>
          <span aria-hidden>·</span>
          <span>{celebration.progressPercent}% do portal</span>
        </div>

        <button
          type="button"
          className="portal-tour-level-up-cta"
          onClick={onClose}
        >
          Continuar explorando
        </button>
      </div>
    </div>
  );
}
