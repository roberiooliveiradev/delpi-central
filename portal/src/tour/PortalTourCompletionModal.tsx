import { Sparkles, Trophy, X } from "lucide-react";
import type { ExplorerLevel } from "./portalTourGamification";

type PortalTourCompletionModalProps = {
  explorerLevel: ExplorerLevel;
  earnedXp: number;
  requiredDone: number;
  requiredTotal: number;
  explorationDurationLabel?: string | null;
  onClose: () => void;
};

export function PortalTourCompletionModal({
  explorerLevel,
  earnedXp,
  requiredDone,
  requiredTotal,
  explorationDurationLabel,
  onClose,
}: PortalTourCompletionModalProps) {
  return (
    <div className="portal-tour-completion-backdrop" role="presentation">
      <div
        className="portal-tour-completion-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="portal-tour-completion-title"
      >
        <button
          type="button"
          className="portal-tour-completion-close"
          onClick={onClose}
          aria-label="Fechar"
        >
          <X size={18} aria-hidden />
        </button>

        <div className="portal-tour-completion-badge" aria-hidden>
          <Trophy size={28} />
        </div>

        <h2 id="portal-tour-completion-title" className="portal-tour-completion-title">
          Você conheceu a Minha DELPI!
        </h2>
        <p className="portal-tour-completion-subtitle">
          Parabéns — você completou a exploração do portal.
        </p>

        <dl className="portal-tour-completion-stats">
          <div>
            <dt>Nível</dt>
            <dd>{explorerLevel.label}</dd>
          </div>
          <div>
            <dt>XP conquistado</dt>
            <dd>{earnedXp}</dd>
          </div>
          <div>
            <dt>Desafios</dt>
            <dd>
              {requiredDone}/{requiredTotal}
            </dd>
          </div>
          {explorationDurationLabel ? (
            <div>
              <dt>Tempo de exploração</dt>
              <dd>{explorationDurationLabel}</dd>
            </div>
          ) : null}
        </dl>

        <button
          type="button"
          className="portal-tour-btn portal-tour-btn--primary portal-tour-completion-cta"
          onClick={onClose}
        >
          <Sparkles size={16} aria-hidden />
          Fechar
        </button>
      </div>
    </div>
  );
}
