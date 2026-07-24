import { useCallback, useRef, useState } from "react";
import { AlertTriangle, Archive, ArrowDownUp, Download, FileJson, RefreshCw, Upload } from "lucide-react";

import type { AppProps } from "../../App";
import { HelpTooltip } from "@delpi/plugin-ui/index";
import { DS_TABLE_CLASS_NAMES } from "../../components/dataTableUi";
import { TableHeader } from "../../components/TableHeader";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { useFloatingNotice } from "../../components/ui/FloatingNoticeProvider";
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
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { StateBox } from "../../components/StateBox";

const tableCn = DS_TABLE_CLASS_NAMES;
const FEEDBACK_NOTICE_ID = "tm-data-transfer-feedback";

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
  const notice = useFloatingNotice();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [mode, setMode] = useState<JsonImportMode>("merge");
  const [importSource, setImportSource] = useState<ImportSource>("package");
  const [bundle, setBundle] = useState<JsonBackupBundle | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [preview, setPreview] = useState<JsonImportPreview | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const notifySuccess = useCallback(
    (title: string, message: string) => {
      notice({
        id: FEEDBACK_NOTICE_ID,
        variant: "success",
        title,
        message,
      });
    },
    [notice],
  );

  const notifyError = useCallback(
    (message: string) => {
      notice({
        id: FEEDBACK_NOTICE_ID,
        variant: "error",
        title: "Não foi possível concluir",
        message,
      });
    },
    [notice],
  );

  const onExportPackage = useCallback(async () => {
    setBusy("export-package");
    try {
      await downloadPackageExport(getAccessToken);
      notifySuccess(
        "Exportação concluída",
        "Pacote .tmbackup.zip baixado (cadastro + arquivos do processo + evidências).",
      );
    } catch (err) {
      notifyError(err instanceof Error ? err.message : "Erro ao exportar pacote.");
    } finally {
      setBusy(null);
    }
  }, [getAccessToken, notifyError, notifySuccess]);

  const onExportJson = useCallback(async () => {
    setBusy("export-json");
    try {
      await downloadJsonExport(getAccessToken);
      notifySuccess(
        "Exportação concluída",
        "Arquivo JSON baixado (sem binários de anexos).",
      );
    } catch (err) {
      notifyError(err instanceof Error ? err.message : "Erro ao exportar JSON.");
    } finally {
      setBusy(null);
    }
  }, [getAccessToken, notifyError, notifySuccess]);

  const onFileChange = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
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
        notifyError(
          "Arquivo inválido — envie um JSON ou pacote .tmbackup.zip exportado pelo Transformômetro.",
        );
      }
    },
    [notifyError],
  );

  const onPreview = useCallback(async () => {
    if (importSource === "package" && !importFile) {
      notifyError("Selecione um pacote .zip antes de pré-visualizar.");
      return;
    }
    if (importSource === "json" && !bundle) {
      notifyError("Selecione um arquivo JSON antes de pré-visualizar.");
      return;
    }
    setBusy("preview");
    try {
      const result =
        importSource === "package" && importFile
          ? await previewPackageImport(importFile, mode, "auto", getAccessToken)
          : await previewJsonImport(bundle!, mode, "auto", getAccessToken);
      setPreview(result);
      if (!result.valid) {
        notifyError((result.errors ?? []).join(" ") || "Pacote inválido.");
      }
    } catch (err) {
      notifyError(err instanceof Error ? err.message : "Erro na pré-visualização.");
    } finally {
      setBusy(null);
    }
  }, [importSource, importFile, bundle, mode, getAccessToken, notifyError]);

  const onApply = useCallback(async () => {
    if (importSource === "package" && !importFile) {
      notifyError("Selecione um pacote .zip antes de importar.");
      return;
    }
    if (importSource === "json" && !bundle) {
      notifyError("Selecione um arquivo JSON antes de importar.");
      return;
    }
    if (mode === "replace") {
      const ok = await confirm({
        title: "Substituir dados",
        message:
          "Substituir todos os dados apagará departamentos, processos, revisões, medições, investimentos, recursos, arquivos do processo e evidências atuais. Deseja continuar?",
        confirmLabel: "Substituir",
        variant: "danger",
      });
      if (!ok) return;
    }
    setBusy("apply");
    try {
      const result =
        importSource === "package" && importFile
          ? await applyPackageImport(importFile, mode, "auto", getAccessToken)
          : await applyJsonImport(bundle!, mode, "auto", getAccessToken);
      setPreview(result as JsonImportPreview);
      const rows = result.recalc?.rows_upserted ?? 0;
      const restoredParts: string[] = [];
      if (result.evidence_files_restored != null) {
        restoredParts.push(
          `${result.evidence_files_restored} evidência(s) de revisão`,
        );
      }
      if (result.processo_arquivo_files_restored != null) {
        restoredParts.push(
          `${result.processo_arquivo_files_restored} arquivo(s) do processo`,
        );
      }
      const restored =
        restoredParts.length > 0
          ? ` ${restoredParts.join(" e ")} restaurado(s).`
          : "";
      notifySuccess(
        "Importação concluída",
        `${mode === "replace" ? "Substituição total" : "Mesclagem por ID"}. Dashboard recalculado (${rows} linhas derivadas).${restored}`,
      );
    } catch (err) {
      notifyError(err instanceof Error ? err.message : "Erro na importação.");
    } finally {
      setBusy(null);
    }
  }, [importSource, importFile, bundle, mode, getAccessToken, confirm, notifyError, notifySuccess]);

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
        subtitle="Backup completo em pacote (.tmbackup.zip) com cadastro, diagramas, mapeamento, arquivos do processo e evidências."
        currentPath={pathname}
        onNavigate={onNavigate}
      />

      <div className="tm-data-transfer">
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
                  O pacote <code>.tmbackup.zip</code> inclui cadastro, diagramas, mapeamento WBS,
                  arquivos do processo e evidências de revisão. Use JSON apenas para transferência
                  leve sem anexos.
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
                className={DS_GHOST_BTN}
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
                  className={DS_GHOST_BTN}
                  onClick={() => fileInputRef.current?.click()}
                >
                  Escolher arquivo
                </button>
              </div>
            </div>

            <div className="tm-data-transfer__toolbar">
              <button
                type="button"
                className={DS_GHOST_BTN}
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
              <StateBox variant="error" className="tm-data-transfer__incompatible" dismissible={false}>
                <p>
                  <AlertTriangle size={16} aria-hidden style={{ verticalAlign: "text-bottom", marginRight: 6 }} />
                  {(preview.errors ?? []).join(" ") ||
                    "Formato do arquivo não reconhecido. Envie um backup exportado pelo Transformômetro."}
                </p>
              </StateBox>
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
                      ? ` · ${preview.evidence_files.in_package} evidência(s) de revisão`
                      : ""}
                    {preview.processo_arquivo_files
                      ? ` · ${preview.processo_arquivo_files.in_package} arquivo(s) do processo`
                      : ""}
                  </p>
                ) : null}
                {preview.resolved_format ? (
                  <p className="tm-data-transfer__format-summary">
                    Formato detectado: {RESOLVED_FORMAT_LABELS[preview.resolved_format]}
                    {preview.legacy_transformed ? " (filiais e instâncias sintéticas geradas)" : ""}
                  </p>
                ) : null}
                <div className={tableCn.wrap}>
                  <table className={tableCn.table}>
                    <thead>
                      <tr>
                        <th className={tableCn.colWide}>
                          <TableHeader label="Entidade" hint={TM_HELP_TOOLTIPS.dataTransfer.previewEntidade} />
                        </th>
                        <th className={tableCn.colNumeric}>
                          <TableHeader label="No arquivo" hint={TM_HELP_TOOLTIPS.dataTransfer.previewNoArquivo} />
                        </th>
                        <th className={tableCn.colNumeric}>
                          <TableHeader label="Inserir" hint={TM_HELP_TOOLTIPS.dataTransfer.previewInserir} />
                        </th>
                        <th className={tableCn.colNumeric}>
                          <TableHeader label="Atualizar" hint={TM_HELP_TOOLTIPS.dataTransfer.previewAtualizar} />
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(preview.entities).map(([key, stats]) => (
                        <tr key={key}>
                          <td className={tableCn.colWide}>{ENTITY_LABELS[key] ?? key}</td>
                          <td className={tableCn.colNumeric}>{stats.total}</td>
                          <td className={tableCn.colNumeric}>{stats.insert}</td>
                          <td className={tableCn.colNumeric}>{stats.update}</td>
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
