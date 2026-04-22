import { useEffect, useMemo, useState } from "react";
import { Expand, Minimize } from "lucide-react";
import { LoadingActivityBadge } from "./LoadingActivityBadge";
import { StatusBadge } from "./StatusBadge";

type PresentationMode = "meeting" | "tv" | "slide";
type StrategicIndicatorsViewMode = "consolidated" | "branch";

type BranchOption = {
  value: string;
  label: string;
};

type MonthsOption = {
  value: number;
  label: string;
};

type PresentationTopBarProps = {
  competence: string;
  sceneTitle: string;
  mode: PresentationMode;
  viewMode: StrategicIndicatorsViewMode;
  branch: string;
  branchOptions: BranchOption[];
  months: number;
  monthsOptions?: MonthsOption[];
  isRefreshing: boolean;
  referenceMonth: string;
  onReferenceMonthChange: (value: string) => void;
  onModeChange: (value: PresentationMode) => void;
  onViewModeChange: (value: StrategicIndicatorsViewMode) => void;
  onBranchChange: (value: string) => void;
  onMonthsChange: (value: number) => void;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
};

const DEFAULT_MONTHS_OPTIONS: MonthsOption[] = [
  { value: 3, label: "3 meses" },
  { value: 6, label: "6 meses" },
  { value: 12, label: "12 meses" },
];

function shouldStartCollapsed(mode: PresentationMode) {
  return mode === "tv" || mode === "slide";
}

