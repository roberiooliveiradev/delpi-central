import { useCallback, useRef, useState } from "react";
import { AlertTriangle, ArrowDownUp, Download, FileJson, RefreshCw, Upload } from "lucide-react";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import {
  applyJsonImport,
  downloadJsonExport,
  previewJsonImport,
  type JsonBackupBundle,
  type JsonImportMode,
  type JsonImportPreview,
} from "../../data/api/transformometroApi";
import "./DataTransferPage.css";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

const ENTITY_LABELS: Record<string, string> = {
  processos: "Processos",
  revisoes: "Revisões",
  medicoes: "Medições",
  investimentos: "Investimentos",
  recursos_compartilhados: "Recursos compartilhados",
  recurso_custos: "Custos de recurso",
  revisao_recursos_compartilhados: "Vínculos revisão ↔ recurso",
};

export function DataTransferPage({ getAccessToken, pathname, onNavigate }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [mode, setMode] = useState<JsonImportMode>("merge");
  const [bundle, setBundle] = useState<JsonBackupBundle | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [preview, setPreview] = useState<JsonImportPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const onExport = useCallback(async () => {
    clearMessages();
    setBusy("export");
    try {
      await downloadJsonExport(getAccessToken);
      setSuccess("Exportação concluída — arquivo JSON baixado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar.");
    } finally {
      setBusy(null);
    }
  }, [getAccessToken]);

  const onFileChange = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    clearMessages();
    setPreview(null);
    const file = event.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as JsonBackupBundle;
      setBundle(parsed);
    } catch {
      setBundle(null);
      setError("Arquivo inválido — envie um JSON exportado pelo Transformômetro.");
    }
  }, []);

  const onPreview = useCallback(async () => {
    if (!bundle) {
      setError("Selecione um arquivo JSON antes de pré-visualizar.");
      return;
    }
    clearMessages();
    setBusy("preview");
    try {
      const result = await previewJsonImport(bundle, mode, getAccessToken);
      setPreview(result);
      if (!result.valid) {
        setError((result.errors ?? []).join(" ") || "Pacote inválido.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na pré-visualização.");
    } finally {
      setBusy(null);
    }
  }, [bundle, mode, getAccessToken]);

  const onApply = useCallback(async () => {
    if (!bundle) {
      setError("Selecione um arquivo JSON antes de importar.");
      return;
    }
    if (mode === "replace") {
      const ok = window.confirm(
        "Substituir todos os dados apagará processos, revisões, medições, investimentos e recursos atuais. Deseja continuar?"
      );
      if (!ok) return;
    }
    clearMessages();
    setBusy("apply");
    try {
      const result = await applyJsonImport(bundle, mode, getAccessToken);
      setPreview(result as JsonImportPreview);
      const rows = result.recalc?.rows_upserted ?? 0;
      setSuccess(
        `Importação concluída (${mode === "replace" ? "substituição total" : "mesclagem por ID"}). Dashboard recalculado (${rows} linhas derivadas).`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na importação.");
    } finally {
      setBusy(null);
    }
  }, [bundle, mode, getAccessToken]);

  const selectMode = (next: JsonImportMode) => {
    setMode(next);
    setPreview(null);
  };

  return (
    <TransformometroShell>
      <PageHeader
        title="Exportar / Importar JSON"
        subtitle="Backup completo do cadastro (processos, revisões, medições, investimentos e recursos)."
        currentPath={pathname}
        onNavigate={onNavigate}
      />

      <div className="tm-data-transfer">
        {error ? (
          <div className="ds-state ds-state--error" role="alert">
            <p>{error}</p>
          </div>
        ) : null}
        {success ? (
          <div className="ds-state ds-state--success" role="status">
            <p>{success}</p>
          </div>
        ) : null}

        <div className="tm-data-transfer__grid">
          <section className="ds-card tm-data-transfer__panel tm-data-transfer__panel--export">
            <div className="tm-data-transfer__panel-head">
              <span className="tm-data-transfer__panel-icon" aria-hidden>
                <Download size={22} strokeWidth={1.75} />
              </span>
              <div className="tm-data-transfer__panel-text">
                <h2 className="ds-section-title">Exportar</h2>
                <p className="ds-hint">
                  Gera um arquivo <code>.json</code> com todo o cadastro atual para backup ou
                  transferência entre ambientes.
                </p>
              </div>
            </div>
            <button
              type="button"
              className="ds-primary-btn"
              disabled={busy !== null}
              onClick={() => void onExport()}
            >
              <Download size={16} aria-hidden />
              {busy === "export" ? "Exportando…" : "Baixar backup JSON"}
            </button>
          </section>

          <section className="ds-card tm-data-transfer__panel tm-data-transfer__panel--import">
            <div className="tm-data-transfer__panel-head">
              <span className="tm-data-transfer__panel-icon" aria-hidden>
                <Upload size={22} strokeWidth={1.75} />
              </span>
              <div className="tm-data-transfer__panel-text">
                <h2 className="ds-section-title">Importar</h2>
                <p className="ds-hint">
                  Envie um backup exportado neste app. Pré-visualize o impacto antes de aplicar.
                </p>
              </div>
            </div>

            <div>
              <p className="tm-data-transfer__field-label">Modo de importação</p>
              <div className="tm-data-transfer__modes" role="radiogroup" aria-label="Modo de importação">
                <label
                  className={`tm-data-transfer__mode${
                    mode === "merge" ? " tm-data-transfer__mode--active" : ""
                  }`}
                >
                  <input
                    type="radio"
                    name="import-mode"
                    checked={mode === "merge"}
                    onChange={() => selectMode("merge")}
                  />
                  <span className="tm-data-transfer__mode-title">
                    <ArrowDownUp size={14} style={{ verticalAlign: -2, marginRight: 6 }} aria-hidden />
                    Mesclar por ID
                  </span>
                  <span className="tm-data-transfer__mode-desc">
                    Atualiza registros existentes e inclui novos. O que não estiver no arquivo
                    permanece no banco.
                  </span>
                </label>
                <label
                  className={`tm-data-transfer__mode tm-data-transfer__mode--danger${
                    mode === "replace" ? " tm-data-transfer__mode--active" : ""
                  }`}
                >
                  <input
                    type="radio"
                    name="import-mode"
                    checked={mode === "replace"}
                    onChange={() => selectMode("replace")}
                  />
                  <span className="tm-data-transfer__mode-title">
                    <AlertTriangle size={14} style={{ verticalAlign: -2, marginRight: 6 }} aria-hidden />
                    Substituir tudo
                  </span>
                  <span className="tm-data-transfer__mode-desc">
                    Apaga o cadastro atual e importa somente o conteúdo do JSON.
                  </span>
                </label>
              </div>
            </div>

            <div
              className={`tm-data-transfer__file-block${
                fileName ? " tm-data-transfer__file-block--has-file" : ""
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="application/json,.json"
                hidden
                onChange={(e) => void onFileChange(e)}
              />
              <div className="tm-data-transfer__file-row">
                <FileJson size={20} aria-hidden style={{ color: "var(--ds-accent)", flexShrink: 0 }} />
                <span
                  className={`tm-data-transfer__file-name${
                    fileName ? " tm-data-transfer__file-name--selected" : ""
                  }`}
                  title={fileName ?? undefined}
                >
                  {fileName ?? "Nenhum arquivo selecionado"}
                </span>
                <button
                  type="button"
                  className="ds-ghost-btn"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Escolher arquivo
                </button>
              </div>
            </div>

            <div className="tm-data-transfer__toolbar">
              <button
                type="button"
                className="ds-ghost-btn"
                disabled={!bundle || busy !== null}
                onClick={() => void onPreview()}
              >
                <RefreshCw size={16} aria-hidden />
                {busy === "preview" ? "Analisando…" : "Pré-visualizar"}
              </button>
              <button
                type="button"
                className="ds-primary-btn"
                disabled={!bundle || busy !== null}
                onClick={() => void onApply()}
              >
                {busy === "apply" ? "Importando…" : "Aplicar importação"}
              </button>
            </div>

            {preview?.valid && preview.entities ? (
              <div className="tm-data-transfer__preview">
                <h3 className="ds-section-title tm-data-transfer__preview-title">
                  Resumo da pré-visualização
                </h3>
                <div className="ds-table-wrap">
                  <table className="ds-table">
                    <thead>
                      <tr>
                        <th>Entidade</th>
                        <th>No arquivo</th>
                        <th>Inserir</th>
                        <th>Atualizar</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(preview.entities).map(([key, stats]) => (
                        <tr key={key}>
                          <td>{ENTITY_LABELS[key] ?? key}</td>
                          <td>{stats.total}</td>
                          <td>{stats.insert}</td>
                          <td>{stats.update}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {preview.current_counts ? (
                  <p className="tm-data-transfer__counts">
                    Cadastro atual no banco:{" "}
                    {Object.entries(preview.current_counts)
                      .map(([k, n]) => `${ENTITY_LABELS[k] ?? k}: ${n}`)
                      .join(" · ")}
                  </p>
                ) : null}
              </div>
            ) : null}
          </section>
        </div>
      </div>
    </TransformometroShell>
  );
}
