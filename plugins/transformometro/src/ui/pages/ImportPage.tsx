import { useState } from "react";
import { Upload } from "lucide-react";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  applySheetImport,
  previewSheetImport,
  type ImportPreviewResult,
} from "../../data/api/transformometroApi";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function ImportPage({ getAccessToken, pathname, onNavigate }: Props) {
  const [preview, setPreview] = useState<ImportPreviewResult | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [replaceExisting, setReplaceExisting] = useState(false);

  async function handlePreview() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setPreview(await previewSheetImport(getAccessToken));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na pré-visualização");
    } finally {
      setLoading(false);
    }
  }

  async function handleApply() {
    if (
      replaceExisting &&
      !window.confirm(
        "Substituir apaga todo o cadastro e o dashboard materializado. Continuar?"
      )
    ) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await applySheetImport(
        { replace_existing: replaceExisting, recalc_dashboard: true },
        getAccessToken
      );
      setResult(data as Record<string, unknown>);
      setPreview(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na importação");
    } finally {
      setLoading(false);
    }
  }

  const validation = preview?.validation;

  return (
    <TransformometroShell>
      <PageHeader
        title="Importar planilha"
        subtitle="Migração Transforma+ (Google Sheets) para o Postgres do Transformômetro"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.import}
        onNavigate={onNavigate}
      />

      <StatusAlerts error={error} loading={loading} hasData onRetry={() => void handlePreview()} />

      <section className="ds-card ds-cadastro-form">
        <h2 className="ds-section-title">Fonte de dados</h2>
        <p className="ds-hint">
          A API lê a planilha configurada em <code>TRANSFORMA_MAIS_SHEET_ID</code> e GIDs no
          ambiente do servidor. Use o script CLI com <code>--csv-dir</code> para imports offline.
        </p>

        <div className="ds-filter-box ds-filter-box--checkbox">
          <label>
            <input
              type="checkbox"
              checked={replaceExisting}
              onChange={(e) => setReplaceExisting(e.target.checked)}
            />
            Substituir cadastro existente (truncate)
          </label>
        </div>

        <div className="ds-cadastro-form__actions">
          <button
            type="button"
            className="ds-ghost-btn"
            disabled={loading}
            onClick={() => void handlePreview()}
          >
            Pré-visualizar
          </button>
          <button
            type="button"
            className="ds-primary-btn"
            disabled={loading || (validation !== undefined && !validation?.ok)}
            onClick={() => void handleApply()}
          >
            <Upload size={16} />
            Importar planilha
          </button>
        </div>
      </section>

      {validation ? (
        <section className="ds-card">
          <h2 className="ds-section-title">Validação</h2>
          <p>
            {validation.ok ? (
              <span className="ds-badge ds-badge--success">Planilha válida</span>
            ) : (
              <span className="ds-badge ds-badge--error">Erros encontrados</span>
            )}
          </p>
          <ul className="ds-cadastro-list">
            {Object.entries(validation.sheet_counts).map(([k, v]) => (
              <li key={k}>
                {k}: {v}
              </li>
            ))}
          </ul>
          {validation.errors.length > 0 ? (
            <ul className="ds-state-box">
              {validation.errors.slice(0, 15).map((msg) => (
                <li key={msg}>{msg}</li>
              ))}
            </ul>
          ) : null}
          {preview.sheet_summary ? (
            <dl className="ds-summary-metrics">
              <div className="ds-summary-metric">
                <dt>Economia líquida (planilha)</dt>
                <dd>
                  {Number(preview.sheet_summary.economia_liquida_total ?? 0).toLocaleString(
                    "pt-BR"
                  )}
                </dd>
              </div>
              <div className="ds-summary-metric">
                <dt>Soluções (planilha)</dt>
                <dd>{preview.sheet_summary.solucoes_implementadas ?? 0}</dd>
              </div>
            </dl>
          ) : null}
        </section>
      ) : null}

      {result ? (
        <section className="ds-card">
          <h2 className="ds-section-title">Resultado</h2>
          <pre className="ds-code-block">{JSON.stringify(result, null, 2)}</pre>
        </section>
      ) : null}
    </TransformometroShell>
  );
}
