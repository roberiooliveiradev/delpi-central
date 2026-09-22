import { type ComponentProps, type ReactNode } from "react";
import {
  attachmentPreviewStripBemClasses,
  createDashboardAttachmentPreviewStrip,
  createDashboardDataCardsGrid,
  createDashboardDataRecordCard,
  createDashboardEmptyState,
  createDashboardFiltersKit,
  createDashboardFormActions,
  createDashboardLoadingState,
  createDashboardMessageThread,
  createDashboardPageHeader,
  createDashboardSectionCard,
  createDashboardSegmentToggle,
  createDashboardSelectField,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTextAreaField,
  createDashboardTextField,
  DataTable,
  dataTableBemClasses,
  FieldLabel,
  IconButton,
  emptyStateCardBemClasses,
  formActionsBemClasses,
  loadingStateCardBemClasses,
  pageHeaderTitleRowBemClasses,
  RichTextEditor,
  sectionCardPacBemClasses,
  selectFieldPacClasses,
  stateBannerBemClasses,
  textAreaFieldBemClasses,
  textFieldPacClasses,
  usePersistedViewLayout,
} from "@delpi/plugin-ui/index";

export { usePersistedViewLayout };

export {
  HelpdeskListPaginationFooter,
  HelpdeskPagination,
  HelpdeskTablePageSizeSelect,
  HELPDESK_PAGE_SIZE_OPTIONS,
} from "../components/Pagination";

const PREFIX = "helpdesk";
const selectClasses = selectFieldPacClasses(PREFIX);

export const HelpdeskPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(PREFIX, {
    buttonClass: "delpi-ui-action-btn delpi-ui-action-btn--primary",
  }),
  labels: { refresh: "Atualizar", refreshing: "Atualizando…" },
});

export const HelpdeskSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PREFIX),
  labels: { titleHelpAriaLabel: (title) => `Ajuda: ${title}` },
});

export const HelpdeskFormActions = createDashboardFormActions({
  classNames: formActionsBemClasses(PREFIX),
});

export const HelpdeskStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(PREFIX),
});

export const HelpdeskEmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses(PREFIX),
  defaultMessage: "Você ainda não tem chamados.",
});

export const HelpdeskLoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses(PREFIX),
  defaultMessage: "Carregando chamados…",
});

const HelpdeskMessageThreadView = createDashboardMessageThread(PREFIX);

export function HelpdeskMessageThread(
  props: Omit<ComponentProps<typeof HelpdeskMessageThreadView>, "bodyMode" | "showMineIdentity" | "fill">,
) {
  return <HelpdeskMessageThreadView {...props} bodyMode="html" showMineIdentity fill />;
}

export const HelpdeskStatusBadge = createDashboardStatusBadge({ prefix: PREFIX });

export const HelpdeskRecordCard = createDashboardDataRecordCard({ prefix: PREFIX });

const tableClassNames = dataTableBemClasses(PREFIX);

export const helpdeskDataTableClassNames = tableClassNames;

export function HelpdeskIconButton(props: ComponentProps<typeof IconButton>) {
  return <IconButton {...props} />;
}

export function HelpdeskDataTable<T extends object>(
  props: Omit<ComponentProps<typeof DataTable<T>>, "classNames" | "labels">,
) {
  return (
    <DataTable
      classNames={tableClassNames}
      labels={{
        emptyMessage: "Nenhum chamado neste recorte.",
        loadingMessage: "Carregando chamados…",
        sortByAriaLabel: (header) => `Ordenar por ${header}`,
        headerHelpAriaLabel: (header) => `Ajuda: ${header}`,
      }}
      {...props}
    />
  );
}

export const HelpdeskTextField = createDashboardTextField({
  classNames: textFieldPacClasses(PREFIX),
});

export const HelpdeskTextArea = createDashboardTextAreaField({
  classNames: textAreaFieldBemClasses(PREFIX),
});

export type HelpdeskRichTextFieldProps = {
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  icon?: ReactNode;
  ariaLabel?: string;
  minHeight?: number;
  disabled?: boolean;
};

/** Same RichTextEditor for open + reply (M-28). No MentionComposer / image paste. */
export function HelpdeskRichTextField({
  label,
  hint,
  value,
  onChange,
  icon,
  ariaLabel,
  minHeight = 180,
  disabled,
}: HelpdeskRichTextFieldProps) {
  return (
    <div className="helpdesk-field helpdesk-rich-text-field">
      <FieldLabel className="helpdesk-field__label" label={label} hint={hint} icon={icon} />
      <RichTextEditor
        value={value}
        onChange={onChange}
        disabled={disabled}
        portalScopeClassName="dashboard-helpdesk"
        minHeight={minHeight}
        ariaLabel={ariaLabel ?? label}
      />
    </div>
  );
}

const helpdeskFilters = createDashboardFiltersKit({
  prefix: PREFIX,
  labels: { filtersAriaLabel: "Filtros dos chamados" },
  portalScopeClassName: "dashboard-helpdesk",
});

export const HelpdeskFiltersRow = helpdeskFilters.FiltersRow;
export const HelpdeskFilterInput = helpdeskFilters.FilterInputField;
export const HelpdeskFilterSelect = helpdeskFilters.FilterSelectField;

export const HelpdeskSegmentToggle = createDashboardSegmentToggle(PREFIX);
export const HelpdeskDataCardsGrid = createDashboardDataCardsGrid({ prefix: PREFIX });

export const HELPDESK_TICKET_LIST_VIEW_LAYOUT_KEY = "helpdesk:ticket-list:view-layout:v1";

export const HelpdeskAttachmentPreviewStrip = createDashboardAttachmentPreviewStrip({
  classNames: attachmentPreviewStripBemClasses(PREFIX),
  labels: {
    empty: "Nenhum arquivo neste chamado.",
    openAriaLabel: (fileName) => `Abrir ${fileName}`,
    removeAriaLabel: (fileName) => `Remover ${fileName}`,
  },
});

export const HelpdeskSelect = createDashboardSelectField({
  field: selectClasses.field,
  control: selectClasses.control,
  labels: {
    placeholder: "Selecione",
    emptyLabel: "Nenhuma opção",
    control: {
      searchPlaceholder: "Buscar",
      emptyOptions: "Nada encontrado",
      searchAriaLabel: (label) => (label ? `Buscar ${label}` : "Buscar"),
    },
  },
});
