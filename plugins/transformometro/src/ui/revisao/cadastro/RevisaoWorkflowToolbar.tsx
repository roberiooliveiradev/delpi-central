import { useState } from "react";
import type { AppProps } from "../../../App";
import {
  aprovarRevisao,
  rejeitarRevisao,
  submeterRevisaoAprovacao,
  type Revisao,
} from "../../../data/api/transformometroApi";
import {
  badgeClassStatusAprovacao,
  labelStatusAprovacao,
} from "../../../utils/revisaoWorkflowLabels";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisao: Revisao;
  onError: (message: string | null) => void;
  onUpdated: () => void;
  onActivate?: () => void | Promise<void>;
};

export function RevisaoWorkflowToolbar({
  revisao,
  getAccessToken,
  onError,
  onUpdated,
  onActivate,
}: Props) {
  const status = revisao.status_aprovacao ?? "rascunho";
  const [motivoRejeicao, setMotivoRejeicao] = useState("");
  const [showReject, setShowReject] = useState(false);
  const [busy, setBusy] = useState(false);

  async function run(action: () => void | Promise<unknown>) {
    onError(null);
    setBusy(true);
    try {
      await action();
      setShowReject(false);
      setMotivoRejeicao("");
      onUpdated();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro no workflow da revisão");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="ds-cadastro-panel__workflow">
      <span className="ds-cadastro-panel__workflow-meta">
        {revisao.versao_revisao} · {revisao.cenario_tipo}
        <span className={badgeClassStatusAprovacao(status)}>
          {labelStatusAprovacao(status)}
        </span>
        {revisao.revisao_ativa ? (
          <span className="ds-badge ds-badge--success">ativa</span>
        ) : null}
      </span>

      <div className="ds-cadastro-panel__workflow-actions">
        {(status === "rascunho" || status === "rejeitada") && (
          <button
            type="button"
            className="ds-primary-btn"
            disabled={busy}
            onClick={() =>
              void run(() => submeterRevisaoAprovacao(revisao.revisao_id, getAccessToken))
            }
          >
            Enviar para análise
          </button>
        )}
        {status === "em_analise" && (
          <>
            <button
              type="button"
              className="ds-primary-btn"
              disabled={busy}
              onClick={() =>
                void run(() => aprovarRevisao(revisao.revisao_id, getAccessToken))
              }
            >
              Aprovar
            </button>
            <button
              type="button"
              className="ds-ghost-btn"
              disabled={busy}
              onClick={() => setShowReject((v) => !v)}
            >
              Rejeitar…
            </button>
          </>
        )}
        {status === "aprovada" && !revisao.revisao_ativa && onActivate ? (
          <button
            type="button"
            className="ds-ghost-btn"
            disabled={busy}
            onClick={() => void run(onActivate)}
          >
            Definir como ativa
          </button>
        ) : null}
      </div>

      {status === "rejeitada" && revisao.motivo_rejeicao ? (
        <p className="ds-hint ds-cadastro-panel__workflow-reject">
          Motivo da rejeição: {revisao.motivo_rejeicao}
          {revisao.aprovado_por_email ? ` (${revisao.aprovado_por_email})` : ""}
        </p>
      ) : null}

      {showReject && status === "em_analise" ? (
        <form
          className="ds-cadastro-panel__workflow-reject-form"
          onSubmit={(e) => {
            e.preventDefault();
            void run(() =>
              rejeitarRevisao(revisao.revisao_id, motivoRejeicao.trim(), getAccessToken)
            );
          }}
        >
          <label className="ds-filter-box ds-filter-box--wide">
            Motivo da rejeição *
            <textarea
              required
              rows={2}
              value={motivoRejeicao}
              onChange={(e) => setMotivoRejeicao(e.target.value)}
            />
          </label>
          <div className="ds-cadastro-form__actions">
            <button type="submit" className="ds-primary-btn" disabled={busy || !motivoRejeicao.trim()}>
              Confirmar rejeição
            </button>
            <button
              type="button"
              className="ds-ghost-btn"
              onClick={() => setShowReject(false)}
            >
              Cancelar
            </button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
