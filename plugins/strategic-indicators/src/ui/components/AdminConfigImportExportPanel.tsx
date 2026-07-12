import { useRef, useState } from "react";
import { exportAdminConfigBundle, importAdminConfigBundle } from "../../data/api/adminConfigBundleApi";
import type { AdminConfigBundle } from "../../data/types/adminConfigBundle";
import { InfoState } from "./InfoState";
import { SiNativeCheckboxControl } from "./siNativeFormFields";
import "./AdminConfigImportExportPanel.css";

type AdminConfigImportExportPanelProps = {
  getAccessToken?: () => string | undefined;
  onCompleted?: () => void;
};

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function AdminConfigImportExportPanel({
  getAccessToken,
  onCompleted,
}: AdminConfigImportExportPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [includeGoals, setIncludeGoals] = useState(true);

  async function handleExport() {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const bundle = await exportAdminConfigBundle(getAccessToken);
      const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
      downloadJson(`strategic-indicators-config-${stamp}.json`, bundle);
      setSuccessMessage(
        "Exportação concluída. O arquivo inclui departamentos, indicadores, metas ativas e parâmetros globais.",
      );
    } catch (exportError) {
      setError(
        exportError instanceof Error
          ? exportError.message
          : "Falha ao exportar configuração.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleImportFile(file: File) {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as AdminConfigBundle;

      const result = await importAdminConfigBundle(
        { ...parsed, include_goals: includeGoals },
        getAccessToken,
      );

      const stats = result.stats;
      setSuccessMessage(
        `${result.message} Departamentos: ${stats.departments_upserted}, indicadores: ${stats.indicators_upserted}, metas criadas: ${stats.goals_created}, metas ignoradas: ${stats.goals_skipped}.`,
      );
      onCompleted?.();
    } catch (importError) {
      setError(
        importError instanceof Error
          ? importError.message
          : "Falha ao importar configuração.",
      );
    } finally {
      setLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  return (
    <section className="si-config-io-panel">
      <div className="si-config-io-panel__header">
        <div>
          <h3>Exportar e importar configuração</h3>
          <p>
            Backup completo do catálogo administrativo: departamentos, indicadores
            estruturais, metas ativas e parâmetros globais (JSON versionado).
          </p>
        </div>
      </div>

      {error ? (
        <InfoState
          title="Operação não concluída"
          description={error}
          actionLabel="Fechar"
          onAction={() => setError(null)}
        />
      ) : null}

      {successMessage ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--success">
          {successMessage}
        </div>
      ) : null}

      <div className="si-config-io-panel__actions">
        <button
          type="button"
          className="si-settings-editor__button"
          disabled={loading}
          onClick={() => void handleExport()}
        >
          {loading ? "Processando..." : "Exportar JSON"}
        </button>

        <label className="si-config-io-panel__import">
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            disabled={loading}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void handleImportFile(file);
            }}
          />
          <span className="si-settings-editor__button si-settings-editor__button--secondary">
            Importar JSON
          </span>
        </label>
      </div>

      <SiNativeCheckboxControl
        className="si-config-io-panel__checkbox"
        checked={includeGoals}
        onChange={setIncludeGoals}
        disabled={loading}
        label="Incluir metas analíticas na importação (somente cria metas ativas que ainda não existem)"
      />
    </section>
  );
}
