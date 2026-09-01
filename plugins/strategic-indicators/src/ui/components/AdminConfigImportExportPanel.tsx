import { useRef, useState } from "react";
import { SectionHintLabel, useConfirmDialogController } from "@delpi/plugin-ui/index";
import {
  applyAdminConfigBundle,
  downloadAdminConfigBundleJson,
  exportAdminConfigBundle,
  previewAdminConfigBundle,
} from "../../data/api/adminConfigBundleApi";
import type {
  AdminConfigBundle,
  AdminConfigImportMode,
  AdminConfigPlannedCounts,
  AdminConfigPreviewResponse,
} from "../../data/types/adminConfigBundle";
import { DataTable } from "./DataTable";
import { InfoState } from "./InfoState";
import { SiConfirmModal } from "./SiConfirmModal";
import { SiHelpActionButton } from "./SiHelpActionButton";
import { SiNativeCheckboxControl } from "./siNativeFormFields";
import { SI_HELP } from "../../content/helpTooltips";
import "./AdminConfigImportExportPanel.css";

type AdminConfigImportExportPanelProps = {
  getAccessToken?: () => string | undefined;
  onCompleted?: () => void;
};

type Feedback = { kind: "success" | "error"; text: string };

type PreviewRow = {
  key: string;
  entity: string;
  inFile: number;
  insert: number;
  update: number;
  skip: number;
  remove: number;
};

function plannedRow(
  key: string,
  entity: string,
  counts: AdminConfigPlannedCounts,
): PreviewRow {
  return {
    key,
    entity,
    inFile: counts.in_file,
    insert: counts.insert,
    update: counts.update,
    skip: counts.skip,
    remove: counts.delete,
  };
}

function isAdminConfigBundle(value: unknown): value is AdminConfigBundle {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.schema_version === "number" &&
    Array.isArray(record.departments) &&
    Array.isArray(record.department_indicators) &&
    Array.isArray(record.indicator_goals) &&
    typeof record.module_settings === "object" &&
    record.module_settings !== null
  );
}

