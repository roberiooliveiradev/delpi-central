import { useState, type ComponentProps, type ReactNode } from "react";
import {
  ActionButton,
  AnchoredPanelPortal,
  attachmentFileListBemClasses,
  ConfirmModalPanel,
  confirmModalBemClasses,
  ContextMenuDivider,
  ContextMenuItem,
  createDashboardTopBar,
  createCompactPagination,
  createDashboardAttachmentFileList,
  createDashboardFileDropzone,
  createFloatingNoticeStack,
  createHostContainedDrawerShell,
  createHostContainedModalShell,
  catalogSearchBarBemClasses,
  createDashboardCatalogSearchBar,
  createDashboardDataRecordCard,
  createDashboardFormActions,
  createDashboardFormGrid,
  createDashboardPagePath,
  createDashboardProgressTracker,
  createDashboardSectionCard,
  createDashboardSegmentToggle,
  createDashboardUnderlineNav,
  createDashboardJourneyProgressBar,
  createSimpleKpiCard,
  createStateBoxPanel,
  FieldLabel,
  fileDropzoneBemClasses,
  HintAction,
  IconButton,
  HelpTooltip,
  PageHero,
  pageHeroBemClasses,
  sectionCardPacBemClasses,
  formActionsBemClasses,
  formGridBemClasses,
  useFloatingNotices,
  type StateBoxVariant,
} from "@delpi/plugin-ui/index";
import { Activity, AlertTriangle, FileQuestion, Loader2 } from "lucide-react";

import { PpFormFieldShell, PpNativeTextAreaField } from "../components/data/ppFormFields";

const PREFIX = "pp";
const PP_PORTAL_SCOPE = "dashboard-production-pulse";

export const PpHostContainedDialog = createHostContainedModalShell({
  prefix: PREFIX,
  portalScopeClassName: PP_PORTAL_SCOPE,
  containedLayout: "dialog",
});

/** Detail firmware / IoT / job — wide host-contained dialog. */
export const PpDetailDialog = createHostContainedModalShell({
  prefix: PREFIX,
  portalScopeClassName: PP_PORTAL_SCOPE,
  containedLayout: "dialog",
  variant: "wide",
});

/** CRUD workbench (create/edit IoT, FW) — page host-contained dialog. */
export const PpWorkbenchDialog = createHostContainedModalShell({
  prefix: PREFIX,
  portalScopeClassName: PP_PORTAL_SCOPE,
  containedLayout: "dialog",
  variant: "page",
});

export const PpHostContainedDrawer = createHostContainedDrawerShell({
  prefix: PREFIX,
  portalScopeClassName: PP_PORTAL_SCOPE,
});

const ppConfirmClasses = confirmModalBemClasses(PREFIX, {
  actionsBlock: "form-actions",
  actionsAlign: "end",
});

export type PpConfirmDialogProps = {
  open: boolean;
  title?: string;
  message: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmBusy?: boolean;
  variant?: "default" | "danger";
  onConfirm: () => void;
  onCancel: () => void;
};

export function PpConfirmDialog({
  open,
  title = "Confirmar",
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmBusy = false,
  variant = "default",
  onConfirm,
  onCancel,
}: PpConfirmDialogProps) {
  return (
    <PpHostContainedDialog open={open} title={title} onClose={onCancel}>
      <ConfirmModalPanel
        message={message}
        confirmLabel={confirmLabel}
        cancelLabel={cancelLabel}
        confirmBusy={confirmBusy}
        variant={variant}
        onConfirm={onConfirm}
        onCancel={onCancel}
        classNames={ppConfirmClasses}
      />
    </PpHostContainedDialog>
  );
}

export const PpFloatingNotices = createFloatingNoticeStack({
  prefix: PREFIX,
  portalScopeClassName: PP_PORTAL_SCOPE,
});

export { useFloatingNotices };
export const PpIconButton = IconButton;
export { HelpTooltip };

