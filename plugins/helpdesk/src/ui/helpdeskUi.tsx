import { useRef, type ComponentProps, type DragEvent, type ReactNode } from "react";
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
  HintAction,
  IconButton,
  emptyStateCardBemClasses,
  formActionsBemClasses,
  loadingStateCardBemClasses,
  pageHeaderTitleRowBemClasses,
  RichTextEditor,
  type RichTextEditorHandle,
  type RichTextInlineImageInsert,
  sectionCardPacBemClasses,
  selectFieldPacClasses,
  stateBannerBemClasses,
  textAreaFieldBemClasses,
  textFieldPacClasses,
  usePersistedViewLayout,
} from "@delpi/plugin-ui/index";
import { Paperclip } from "lucide-react";


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

export type HelpdeskInlineUploadResult =
  | { kind: "uploaded"; documentId: number; src: string; alt?: string }
  | { kind: "pending"; pendingId: string; src: string; alt?: string };

export type HelpdeskRichTextFieldProps = {
  label: string;
  hint?: string;
  /** Ajuda do botão clipe (anexar). */
  attachHint?: string;
  value: string;
  onChange: (value: string) => void;
  icon?: ReactNode;
  ariaLabel?: string;
  minHeight?: number;
  disabled?: boolean;
  /** H12 — colar/arrastar imagem ou escolher arquivo. */
  onUploadFiles?: (files: File[]) => Promise<HelpdeskInlineUploadResult[]>;
  onUploadError?: (error: unknown) => void;
  accept?: string;
  /** Kit contract: display blob for `data-attachment-id` (MessageThread parity). */
  resolveAttachmentImageSrc?: (attachmentId: string) => string | null | undefined;
  /** Kit contract: persist stable BFF URL before onChange. */
  persistAttachmentImageSrc?: (attachmentId: string) => string | null | undefined;
};

/** Same RichTextEditor for open + reply (M-28). H12 adds paste/attach without MentionComposer. */
export function HelpdeskRichTextField({
  label,
  hint,
  attachHint,
  value,
  onChange,
  icon,
  ariaLabel,
  minHeight = 180,
  disabled,
  onUploadFiles,
  onUploadError,
  accept = "image/*,.pdf,.png,.jpg,.jpeg,.gif,.webp,.doc,.docx,.xls,.xlsx,.txt",
  resolveAttachmentImageSrc,
  persistAttachmentImageSrc,
}: HelpdeskRichTextFieldProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const editorRef = useRef<RichTextEditorHandle>(null);
  const uploadingRef = useRef(false);

  /** Host only materializes File → src/attrs; kit inserts at caret (S-P2). */
  const materializeUploads = async (
    files: File[],
  ): Promise<RichTextInlineImageInsert[]> => {
    if (!onUploadFiles || disabled || uploadingRef.current || files.length === 0) {
      return [];
    }
    uploadingRef.current = true;
    try {
      const results = await onUploadFiles(files);
      return results.map((item): RichTextInlineImageInsert => {
        if (item.kind === "uploaded") {
          return {
            src: item.src,
            documentId: item.documentId,
            alt: item.alt,
          };
        }
        return {
          src: item.src,
          pendingId: item.pendingId,
          alt: item.alt,
        };
      });
    } catch (error) {
      throw error;
    } finally {
      uploadingRef.current = false;
    }
  };

  const ingestViaEditor = async (files: File[]) => {
    try {
      const inserts = await materializeUploads(files);
      if (inserts && inserts.length > 0) {
        editorRef.current?.insertInlineImages(inserts);
      }
    } catch (error) {
      onUploadError?.(error);
    }
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    if (!onUploadFiles || disabled) return;
    const files = Array.from(event.dataTransfer?.files || []).filter((file) =>
      (file.type || "").startsWith("image/") || /\.(png|jpe?g|gif|webp|bmp)$/i.test(file.name || ""),
    );
    if (files.length === 0) return;
    event.preventDefault();
    event.stopPropagation();
    void ingestViaEditor(files);
  };

  return (
    <div
      className="helpdesk-field helpdesk-rich-text-field"
      onDrop={onDrop}
      onDragOver={(event) => {
        if (onUploadFiles && !disabled) event.preventDefault();
      }}
    >
      <FieldLabel className="helpdesk-field__label" label={label} hint={hint} icon={icon} />
      <RichTextEditor
        ref={editorRef}
        value={value}
        onChange={onChange}
        disabled={disabled}
        portalScopeClassName="dashboard-helpdesk"
        minHeight={minHeight}
        ariaLabel={ariaLabel ?? label}
        resolveAttachmentImageSrc={resolveAttachmentImageSrc}
        persistAttachmentImageSrc={persistAttachmentImageSrc}
        onPasteImages={onUploadFiles && !disabled ? materializeUploads : undefined}
        onPasteImagesError={onUploadError}
      />
      {onUploadFiles ? (
        <div className="helpdesk-rich-text-field__attach">
          <input
            ref={fileRef}
            type="file"
            accept={accept}
            multiple
            hidden
            onChange={(event) => {
              const files = Array.from(event.target.files || []);
              event.target.value = "";
              void ingestViaEditor(files);
            }}
          />
          {attachHint ? (
            <HintAction hint={attachHint} ariaLabel="Ajuda: Anexar arquivo">
              <IconButton
                type="button"
                aria-label="Anexar arquivo"
                disabled={disabled}
                onClick={() => fileRef.current?.click()}
              >
                <Paperclip size={16} aria-hidden />
              </IconButton>
            </HintAction>
          ) : (
            <IconButton
              type="button"
              aria-label="Anexar arquivo"
              disabled={disabled}
              onClick={() => fileRef.current?.click()}
            >
              <Paperclip size={16} aria-hidden />
            </IconButton>
          )}
        </div>
      ) : null}
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