export function AdminConfigImportExportPanel({
  getAccessToken,
  onCompleted,
}: AdminConfigImportExportPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const confirmDialog = useConfirmDialogController();
  const [busy, setBusy] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [parsedBundle, setParsedBundle] = useState<AdminConfigBundle | null>(null);
  const [mode, setMode] = useState<AdminConfigImportMode>("replace");
  const [includeGoals, setIncludeGoals] = useState(true);
  const [preview, setPreview] = useState<AdminConfigPreviewResponse | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  const canPreview = Boolean(parsedBundle) && !busy;
  const canApply = Boolean(preview?.valid) && !busy;

  function resetPreview() {
    setPreview(null);
  }

  function handleModeChange(next: AdminConfigImportMode) {
    setMode(next);
    resetPreview();
  }

  async function handleExport() {
    setBusy(true);
    setFeedback(null);
    try {
      const bundle = await exportAdminConfigBundle(getAccessToken);
      const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
      downloadAdminConfigBundleJson(
        bundle,
        `strategic-indicators-config-${stamp}.json`,
      );
      setFeedback({
        kind: "success",
        text: "Exportação concluída. O arquivo inclui departamentos, indicadores, metas ativas e parâmetros globais.",
      });
    } catch (exportError) {
      setFeedback({
        kind: "error",
        text:
          exportError instanceof Error
            ? exportError.message
            : "Falha ao exportar configuração.",
      });
    } finally {
      setBusy(false);
    }
  }

  async function handleChooseFile(file: File) {
    setFeedback(null);
    resetPreview();
    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as unknown;
      if (!isAdminConfigBundle(parsed)) {
        setParsedBundle(null);
        setFileName(null);
        setFeedback({
          kind: "error",
          text: "Arquivo JSON inválido: envelope de configuração não reconhecido.",
        });
        return;
      }
      setParsedBundle(parsed);
      setFileName(file.name);
    } catch {
      setParsedBundle(null);
      setFileName(null);
      setFeedback({
        kind: "error",
        text: "Arquivo JSON inválido: não foi possível ler o conteúdo.",
      });
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function handlePreview() {
    if (!parsedBundle) return;
    setBusy(true);
    setFeedback(null);
    try {
      const result = await previewAdminConfigBundle(
        parsedBundle,
        { mode, includeGoals },
        getAccessToken,
      );
      setPreview(result);
      if (!result.valid) {
        setFeedback({
          kind: "error",
          text: result.errors.join(" ") || "Pré-visualização inválida.",
        });
      }
    } catch (previewError) {
      setPreview(null);
      setFeedback({
        kind: "error",
        text:
          previewError instanceof Error
            ? previewError.message
            : "Falha ao pré-visualizar configuração.",
      });
    } finally {
      setBusy(false);
    }
  }

  async function runApply() {
    if (!parsedBundle) return;
    setBusy(true);
    setFeedback(null);
    try {
      const result = await applyAdminConfigBundle(
        parsedBundle,
        { mode, includeGoals },
        getAccessToken,
      );
      const stats = result.stats;
      const wipeNote =
        mode === "replace"
          ? " Scores materializados foram limpos; use Atualizar ou aguarde o job."
          : "";
      setFeedback({
        kind: "success",
        text: `${result.message} ${
          mode === "replace" ? "Substituir" : "Mesclar"
        }: ${stats.departments_upserted} departamentos, ${stats.indicators_upserted} indicadores, ${stats.goals_created} metas.${wipeNote}`,
      });
      resetPreview();
      onCompleted?.();
    } catch (applyError) {
      setFeedback({
        kind: "error",
        text:
          applyError instanceof Error
            ? applyError.message
            : "Falha ao importar configuração.",
      });
    } finally {
      setBusy(false);
    }
  }

  async function handleApply() {
    if (!canApply) return;
    if (mode === "replace") {
      const confirmed = await confirmDialog.confirm({
        title: "Substituir cadastro?",
        message:
          "Isso apaga TODOS os departamentos, indicadores e metas atuais e importa o arquivo. Auditoria e solicitações de mudança não entram no backup. O painel estratégico fica sem scores até o job horário ou Atualizar.",
        confirmLabel: "Substituir e aplicar",
        cancelLabel: "Cancelar",
        variant: "danger",
      });
      if (!confirmed) return;
    }
    await runApply();
  }

  const previewRows: PreviewRow[] = preview
    ? [
        plannedRow("departments", "Departamentos", preview.planned.departments),
        plannedRow(
          "indicators",
          "Indicadores",
          preview.planned.department_indicators,
        ),
        plannedRow("goals", "Metas ativas", preview.planned.indicator_goals),
        plannedRow(
          "settings",
          "Parâmetros globais",
          preview.planned.module_settings,
        ),
      ]
    : [];

  const previewColumns =
    mode === "replace"
      ? [
          { key: "entity", header: "Entidade", render: (row: PreviewRow) => row.entity },
          { key: "inFile", header: "Arquivo", render: (row: PreviewRow) => String(row.inFile) },
          { key: "insert", header: "Inserir", render: (row: PreviewRow) => String(row.insert) },
          { key: "remove", header: "Remover", render: (row: PreviewRow) => String(row.remove) },
        ]
      : [
          { key: "entity", header: "Entidade", render: (row: PreviewRow) => row.entity },
          { key: "inFile", header: "Arquivo", render: (row: PreviewRow) => String(row.inFile) },
          { key: "insert", header: "Inserir", render: (row: PreviewRow) => String(row.insert) },
          { key: "update", header: "Atualizar", render: (row: PreviewRow) => String(row.update) },
          { key: "skip", header: "Ignorar", render: (row: PreviewRow) => String(row.skip) },
        ];

  return (
    <section className="si-config-io-panel">
      <div className="si-config-io-panel__header">
        <SectionHintLabel
          label="Exportar e importar configuração"
          hint={SI_HELP.system.importExportTitle}
          className="si-config-io-panel__title"
        />
      </div>

      {feedback?.kind === "error" ? (
        <InfoState
          title="Operação não concluída"
          description={feedback.text}
          actionLabel="Fechar"
          onAction={() => setFeedback(null)}
        />
      ) : null}

      {feedback?.kind === "success" ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--success">
          {feedback.text}
        </div>
      ) : null}

      <div className="si-config-io-panel__actions">
        <SiHelpActionButton
          className="si-settings-editor__button"
          disabled={busy}
          helpHint={SI_HELP.system.exportJson}
          onClick={() => void handleExport()}
        >
          {busy ? "Processando..." : "Exportar JSON"}
        </SiHelpActionButton>
      </div>

      <div className="si-config-io-panel__import-block">
        <p className="si-config-io-panel__section-title">Importar</p>
        <p className="si-config-io-panel__file-name">
          Arquivo: {fileName ?? "nenhum selecionado"}
        </p>
        <label
          className="si-config-io-panel__import"
          title={SI_HELP.system.importFile}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            disabled={busy}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) void handleChooseFile(file);
            }}
          />
          <span className="si-settings-editor__button si-settings-editor__button--secondary">
            {fileName ? "Trocar arquivo JSON" : "Escolher arquivo JSON"}
          </span>
        </label>
      </div>

      <fieldset className="si-config-io-panel__modes" disabled={busy}>
        <legend>Modo de importação</legend>
        <label className="si-config-io-panel__mode">
          <input
            type="radio"
            name="si-config-import-mode"
            checked={mode === "replace"}
            onChange={() => handleModeChange("replace")}
          />
          <span>
            <strong>Substituir tudo</strong>
            <small>{SI_HELP.system.importModeReplace}</small>
          </span>
        </label>
        <label className="si-config-io-panel__mode">
          <input
            type="radio"
            name="si-config-import-mode"
            checked={mode === "merge"}
            onChange={() => handleModeChange("merge")}
          />
          <span>
            <strong>Mesclar por ID</strong>
            <small>{SI_HELP.system.importModeMerge}</small>
          </span>
        </label>
      </fieldset>

      {mode === "merge" ? (
        <SiNativeCheckboxControl
          className="si-config-io-panel__checkbox"
          checked={includeGoals}
          onChange={(next) => {
            setIncludeGoals(next);
            resetPreview();
          }}
          disabled={busy}
          label="Incluir metas analíticas (somente cria as que ainda não existem)"
          title={SI_HELP.system.importIncludeGoals}
        />
      ) : null}

      <div className="si-config-io-panel__actions">
        <SiHelpActionButton
          className="si-settings-editor__button si-settings-editor__button--secondary"
          disabled={!canPreview}
          helpHint={SI_HELP.system.importPreview}
          onClick={() => void handlePreview()}
        >
          {preview ? "Pré-visualizar de novo" : "Pré-visualizar"}
        </SiHelpActionButton>
        <SiHelpActionButton
          className="si-settings-editor__button"
          disabled={!canApply}
          helpHint={SI_HELP.system.importApply}
          onClick={() => void handleApply()}
        >
          Aplicar
        </SiHelpActionButton>
      </div>

      {preview?.valid ? (
        <div className="si-config-io-panel__preview">
          <p className="si-config-io-panel__section-title">
            Pré-visualização modo={mode} válido
          </p>
          <DataTable
            columns={previewColumns}
            rows={previewRows}
            getRowKey={(row) => row.key}
            emptyText="Sem diferenças planejadas."
          />
          {mode === "replace" ? (
            <p className="si-config-io-panel__warning">
              Substituir tudo apaga o cadastro atual (incluindo metas inativas
              que não vão no JSON) e os scores materializados. Tendências/Painel
              ficam incompletos até o refresh.
            </p>
          ) : null}
        </div>
      ) : null}

      <SiConfirmModal
        open={confirmDialog.pending !== null}
        title={confirmDialog.pending?.title}
        message={confirmDialog.pending?.message ?? ""}
        confirmLabel={confirmDialog.pending?.confirmLabel}
        cancelLabel={confirmDialog.pending?.cancelLabel}
        confirmBusy={busy}
        variant={confirmDialog.pending?.variant}
        onConfirm={confirmDialog.confirmPending}
        onCancel={confirmDialog.cancelPending}
      />
    </section>
  );
}
