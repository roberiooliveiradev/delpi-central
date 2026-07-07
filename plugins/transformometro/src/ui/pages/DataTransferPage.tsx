import { useCallback, useRef, useState } from "react";
import { AlertTriangle, Archive, ArrowDownUp, Download, FileJson, RefreshCw, Upload } from "lucide-react";

import type { AppProps } from "../../App";
import { HelpTooltip } from "@delpi/plugin-ui";
import { TableHeader } from "../../components/TableHeader";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  applyJsonImport,
  applyPackageImport,
  downloadJsonExport,
  downloadPackageExport,
  previewJsonImport,
  previewPackageImport,
  type JsonBackupBundle,
  type JsonImportMode,
  type JsonImportPreview,
} from "../../data/api/transformometroApi";
import "./DataTransferPage.css";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

type ImportSource = "json" | "package";

const ENTITY_LABELS: Record<string, string> = {
  filiais: "Unidades",
  setores: "Departamentos",
  setor_filiais: "Departamento × unidade",
  processos: "Processos",
  processo_instancias: "Instâncias de processo",
  processo_instancia_setores: "Instância × departamento",
  processo_diagramas: "Diagramas de processo",
  instancia_diagrama_escopos: "Escopos de diagrama",
  revisao_diagrama_overlays: "Overlays de diagrama",
  processo_decomposicao: "Mapeamento (WBS)",
  instancia_decomposicao_escopos: "Escopos de mapeamento",
  revisao_decomposicao_overlays: "Overlays de mapeamento",
  revisoes: "Revisões",
  medicoes: "Medições",
  investimentos: "Investimentos",
  recursos_compartilhados: "Recursos compartilhados",
  recurso_custos: "Custos de recurso",
  revisao_recursos_compartilhados: "Vínculos revisão ↔ recurso",
  revisao_evidencias: "Evidências de revisão",
};

const RESOLVED_FORMAT_LABELS: Record<"legacy" | "modern", string> = {
  legacy: "backup legado (1.1)",
  modern: "Playbook 18+",
};