export function PresentationTopBar({
  competence,
  sceneTitle,
  mode,
  viewMode,
  branch,
  branchOptions,
  months,
  monthsOptions = DEFAULT_MONTHS_OPTIONS,
  isRefreshing,
  referenceMonth,
  onReferenceMonthChange,
  onModeChange,
  onViewModeChange,
  onBranchChange,
  onMonthsChange,
  isFullscreen = false,
  onToggleFullscreen,
}: PresentationTopBarProps) {
  const showBranchFilter = viewMode === "branch";

  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(() => {
    if (typeof window !== "undefined" && window.innerWidth <= 900) {
      return false;
    }

    return !shouldStartCollapsed(mode);
  });

  const isCollapsed = useMemo(() => !isMenuOpen, [isMenuOpen]);

  function handleToggleControls() {
    setIsMenuOpen((current) => !current);
  }

  useEffect(() => {
    function handleResize() {
      if (window.innerWidth <= 900) {
        setIsMenuOpen(false);
        return;
      }

      setIsMenuOpen(!shouldStartCollapsed(mode));
    }

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [mode]);

  useEffect(() => {
    if (typeof window !== "undefined" && window.innerWidth <= 900) {
      setIsMenuOpen(false);
      return;
    }

    setIsMenuOpen(!shouldStartCollapsed(mode));
  }, [mode]);

  useEffect(() => {
    if (typeof window !== "undefined" && window.innerWidth <= 900) {
      setIsMenuOpen(false);
      return;
    }

    setIsMenuOpen(!shouldStartCollapsed(mode));
  }, [mode]);

  return (
    <section
      className={`si-presentation-topbar${
        isMenuOpen ? " is-menu-open" : ""
      }${isCollapsed ? " is-collapsed" : ""}`}
    >
      <div className="si-presentation-topbar__identity">
        <div className="si-presentation-topbar__title-row">
          <div className="si-presentation-topbar__title-group">
            <span className="si-presentation-topbar__eyebrow">
              Apresentação Executiva
            </span>

            <h2 className="si-presentation-topbar__title">{sceneTitle}</h2>

            <p className="si-presentation-topbar__subtitle">
              Competência {competence}
            </p>
          </div>

          <button
            type="button"
            className="si-presentation-topbar__menu-toggle"
            aria-label={isMenuOpen ? "Recolher filtros" : "Expandir filtros"}
            aria-expanded={isMenuOpen}
            onClick={handleToggleControls}
          >
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              {isMenuOpen ? (
                <path
                  d="M6 6l12 12M18 6L6 18"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              ) : (
                <>
                  <path
                    d="M4 7h16"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                  <path
                    d="M4 12h16"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                  <path
                    d="M4 17h16"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      <div className="si-presentation-topbar__meta">
        {onToggleFullscreen ? (
        <div className="si-presentation-topbar__meta-actions">
          <button
            type="button"
            className="si-presentation-topbar__fullscreen-toggle"
            aria-label={isFullscreen ? "Sair da tela cheia" : "Entrar em tela cheia"}
            aria-pressed={isFullscreen}
            onClick={onToggleFullscreen}
          >
            {isFullscreen ? (
              <Minimize size={18} aria-hidden="true" />
            ) : (
              <Expand size={18} aria-hidden="true" />
            )}
          </button>
        </div>
      ) : null}
        <div className="si-presentation-topbar__mode-group">
          <div
            className="si-presentation-mode-toggle"
            role="tablist"
            aria-label="Modo da apresentação"
          >
            <button
              type="button"
              className={`si-presentation-mode-toggle__button${
                mode === "meeting" ? " is-active" : ""
              }`}
              onClick={() => onModeChange("meeting")}
              aria-pressed={mode === "meeting"}
            >
              Reunião
            </button>

            <button
              type="button"
              className={`si-presentation-mode-toggle__button${
                mode === "tv" ? " is-active" : ""
              }`}
              onClick={() => onModeChange("tv")}
              aria-pressed={mode === "tv"}
            >
              TV
            </button>

            <button
              type="button"
              className={`si-presentation-mode-toggle__button${
                mode === "slide" ? " is-active" : ""
              }`}
              onClick={() => onModeChange("slide")}
              aria-pressed={mode === "slide"}
            >
              Slide
            </button>
          </div>
        </div>

        <div className="si-presentation-topbar__mode-group">
          <div
            className="si-presentation-mode-toggle"
            role="tablist"
            aria-label="Visão da apresentação"
          >
            <button
              type="button"
              className={`si-presentation-mode-toggle__button${
                viewMode === "consolidated" ? " is-active" : ""
              }`}
              onClick={() => onViewModeChange("consolidated")}
              aria-pressed={viewMode === "consolidated"}
            >
              Consolidado
            </button>

            <button
              type="button"
              className={`si-presentation-mode-toggle__button${
                viewMode === "branch" ? " is-active" : ""
              }`}
              onClick={() => onViewModeChange("branch")}
              aria-pressed={viewMode === "branch"}
            >
              Filial
            </button>
          </div>
        </div>

        {showBranchFilter ? (
          <label className="si-presentation-topbar__filter">
            <span>Filial</span>
            <select
              value={branch}
              onChange={(event) => onBranchChange(event.target.value)}
            >
              {branchOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
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

        <label className="si-presentation-topbar__filter">
          <span>Janela de tendência</span>
          <select
            value={String(months)}
            onChange={(event) => onMonthsChange(Number(event.target.value))}
          >
            {monthsOptions.map((option) => (
              <option key={option.value} value={String(option.value)}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <div className="si-presentation-topbar__status">
          {isRefreshing ? (
            <LoadingActivityBadge label="Atualizando" tone="info" />
          ) : (
            <StatusBadge label="API real" variant="success" />
          )}
        </div>
      </div>

      <button
        type="button"
        className="si-presentation-topbar__edge-toggle"
        aria-label={isMenuOpen ? "Recolher filtros" : "Expandir filtros"}
        aria-expanded={isMenuOpen}
        onClick={handleToggleControls}
      >
        <span className="si-presentation-topbar__edge-toggle-pill">
          <span
            className={`si-presentation-topbar__edge-toggle-icon${
              isMenuOpen ? " is-open" : ""
            }`}
            aria-hidden="true"
          >
            <svg viewBox="0 0 20 20" fill="none">
              <path
                d="M5 8l5 5 5-5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
        </span>
      </button>
    </section>
  );
}