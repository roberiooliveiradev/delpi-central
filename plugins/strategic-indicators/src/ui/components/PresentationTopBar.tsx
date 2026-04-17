import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import {
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
import { PresentationModeToggle } from "./PresentationModeToggle";
import { StatusBadge } from "./StatusBadge";

type PresentationTopBarProps = {
  competence: string;
  sceneTitle: string;
  mode: "meeting" | "tv" | "slide";
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  branchOptions: Array<{ value: string; label: string }>;
  isRefreshing: boolean;
  referenceMonth: string;
  onReferenceMonthChange: (value: string) => void;
  onModeChange: (value: "meeting" | "tv" | "slide") => void;
  onViewModeChange: (value: StrategicIndicatorsViewMode) => void;
  onBranchChange: (value: string) => void;
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
  viewMode,
  branch,
  branchOptions,
  isRefreshing,
  referenceMonth,
  onReferenceMonthChange,
  onModeChange,
  onViewModeChange,
  onBranchChange,
}: PresentationTopBarProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [sceneTitle, competence, mode, viewMode, branch, referenceMonth]);

  return (
    <section
      className={`si-presentation-topbar ${menuOpen ? "is-menu-open" : ""}`}
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
            aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((current) => !current)}
          >
            {menuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      <div className="si-presentation-topbar__meta">
        <div className="si-presentation-topbar__mode-group">
          <div className="si-presentation-topbar__meta-item">
            <span>Modo</span>
            <strong>{getModeLabel(mode)}</strong>
          </div>

          <PresentationModeToggle mode={mode} onChange={onModeChange} />
        </div>

        <div className="si-presentation-topbar__meta-item">
          <span>Visão</span>

          <div
            className="si-segmented-control"
            role="group"
            aria-label="Modo de visão"
          >
            <button
              type="button"
              className={viewMode === "consolidated" ? "is-active" : ""}
              onClick={() => onViewModeChange("consolidated")}
            >
              Consolidado
            </button>

            <button
              type="button"
              className={viewMode === "branch" ? "is-active" : ""}
              onClick={() => onViewModeChange("branch")}
            >
              Filial
            </button>
          </div>
        </div>

        {viewMode === "branch" ? (
          <label className="si-presentation-topbar__filter">
            <span>Filial</span>
            <select
              value={branch}
              onChange={(event) => onBranchChange(event.target.value)}
            >
              {branchOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        ) : null}

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