import type { ComponentProps } from "react";
import {
  ActionButton,
  attachmentFileListBemClasses,
  createDashboardTopBar,
  createCompactPagination,
  createDashboardAttachmentFileList,
  createDashboardFileDropzone,
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
  PageHero,
  pageHeroBemClasses,
  sectionCardPacBemClasses,
  formActionsBemClasses,
  formGridBemClasses,
  type StateBoxVariant,
} from "@delpi/plugin-ui/index";
import { Activity, AlertTriangle, FileQuestion, Loader2 } from "lucide-react";

import { PpFormFieldShell } from "../components/data/ppFormFields";

const PREFIX = "pp";
const PP_PORTAL_SCOPE = "dashboard-production-pulse";

export const PpHostContainedDialog = createHostContainedModalShell({
  prefix: PREFIX,
  portalScopeClassName: PP_PORTAL_SCOPE,
  containedLayout: "dialog",
});

export function PpPageHero(props: ComponentProps<typeof PageHero>) {
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
    title: "Arraste o artefato aqui ou clique para anexar",
    hint: "Use o .bin compilado no Arduino IDE / PlatformIO (não o fonte .ino).",
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

export type PpFirmwareFileFieldProps = {
  id: string;
  label: string;
  hint?: string;
  accept?: string;
  disabled?: boolean;
  file: File | null;
  onChange: (file: File | null) => void;
};

/** Upload OTA via FileDropzone do kit — artefato compilado (.bin), não o fonte .ino. */
export function PpFirmwareFileField({
  id,
  label,
  hint,
  accept = ".bin,application/octet-stream",
  disabled,
  file,
  onChange,
}: PpFirmwareFileFieldProps) {
  const items = file
    ? [
        {
          id: "firmware-artifact",
          fileName: file.name,
          detail: `${Math.max(1, Math.round(file.size / 1024))} KB`,
        },
      ]
    : [];

  return (
    <PpFormFieldShell id={id} label={label} hint={hint} span>
      <div className="pp-firmware-file-field">
        <PpFileDropzone
          accept={accept}
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
            items={items}
            canRemove={!disabled}
            onRemove={() => onChange(null)}
          />
        ) : null}
      </div>
    </PpFormFieldShell>
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
