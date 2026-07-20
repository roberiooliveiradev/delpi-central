import { GitCompareArrows } from "lucide-react";

import { dsGhostBtn } from "./ghostChrome";

type Props = {
  active: boolean;
  onChange: (active: boolean) => void;
  disabled?: boolean;
  /** Contagem opcional exibida ao lado do rótulo. */
  summary?: string | null;
};

/**
 * Liga/desliga o destaque visual de diferenças (vs referência ou conflitos).
 * Desligado por padrão — o consumidor controla o estado.
 */
export function DiffHighlightToggle({ active, onChange, disabled, summary }: Props) {
  return (
    <div className="tm-diff-highlight-toggle">
      <button
        type="button"
        className={active ? dsGhostBtn("active") : dsGhostBtn()}
        aria-pressed={active}
        disabled={disabled}
        onClick={() => onChange(!active)}
        title={
          active
            ? "Ocultar destaque de diferenças"
            : "Destacar nós alterados, novos ou removidos em relação à referência"
        }
      >
        <GitCompareArrows size={16} aria-hidden />
        {active ? "Ocultar diferenças" : "Destacar diferenças"}
      </button>
      {active && summary ? <p className="ds-hint tm-diff-highlight-toggle__summary">{summary}</p> : null}
    </div>
  );
}