export function DataTransferPage({ getAccessToken, pathname, onNavigate }: Props) {
  const confirm = useConfirm();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [mode, setMode] = useState<JsonImportMode>("merge");
  const [importSource, setImportSource] = useState<ImportSource>("package");
  const [bundle, setBundle] = useState<JsonBackupBundle | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [preview, setPreview] = useState<JsonImportPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const onExportPackage = useCallback(async () => {
    clearMessages();
    setBusy("export-package");
    try {
      await downloadPackageExport(getAccessToken);
      setSuccess("Exportação concluída — pacote .tmbackup.zip baixado (cadastro + evidências).");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar pacote.");
    } finally {
      setBusy(null);
    }
  }, [getAccessToken]);

  const onExportJson = useCallback(async () => {
    clearMessages();
    setBusy("export-json");
    try {
      await downloadJsonExport(getAccessToken);
      setSuccess("Exportação concluída — arquivo JSON baixado (sem binários de evidência).");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar JSON.");
    } finally {
      setBusy(null);
    }
  }, [getAccessToken]);

  const onFileChange = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    clearMessages();
    setPreview(null);
    setBundle(null);
    setImportFile(null);
    const file = event.target.files?.[0];
    if (!file) return;
    setFileName(file.name);

    const lower = file.name.toLowerCase();
    if (lower.endsWith(".zip") || lower.endsWith(".tmbackup.zip")) {
      setImportSource("package");
      setImportFile(file);
      return;
    }

    setImportSource("json");
    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as JsonBackupBundle;
      setBundle(parsed);
    } catch {
      setError("Arquivo inválido — envie um JSON ou pacote .tmbackup.zip exportado pelo Transformômetro.");
    }
  }, []);

  const onPreview = useCallback(async () => {
    if (importSource === "package" && !importFile) {
      setError("Selecione um pacote .zip antes de pré-visualizar.");
      return;
    }
    if (importSource === "json" && !bundle) {
      setError("Selecione um arquivo JSON antes de pré-visualizar.");
      return;
    }
    clearMessages();
    setBusy("preview");
    try {
      const result =
        importSource === "package" && importFile
          ? await previewPackageImport(importFile, mode, "auto", getAccessToken)
          : await previewJsonImport(bundle!, mode, "auto", getAccessToken);
      setPreview(result);
      if (!result.valid) {
        setError((result.errors ?? []).join(" ") || "Pacote inválido.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na pré-visualização.");
    } finally {
      setBusy(null);
    }
  }, [importSource, importFile, bundle, mode, getAccessToken]);

  const onApply = useCallback(async () => {
    if (importSource === "package" && !importFile) {
      setError("Selecione um pacote .zip antes de importar.");
      return;
    }
    if (importSource === "json" && !bundle) {
      setError("Selecione um arquivo JSON antes de importar.");
      return;
    }
    if (mode === "replace") {
      const ok = await confirm({
        title: "Substituir dados",
        message:
          "Substituir todos os dados apagará departamentos, processos, revisões, medições, investimentos, recursos e evidências atuais. Deseja continuar?",
        confirmLabel: "Substituir",
        variant: "danger",
      });
      if (!ok) return;
    }
    clearMessages();
    setBusy("apply");
    try {
      const result =
        importSource === "package" && importFile
          ? await applyPackageImport(importFile, mode, "auto", getAccessToken)
          : await applyJsonImport(bundle!, mode, "auto", getAccessToken);
      setPreview(result as JsonImportPreview);
      const rows = result.recalc?.rows_upserted ?? 0;
      const evidence =
        result.evidence_files_restored != null
          ? ` ${result.evidence_files_restored} arquivo(s) de evidência restaurado(s).`
          : "";
      setSuccess(
        `Importação concluída (${mode === "replace" ? "substituição total" : "mesclagem por ID"}). Dashboard recalculado (${rows} linhas derivadas).${evidence}`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro na importação.");
    } finally {
      setBusy(null);
    }
  }, [importSource, importFile, bundle, mode, getAccessToken]);

  const selectMode = (next: JsonImportMode) => {
    setMode(next);
    setPreview(null);
  };

  const hasImportFile =
    (importSource === "package" && importFile !== null) ||
    (importSource === "json" && bundle !== null);

  return (
    <TransformometroShell>
      <PageHeader
        title="Exportar / Importar"
        subtitle="Backup completo em pacote (.tmbackup.zip) com cadastro, diagramas, mapeamento e evidências."
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
                <h2 className="ds-section-title">
                  Exportar
                  <HelpTooltip
                    content={TM_HELP_TOOLTIPS.dataTransfer.export}
                    ariaLabel="Ajuda: Exportar"
                  />
                </h2>
                <p className="ds-hint">
                  O pacote <code>.tmbackup.zip</code> inclui cadastro, diagramas, mapeamento WBS e
                  arquivos de evidência. Use JSON apenas para transferência leve sem anexos.
                </p>
              </div>
            </div>
            <div className="tm-data-transfer__toolbar">
              <button
                type="button"
                className="ds-primary-btn"
                disabled={busy !== null}
                onClick={() => void onExportPackage()}
              >
                <Archive size={16} aria-hidden />
                {busy === "export-package" ? "Exportando…" : "Baixar pacote completo"}
              </button>
              <button
                type="button"
                className="ds-ghost-btn"
                disabled={busy !== null}
                onClick={() => void onExportJson()}
              >
                <FileJson size={16} aria-hidden />
                {busy === "export-json" ? "Exportando…" : "Só JSON"}
              </button>
            </div>
          </section>

          <section className="ds-card tm-data-transfer__panel tm-data-transfer__panel--import">
            <div className="tm-data-transfer__panel-head">
              <span className="tm-data-transfer__panel-icon" aria-hidden>
                <Upload size={22} strokeWidth={1.75} />
              </span>
              <div className="tm-data-transfer__panel-text">
                <h2 className="ds-section-title">Importar</h2>
                <p className="ds-hint">
                  Envie um pacote <code>.tmbackup.zip</code> (recomendado) ou JSON exportado neste
                  app. Pré-visualize o impacto antes de aplicar.
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
                    Apaga o cadastro atual e importa somente o conteúdo do pacote.
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
                accept="application/json,.json,application/zip,.zip,.tmbackup.zip"
                hidden
                onChange={(e) => void onFileChange(e)}
              />
              <div className="tm-data-transfer__file-row">
                {importSource === "package" ? (
                  <Archive size={20} aria-hidden style={{ color: "var(--ds-accent)", flexShrink: 0 }} />
                ) : (
                  <FileJson size={20} aria-hidden style={{ color: "var(--ds-accent)", flexShrink: 0 }} />
                )}
                <span
                  className={`tm-data-transfer__file-name${
                    fileName ? " tm-data-transfer__file-name--selected" : ""
                  }`}
                  title={fileName ?? undefined}
                >
                  {fileName ?? "Nenhum arquivo selecionado"}
                  {fileName ? (
                    <span className="ds-hint" style={{ display: "block", marginTop: 4 }}>
                      Formato: {importSource === "package" ? "pacote completo" : "JSON"}
                    </span>
                  ) : null}
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
                disabled={!hasImportFile || busy !== null}
                onClick={() => void onPreview()}
              >
                <RefreshCw size={16} aria-hidden />
                {busy === "preview" ? "Analisando…" : "Pré-visualizar"}
              </button>
              <button
                type="button"
                className="ds-primary-btn"
                disabled={!hasImportFile || busy !== null}
                onClick={() => void onApply()}
              >
                {busy === "apply" ? "Importando…" : "Aplicar importação"}
              </button>
            </div>

            {preview && preview.format_compatible === false ? (
              <div className="ds-state ds-state--error tm-data-transfer__incompatible" role="alert">
                <p>
                  <AlertTriangle size={16} aria-hidden style={{ verticalAlign: "text-bottom", marginRight: 6 }} />
                  {(preview.errors ?? []).join(" ") ||
                    "Formato do arquivo não reconhecido. Envie um backup exportado pelo Transformômetro."}
                </p>
              </div>
            ) : null}

            {preview?.valid && preview.entities ? (
              <div className="tm-data-transfer__preview">
                <h3 className="ds-section-title tm-data-transfer__preview-title">
                  Resumo da pré-visualização
                </h3>
                {preview.package_format ? (
                  <p className="tm-data-transfer__format-summary">
                    Pacote {preview.package_version ?? ""} · schema {preview.manifest_schema_version ?? "—"}
                    {preview.evidence_files
                      ? ` · ${preview.evidence_files.in_package} arquivo(s) de evidência`
                      : ""}
                  </p>
                ) : null}
                {preview.resolved_format ? (
                  <p className="tm-data-transfer__format-summary">
                    Formato detectado: {RESOLVED_FORMAT_LABELS[preview.resolved_format]}
                    {preview.legacy_transformed ? " (filiais e instâncias sintéticas geradas)" : ""}
                  </p>
                ) : null}
                <div className="ds-table-wrap">
                  <table className="ds-table">
                    <thead>
                      <tr>
                        <th><TableHeader label="Entidade" hint={TM_HELP_TOOLTIPS.dataTransfer.previewEntidade} /></th>
                        <th><TableHeader label="No arquivo" hint={TM_HELP_TOOLTIPS.dataTransfer.previewNoArquivo} /></th>
                        <th><TableHeader label="Inserir" hint={TM_HELP_TOOLTIPS.dataTransfer.previewInserir} /></th>
                        <th><TableHeader label="Atualizar" hint={TM_HELP_TOOLTIPS.dataTransfer.previewAtualizar} /></th>
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