export { AnchoredPanelPortal, ContextMenuDivider, ContextMenuItem };

export type PpPageHeroProps = Omit<
  ComponentProps<typeof PageHero>,
  "classNames" | "density"
>;

export function PpPageHero(props: PpPageHeroProps) {
  return <PageHero {...props} classNames={pageHeroBemClasses(PREFIX)} density="compact" />;
}

export const PpStateBox = createStateBoxPanel({
  prefix: PREFIX,
  renderIcon: (variant: StateBoxVariant) => {
    if (variant === "error") return <AlertTriangle size={22} />;
    if (variant === "empty") return <FileQuestion size={22} />;
    return <Loader2 size={22} />;
  },
});

export const PpActionButton = ActionButton;
export const PpHintAction = HintAction;
export const PpPagePath = createDashboardPagePath({
  prefix: PREFIX,
  portalScopeClassName: PP_PORTAL_SCOPE,
});
export const PpTopBar = createDashboardTopBar({ prefix: PREFIX });
export const PpFieldLabel = FieldLabel;
export const PpSimpleKpiCard = createSimpleKpiCard(PREFIX, { withBody: true, withSubtitle: true });
export const PpSegmentToggle = createDashboardSegmentToggle(PREFIX);
export const PpCatalogSearchBar = createDashboardCatalogSearchBar({
  classNames: catalogSearchBarBemClasses(PREFIX),
});
export const PpSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PREFIX),
  labels: { titleHelpAriaLabel: (title: string) => `Ajuda: ${title}` },
});
export const PpFormGrid = createDashboardFormGrid({ classNames: formGridBemClasses(PREFIX) });
export const PpFormActions = createDashboardFormActions({ classNames: formActionsBemClasses(PREFIX) });
export const PpUnderlineNav = createDashboardUnderlineNav({ prefix: PREFIX });
export const PpProgressTracker = createDashboardProgressTracker({ prefix: PREFIX });
export const PpOtaProgressBar = createDashboardJourneyProgressBar({ prefix: PREFIX });
export const PpPagination = createCompactPagination({
  prefix: PREFIX,
  layout: "flat",
  labels: {
    info: ({ page, totalPages, total }) =>
      `Página ${page} de ${totalPages} · ${total.toLocaleString("pt-BR")} registro(s)`,
    previous: "Anterior",
    next: "Próxima",
    navigationAriaLabel: "Paginação",
  },
});

export const PpDataRecordCard = createDashboardDataRecordCard({ prefix: PREFIX });

export const PpFileDropzone = createDashboardFileDropzone({
  classNames: fileDropzoneBemClasses(PREFIX, "file-dropzone"),
  labels: {
    title: "Arraste o arquivo aqui ou clique para anexar",
    hint: "Cada campo indica o formato aceito.",
  },
});

export const PpAttachmentFileList = createDashboardAttachmentFileList({
  classNames: attachmentFileListBemClasses(PREFIX),
  labels: {
    open: "Abrir",
    download: "Baixar",
    remove: "Remover",
    empty: "Nenhum arquivo anexado.",
  },
});

const FIRMWARE_ARTIFACT_ACCEPT = ".bin,application/octet-stream";
const FIRMWARE_SOURCE_ACCEPT = ".ino,.txt,text/plain";

