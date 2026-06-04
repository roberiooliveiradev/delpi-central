import { useCallback, useRef, useState } from "react";
import { Download, FileUp, RefreshCw } from "lucide-react";

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

  return (
    <TransformometroShell>
      <PageHeader
        title="Exportar / Importar JSON"
        subtitle="Backup completo do cadastro (processos, revisões, medições, investimentos e recursos)."
        currentPath={pathname}
        onNavigate={onNavigate}
        actions={
          <button
            type="button"
            className="ds-primary-btn"
            disabled={busy !== null}
            onClick={() => void onExport()}
          >
            <Download size={16} aria-hidden />
            {busy === "export" ? "Exportando…" : "Exportar JSON"}
          </button>
        }
      />

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

      <section className="ds-card ds-stack" style={{ gap: "1.25rem", marginTop: "1rem" }}>
        <div>
          <h2 className="ds-section-title">Importar</h2>
          <p className="ds-page-subtitle" style={{ marginTop: "0.35rem" }}>
            Envie um arquivo exportado neste app. Escolha se deseja substituir todo o cadastro ou
            mesclar registros pelo ID (atualiza existentes e inclui novos, sem apagar o que não
            estiver no arquivo).
          </p>
        </div>

        <fieldset className="ds-stack" style={{ gap: "0.5rem", border: "none", padding: 0 }}>
          <legend className="ds-label">Modo de importação</legend>
          <label className="ds-inline-check">
            <input
              type="radio"
              name="import-mode"
              checked={mode === "merge"}
              onChange={() => {
                setMode("merge");
                setPreview(null);
              }}
            />
            Mesclar por ID — atualizar/inserir conforme o JSON, manter o restante
          </label>
          <label className="ds-inline-check">
            <input
              type="radio"
              name="import-mode"
              checked={mode === "replace"}
              onChange={() => {
                setMode("replace");
                setPreview(null);
              }}
            />
            Substituir tudo — apaga o cadastro atual e importa somente o JSON
          </label>
        </fieldset>

        <div className="ds-inline-actions" style={{ flexWrap: "wrap", gap: "0.75rem" }}>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            className="ds-visually-hidden"
            onChange={(e) => void onFileChange(e)}
          />
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={() => fileInputRef.current?.click()}
          >
            <FileUp size={16} aria-hidden />
            Escolher arquivo
          </button>
          {fileName ? <span className="ds-hint">{fileName}</span> : null}
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
            {preview.current_counts ? (
              <p className="ds-muted" style={{ marginTop: "0.75rem" }}>
                Cadastro atual no banco:{" "}
                {Object.entries(preview.current_counts)
                  .map(([k, n]) => `${ENTITY_LABELS[k] ?? k}: ${n}`)
                  .join(" · ")}
              </p>
            ) : null}
          </div>
        ) : null}
      </section>
    </TransformometroShell>
  );
}
