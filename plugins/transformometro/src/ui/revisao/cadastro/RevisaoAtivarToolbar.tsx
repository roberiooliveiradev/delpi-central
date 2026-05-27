import { useState } from "react";
import type { AppProps } from "../../../App";
import type { Revisao } from "../../../data/api/transformometroApi";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisao: Revisao;
  onError: (message: string | null) => void;
  onActivate?: () => void | Promise<void>;
};

export function RevisaoAtivarToolbar({ revisao, onError, onActivate }: Props) {
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
        {revisao.versao_revisao} · {revisao.cenario_tipo}
        {revisao.revisao_ativa ? (
          <span className="ds-badge ds-badge--success">ativa</span>
        ) : null}
      </span>

      {!revisao.revisao_ativa && onActivate ? (
        <div className="ds-cadastro-panel__workflow-actions">
          <button
            type="button"
            className="ds-primary-btn"
            disabled={busy}
            onClick={() => void handleActivate()}
          >
            Definir como ativa
          </button>
        </div>
      ) : null}
    </div>
  );
}