function formatAttachmentSize(bytes: number): string {
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export type PpFirmwareArtifactFieldProps = {
  id: string;
  label: string;
  hint?: string;
  disabled?: boolean;
  file: File | null;
  onChange: (file: File | null) => void;
};

/** Artefato OTA (.bin) via FileDropzone do kit — o fonte .ino nunca é flashável. */
export function PpFirmwareArtifactField({
  id,
  label,
  hint,
  disabled,
  file,
  onChange,
}: PpFirmwareArtifactFieldProps) {
  return (
    <PpFormFieldShell id={id} label={label} hint={hint} span>
      <div className="pp-firmware-file-field">
        <PpFileDropzone
          accept={FIRMWARE_ARTIFACT_ACCEPT}
          multiple={false}
          disabled={disabled}
          hideInput
          ariaLabel={label}
          onFilesSelected={(files) => onChange(files[0] ?? null)}
          labels={{
            title: file ? "Substituir artefato (.bin)" : "Arraste o .bin ou clique para anexar",
            hint: "Compile o sketch (.ino) e anexe o binário gerado — o .ino não é flashável via OTA.",
          }}
        />
        {file ? (
          <PpAttachmentFileList
            items={[
              {
                id: "firmware-artifact",
                fileName: file.name,
                detail: formatAttachmentSize(file.size),
              },
            ]}
            canRemove={!disabled}
            onRemove={() => onChange(null)}
          />
        ) : null}
      </div>
    </PpFormFieldShell>
  );
}

export type PpFirmwareSourceFieldProps = {
  id: string;
  label: string;
  hint?: string;
  editorLabel: string;
  editorHint?: string;
  disabled?: boolean;
  rows?: number;
  /** Snapshot do sketch — dropzone e editor compartilham este estado. */
  value: string;
  onChange: (sourceText: string) => void;
  onReadError?: () => void;
};

/** Sketch (.ino): importar arquivo e editar texto alimentam o mesmo snapshot. */
export function PpFirmwareSourceField({
  id,
  label,
  hint,
  editorLabel,
  editorHint,
  disabled,
  rows = 12,
  value,
  onChange,
  onReadError,
}: PpFirmwareSourceFieldProps) {
  const [imported, setImported] = useState<{ name: string; size: number } | null>(null);

  const importSource = async (file: File | null) => {
    if (!file) return;
    try {
      const text = await file.text();
      setImported({ name: file.name, size: file.size });
      onChange(text);
    } catch {
      setImported(null);
      onReadError?.();
    }
  };

  const clearSource = () => {
    setImported(null);
    onChange("");
  };

  return (
    <>
      <PpFormFieldShell id={id} label={label} hint={hint} span>
        <div className="pp-firmware-file-field">
          <PpFileDropzone
            accept={FIRMWARE_SOURCE_ACCEPT}
            multiple={false}
            disabled={disabled}
            hideInput
            ariaLabel={label}
            onFilesSelected={(files) => void importSource(files[0] ?? null)}
            labels={{
              title: imported
                ? "Substituir sketch (.ino)"
                : "Arraste o .ino ou clique para importar",
              hint: "O texto importado entra no snapshot da versão e continua editável abaixo.",
            }}
          />
          {imported ? (
            <PpAttachmentFileList
              items={[
                {
                  id: "firmware-source",
                  fileName: imported.name,
                  detail: formatAttachmentSize(imported.size),
                },
              ]}
              canRemove={!disabled}
              onRemove={clearSource}
            />
          ) : null}
        </div>
      </PpFormFieldShell>
      <PpNativeTextAreaField
        id={`${id}-editor`}
        label={editorLabel}
        hint={editorHint}
        value={value}
        onChange={onChange}
        rows={rows}
        span
      />
    </>
  );
}

export const ppShellIcon = <Activity size={28} strokeWidth={1.75} />;

export {
  PpChartCard,
  PpReadingsAreaChart,
  buildPpReadingsChartSeries,
  formatPpReadingsChartValue,
  readingsToComparativeData,
  readingsToSeriesPoints,
  type PpReadingsChartVariant,
} from "../components/data/ppCharts";
export { PpDataTable, type DataTableColumn } from "../components/data/dataTableUi";
export {
  PpFilterInputField,
  PpFilterSelectField,
  PpFiltersRow,
  PpFilterToolbarRowClasses,
} from "../components/data/filtersUi";
export {
  PpFormFieldShell,
  PpNativeInlineTextField,
  PpNativeSelectField,
  PpNativeSwitchField,
  PpNativeTextAreaField,
  PpNativeTextField,
  ppFieldError,
  ppFieldHint,
} from "../components/data/ppFormFields";
