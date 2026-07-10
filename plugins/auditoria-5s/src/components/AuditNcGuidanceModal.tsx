import { useEffect } from "react";
import { CheckCircle2, CircleHelp, X } from "lucide-react";

import { NC_PRIORITY_OPTIONS } from "../constants/audit5s";

const TIPS = [
  "Descreva objetivamente o que foi observado.",
  "Informe a causa raiz identificada.",
  "Defina responsável e prazo realistas.",
  "Priorize ações com maior impacto no posto.",
];

export function AuditNcGuidanceContent() {
  return (
    <div className="a5s-nc-guidance__content">
      <section className="a5s-nc-sidebar__card">
        <h3>Boas práticas para registrar NCs</h3>
        <ul className="a5s-nc-sidebar__tips">
          {TIPS.map((tip) => (
            <li key={tip}>
              <CheckCircle2 size={16} aria-hidden />
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="a5s-nc-sidebar__card">
        <h3>Legenda de prioridade</h3>
        <ul className="a5s-nc-sidebar__legend">
          {NC_PRIORITY_OPTIONS.map((item) => (
            <li key={item.value}>
              <span className={`a5s-priority-dot a5s-priority-dot--${item.tone}`} aria-hidden />
              <div>
                <strong>{item.label}</strong>
                <p>
                  {item.value === "high"
                    ? "Risco alto ou impacto imediato na operação."
                    : item.value === "medium"
                      ? "Risco moderado ou impacto relevante."
                      : "Risco baixo ou impacto limitado."}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

type ModalProps = {
  open: boolean;
  onClose: () => void;
};

export function AuditNcGuidanceModal({ open, onClose }: ModalProps) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="a5s-confirm-overlay" role="presentation" onClick={onClose}>
      <div
        className="a5s-nc-guidance-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="a5s-nc-guidance-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="a5s-nc-guidance-dialog__head">
          <div className="a5s-nc-guidance-dialog__title-wrap">
            <CircleHelp size={20} aria-hidden />
            <h2 id="a5s-nc-guidance-title">Orientações para registro de NC</h2>
          </div>
          <button
            type="button"
            className="a5s-nc-guidance-dialog__close"
            aria-label="Fechar orientações"
            onClick={onClose}
          >
            <X size={18} aria-hidden />
          </button>
        </header>

        <AuditNcGuidanceContent />

        <footer className="a5s-nc-guidance-dialog__actions">
          <button type="button" className="a5s-btn" onClick={onClose}>
            Entendi
          </button>
        </footer>
      </div>
    </div>
  );
}
