import { copy } from "../content/copy";
import type { BlockState } from "../types";

type FinBlockStateProps = {
  block: BlockState | undefined;
  /** Mensagem exibida quando o bloco veio disponível, porém vazio. */
  emptyMessage?: string;
  empty?: boolean;
};

/** Bloco indisponível não derruba a tela: mostra o motivo no lugar do dado. */
export function FinBlockState({ block, emptyMessage, empty }: FinBlockStateProps) {
  if (block && block.available === false) {
    return (
      <p className="fin-block-state fin-block-state--error" role="status">
        {block.error || copy.home.loadError}
      </p>
    );
  }
  if (empty) {
    return <p className="fin-block-state">{emptyMessage ?? copy.empty}</p>;
  }
  return null;
}
