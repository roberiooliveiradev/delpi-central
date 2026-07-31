import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, ClipboardList, RefreshCw } from "lucide-react";

import { getReportDefinition } from "../api/reportsApi";
import { ShortageItemNotesSection } from "../components/ShortageItemNotesSection";
import type { ReportDefinition } from "../types/reports";
import { formatBranchUnitLabel } from "../utils/format";
import {
  REPORTS_FOLLOW_UP_LIST_PATH,
  followUpPath,
} from "../utils/route";

type Props = {
  definitionId: string;
  initialProductCode?: string | null;
};

export function FollowUpNotesPage({
  definitionId,
  initialProductCode = null,
}: Props) {
  const [item, setItem] = useState<ReportDefinition | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const definition = await getReportDefinition(definitionId, signal);
        if (signal?.aborted) return;
        setItem(definition);
      } catch (err) {
        if (signal?.aborted) return;
        setError(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar a definição.",
        );
        setItem(null);
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [definitionId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);

  const branch = String(item?.params.branch ?? "01");
  const horizonDays = Number(item?.params.horizonDays ?? 30);
  const title = item?.name?.trim() || "Acompanhamentos";

  return (
    <div className="rp-page-content">
      <header className="rp-page-header">
        <div className="rp-page-header__shell">
          <div className="rp-page-header__main">
            <div className="rp-page-header__brand">
              <div className="rp-page-header__titles">
                <p className="rp-page-header__eyebrow">Delpi Reports</p>
                <div className="rp-page-header__title-row">
                  <h1>
                    <ClipboardList size={28} aria-hidden />
                    {loading ? "Carregando…" : title}
                  </h1>
                </div>
                <p className="rp-page-header__subtitle">
                  Registre previsões e comentários na Observação do e-mail —
                  sem alterar a configuração do relatório.
                </p>
              </div>
            </div>
            <div className="rp-page-header__actions">
              <a className="rp-btn rp-btn--ghost" href={REPORTS_FOLLOW_UP_LIST_PATH}>
                <ArrowLeft size={16} aria-hidden />
                Lista
              </a>
              <button
                type="button"
                className="rp-btn rp-btn--ghost"
                disabled={loading}
                onClick={() => void reload()}
              >
                <RefreshCw
                  size={16}
                  aria-hidden
                  className={loading ? "rp-spin" : undefined}
                />
                Atualizar
              </button>
            </div>
          </div>

          {item ? (
            <div className="rp-meta-strip" aria-label="Resumo">
              <div className="rp-meta-chip">
                <span>
                  <strong>Unidade</strong>
                  <em>{formatBranchUnitLabel(branch)}</em>
                </span>
              </div>
              <div className="rp-meta-chip">
                <span>
                  <strong>Horizonte</strong>
                  <em>{horizonDays} dias</em>
                </span>
              </div>
            </div>
          ) : null}

          <div className="rp-page-header__brand-bar" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
      </header>

      {error ? (
        <p className="rp-banner rp-banner--error" role="alert">
          {error}
        </p>
      ) : null}
      {statusMsg ? (
        <p className="rp-banner rp-banner--ok" role="status">
          {statusMsg}
        </p>
      ) : null}

      {loading && !item ? (
        <p className="rp-banner">Carregando definição…</p>
      ) : null}

      {item ? (
        <div className="rp-detail-stack">
          <ShortageItemNotesSection
            definitionId={definitionId}
            branch={branch}
            horizonDays={horizonDays}
            initialProductCode={initialProductCode ?? ""}
            onStatus={(message) => {
              setStatusMsg(message);
              setError(null);
            }}
            onError={(message) => {
              setError(message);
              setStatusMsg(null);
            }}
          />
          <p className="rp-inline-note">
            Link permanente desta tela:{" "}
            <code className="rp-code">{followUpPath(definitionId)}</code>
          </p>
        </div>
      ) : null}
    </div>
  );
}
