import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import { PresentationModeToggle } from "./PresentationModeToggle";

type PresentationTopBarProps = {
  competence: string;
  sceneTitle: string;
  mode: "meeting" | "tv" | "slide";
  isRefreshing: boolean;
  referenceMonth: string;
  onReferenceMonthChange: (value: string) => void;
  onModeChange: (mode: "meeting" | "tv" | "slide") => void;
};

function getModeLabel(mode: PresentationTopBarProps["mode"]) {
  if (mode === "meeting") return "Reunião";
  if (mode === "tv") return "TV";
  return "Slide";
}

export function PresentationTopBar({
  competence,
  sceneTitle,
  mode,
  isRefreshing,
  referenceMonth,
  onReferenceMonthChange,
  onModeChange,
}: PresentationTopBarProps) {
  const [isCollapsedMenuOpen, setIsCollapsedMenuOpen] = useState(false);

  useEffect(() => {
    setIsCollapsedMenuOpen(false);
  }, [sceneTitle, referenceMonth, mode]);

  return (
    <section
      className={`si-presentation-topbar ${
        isCollapsedMenuOpen ? "is-menu-open" : ""
      }`}
    >
      <div className="si-presentation-topbar__identity">
        <span className="si-presentation-topbar__eyebrow">
          Apresentação Executiva
        </span>

        <div className="si-presentation-topbar__title-row">
          <div className="si-presentation-topbar__title-group">
            <h2 className="si-presentation-topbar__title">{sceneTitle}</h2>
            <p className="si-presentation-topbar__subtitle">
              Competência {competence}
            </p>
          </div>

          <button
            type="button"
            className="si-presentation-topbar__menu-toggle"
            aria-label={
              isCollapsedMenuOpen ? "Fechar menu da apresentação" : "Abrir menu da apresentação"
            }
            aria-expanded={isCollapsedMenuOpen}
            onClick={() => setIsCollapsedMenuOpen((current) => !current)}
          >
            {isCollapsedMenuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      <div className="si-presentation-topbar__meta">
        <div
          className="si-presentation-topbar__mode-group"
          role="group"
          aria-label="Modo de exibição"
        >
          <div className="si-presentation-topbar__meta-item">
            <span>Modo</span>
            <strong>{getModeLabel(mode)}</strong>
          </div>

          <PresentationModeToggle mode={mode} onChange={onModeChange} />
        </div>

        <label className="si-presentation-topbar__filter">
          <span>Mês de referência</span>
          <input
            type="month"
            value={referenceMonth}
            onChange={(event) => onReferenceMonthChange(event.target.value)}
          />
        </label>

        <div className="si-presentation-topbar__status">
          <StatusBadge
            label={isRefreshing ? "Atualizando" : "API real"}
            variant={isRefreshing ? "neutral" : "success"}
          />
        </div>
      </div>
    </section>
  );
}