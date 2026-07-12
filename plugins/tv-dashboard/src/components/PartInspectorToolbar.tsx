import type { ReactNode } from "react";
import { ArrowLeft, EyeOff, PenLine } from "lucide-react";

export type PartInspectorToolbarProps = {
  onBack: () => void;
  backLabel?: string;
  onEditOnStage?: () => void;
  editLabel?: string;
  onHide?: () => void;
  hideLabel?: string;
  hideDanger?: boolean;
  hint?: ReactNode;
};

/**
 * Barra de ações do inspetor de parte (KPI / gráfico / tabela).
 * Empilha botões em coluna para caber no painel lateral sem quebra feia.
 */
export function PartInspectorToolbar({
  onBack,
  backLabel = "Voltar",
  onEditOnStage,
  editLabel = "Editar no palco",
  onHide,
  hideLabel = "Ocultar",
  hideDanger = false,
  hint,
}: PartInspectorToolbarProps) {
  return (
    <div className="td-part-inspector-toolbar">
      <div className="td-part-inspector-toolbar__actions" role="toolbar" aria-label="Ações da parte">
        <button type="button" className="td-part-inspector-toolbar__btn" onClick={onBack}>
          <ArrowLeft size={14} aria-hidden="true" />
          <span>{backLabel}</span>
        </button>
        {onEditOnStage ? (
          <button type="button" className="td-part-inspector-toolbar__btn" onClick={onEditOnStage}>
            <PenLine size={14} aria-hidden="true" />
            <span>{editLabel}</span>
          </button>
        ) : null}
        {onHide ? (
          <button
            type="button"
            className={`td-part-inspector-toolbar__btn${hideDanger ? " td-part-inspector-toolbar__btn--danger" : ""}`}
            onClick={onHide}
          >
            <EyeOff size={14} aria-hidden="true" />
            <span>{hideLabel}</span>
          </button>
        ) : null}
      </div>
      {hint ? <p className="td-deck-inspector__hint td-part-inspector-toolbar__hint">{hint}</p> : null}
    </div>
  );
}
