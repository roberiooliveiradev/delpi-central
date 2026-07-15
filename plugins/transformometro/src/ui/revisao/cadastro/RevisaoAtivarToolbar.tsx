import { useState } from "react";
import type { Revisao } from "../../../data/api/transformometroApi";
import { cenarioLabel } from "../../../content/cenarioLabels";
import { DS_GHOST_BTN } from "../../../components/ghostChrome";

type Props = {
  revisao: Revisao;
  onError: (message: string | null) => void;
  onActivate?: () => void | Promise<void>;
  onDelete?: () => void | Promise<void>;
};

export function RevisaoAtivarToolbar({ revisao, onError, onActivate, onDelete }: Props) {
  const [busy, setBusy] = useState(false);

  async function handleActivate() {
    if (!onActivate) return;
    onError(null);
    setBusy(true);
    try {
      await onActivate();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao ativar revisão");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="ds-cadastro-panel__workflow">
      <span className="ds-cadastro-panel__workflow-meta">
        {revisao.versao_revisao} · {cenarioLabel(revisao.cenario_tipo)}
        {revisao.revisao_ativa ? (
          <span className="ds-badge ds-badge--success">ativa</span>
        ) : null}
      </span>

      <div className="ds-cadastro-panel__workflow-actions">
        {!revisao.revisao_ativa && onActivate ? (
          <button
            type="button"
            className="ds-primary-btn"
            disabled={busy}
            onClick={() => void handleActivate()}
          >
            Definir como ativa
          </button>
        ) : null}
        {onDelete ? (
          <button
            type="button"
            className={DS_GHOST_BTN}
            disabled={busy}
            onClick={() => void onDelete()}
          >
            Excluir revisão
          </button>
        ) : null}
      </div>
    </div>
  );
}
