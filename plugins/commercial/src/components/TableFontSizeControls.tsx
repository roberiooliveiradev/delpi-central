import { Minus, Plus, RotateCcw } from "lucide-react";

type TableFontSizeControlsProps = {
  fontSize: number;
  canIncrease: boolean;
  canDecrease: boolean;
  isDefault: boolean;
  onIncrease: () => void;
  onDecrease: () => void;
  onReset: () => void;
};

export function TableFontSizeControls({
  fontSize,
  canIncrease,
  canDecrease,
  isDefault,
  onIncrease,
  onDecrease,
  onReset,
}: TableFontSizeControlsProps) {
  return (
    <div className="pva-table-font-size" aria-label="Tamanho da fonte da tabela">
      <span className="pva-table-font-size__label">Fonte</span>
      <div className="pva-table-font-size__controls">
        <button
          type="button"
          className="pva-btn pva-btn--ghost pva-btn--sm pva-table-font-size__btn"
          aria-label="Diminuir fonte da tabela"
          disabled={!canDecrease}
          onClick={onDecrease}
        >
          <Minus size={14} aria-hidden="true" />
        </button>
        <span className="pva-table-font-size__value" aria-live="polite">
          {fontSize}px
        </span>
        <button
          type="button"
          className="pva-btn pva-btn--ghost pva-btn--sm pva-table-font-size__btn"
          aria-label="Aumentar fonte da tabela"
          disabled={!canIncrease}
          onClick={onIncrease}
        >
          <Plus size={14} aria-hidden="true" />
        </button>
        {!isDefault ? (
          <button
            type="button"
            className="pva-btn pva-btn--ghost pva-btn--sm pva-table-font-size__btn"
            aria-label="Restaurar fonte padrão da tabela"
            onClick={onReset}
          >
            <RotateCcw size={14} aria-hidden="true" />
          </button>
        ) : null}
      </div>
    </div>
  );
}
