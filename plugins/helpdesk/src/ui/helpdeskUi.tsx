import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type ComponentProps,
  type ReactNode,
} from "react";
import {
  ActionButton,
  attachmentPreviewStripBemClasses,
  createDashboardAttachmentPreviewStrip,
  createDashboardConversationFileDropLayer,
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
  createDashboardScreenLoading,
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
  screenLoadingBemClasses,
  type MentionMenuHit,
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

import { listUsers } from "../api/helpdeskApi";

export { usePersistedViewLayout };

export {
  HelpdeskListPaginationFooter,
  HelpdeskPagination,
  HelpdeskTablePageSizeSelect,
  HELPDESK_PAGE_SIZE_OPTIONS,
} from "../components/Pagination";

const PREFIX = "helpdesk";
const selectClasses = selectFieldPacClasses(PREFIX);
const MENTION_SEARCH_DEBOUNCE_MS = 250;
const HELPDESK_MENTION_LABELS = {
  listAriaLabel: "Sugestões de menção",
  emptyLabel: "Nenhum usuário encontrado",
};

/** Overlay de arrastar-para-anexar — paridade InteractionRoom (plugin-ui). */
export const HelpdeskConversationFileDrop =
  createDashboardConversationFileDropLayer(PREFIX);

export const HELPDESK_COMPOSE_DROP_OVERLAY = "Solte o arquivo para anexar";

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

/** Splash de página — ScreenLoading do plugin-ui (badge + pulse). */
export const HelpdeskScreenLoading = createDashboardScreenLoading({
  classNames: screenLoadingBemClasses(PREFIX),
  defaultLabel: "Carregando",
  variant: "embedded",
  tone: "brand",
  logoSrc: "/logoMinhaDelpi.svg",
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

export type HelpdeskRichTextFieldHandle = {
  openAttachPicker: () => void;
};

export type HelpdeskRichTextFieldProps = {
  label: string;
  hint?: string;
  /** Ajuda do botão clipe (anexar) — só usada se `showAttachButton`. */
  attachHint?: string;
  value: string;
  onChange: (value: string) => void;
  icon?: ReactNode;
  ariaLabel?: string;
  minHeight?: number;
  /** Occupy remaining flex height in create/reply layouts. */
  fill?: boolean;
  disabled?: boolean;
  /** When false (default), host places Anexar next to Enviar via `openAttachPicker`. */
  showAttachButton?: boolean;
  /** H12 — colar/arrastar imagem ou escolher arquivo. */
  onUploadFiles?: (files: File[]) => Promise<HelpdeskInlineUploadResult[]>;
  onUploadError?: (error: unknown) => void;
  accept?: string;
  /** Kit contract: display blob for `data-attachment-id` (MessageThread parity). */
  resolveAttachmentImageSrc?: (attachmentId: string) => string | null | undefined;
  /** Kit contract: persist stable BFF URL before onChange. */
  persistAttachmentImageSrc?: (attachmentId: string) => string | null | undefined;
  /**
   * M-23 — digitar @ busca GET /users e grava span data-user-id.
   * Ligado no create e reply (mesmo campo).
   */
  enableMentions?: boolean;
};

/** CTA Anexar — placed next to Enviar in form actions. */
export function HelpdeskAttachButton({
  hint,
  disabled,
  onClick,
  className,
}: {
  hint?: string;
  disabled?: boolean;
  onClick: () => void;
  className?: string;
}) {
  const button = (
    <ActionButton
      type="button"
      variant="ghost"
      className={className}
      aria-label="Anexar"
      disabled={disabled}
      onClick={onClick}
    >
      <Paperclip size={16} aria-hidden />
      Anexar
    </ActionButton>
  );
  if (!hint) return button;
  return (
    <HintAction hint={hint} ariaLabel="Ajuda: Anexar arquivo">
      {button}
    </HintAction>
  );
}

/** Same RichTextEditor for open + reply (M-28). H12 paste/attach; M-23 @ via GET /users. */
export const HelpdeskRichTextField = forwardRef<
  HelpdeskRichTextFieldHandle,
  HelpdeskRichTextFieldProps
>(function HelpdeskRichTextField(
  {
    label,
    hint,
    attachHint,
    value,
    onChange,
    icon,
    ariaLabel,
    minHeight = 180,
    fill = false,
    disabled,
    showAttachButton = false,
    onUploadFiles,
    onUploadError,
    accept = "image/*,.pdf,.png,.jpg,.jpeg,.gif,.webp,.doc,.docx,.xls,.xlsx,.txt",
    resolveAttachmentImageSrc,
    persistAttachmentImageSrc,
    enableMentions = false,
  },
  ref,
) {
  const fileRef = useRef<HTMLInputElement>(null);
  const editorRef = useRef<RichTextEditorHandle>(null);
  const uploadingRef = useRef(false);
  const mentionDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mentionAbortRef = useRef<AbortController | null>(null);
  const [mentionHits, setMentionHits] = useState<MentionMenuHit[]>([]);

  useImperativeHandle(
    ref,
    () => ({
      openAttachPicker: () => {
        fileRef.current?.click();
      },
    }),
    [],
  );

  useEffect(() => {
    return () => {
      if (mentionDebounceRef.current) clearTimeout(mentionDebounceRef.current);
      mentionAbortRef.current?.abort();
    };
  }, []);

  const handleMentionQueryChange = useCallback(
    (query: string | null) => {
      if (!enableMentions) return;
      if (mentionDebounceRef.current) clearTimeout(mentionDebounceRef.current);
      mentionAbortRef.current?.abort();
      if (query === null) {
        setMentionHits([]);
        return;
      }
      mentionDebounceRef.current = setTimeout(() => {
        const controller = new AbortController();
        mentionAbortRef.current = controller;
        void listUsers({ q: query, limit: 20 }, controller.signal)
          .then((result) => {
            if (controller.signal.aborted) return;
            setMentionHits(
              (result.items || []).map((user) => ({
                id: String(user.id),
                kind: "user",
                label: user.display_name || String(user.id),
                subtitle: (user.email || "").trim() || undefined,
                avatarName: user.display_name || user.email || String(user.id),
              })),
            );
          })
          .catch(() => {
            if (controller.signal.aborted) return;
            setMentionHits([]);
          });
      }, MENTION_SEARCH_DEBOUNCE_MS);
    },
    [enableMentions],
  );

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

  const fieldBody = (
    <>
      <FieldLabel className="helpdesk-field__label" label={label} hint={hint} icon={icon} />
      <RichTextEditor
        ref={editorRef}
        value={value}
        onChange={onChange}
        disabled={disabled}
        fill={fill}
        portalScopeClassName="dashboard-helpdesk"
        minHeight={minHeight}
        ariaLabel={ariaLabel ?? label}
        resolveAttachmentImageSrc={resolveAttachmentImageSrc}
        persistAttachmentImageSrc={persistAttachmentImageSrc}
        onPasteImages={onUploadFiles && !disabled ? materializeUploads : undefined}
        onPasteImagesError={onUploadError}
        mentionHits={enableMentions ? mentionHits : undefined}
        onMentionQueryChange={enableMentions ? handleMentionQueryChange : undefined}
        mentionLabels={enableMentions ? HELPDESK_MENTION_LABELS : undefined}
      />
      {onUploadFiles ? (
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
      ) : null}
      {onUploadFiles && showAttachButton ? (
        <div className="helpdesk-rich-text-field__attach">
          <HelpdeskAttachButton
            hint={attachHint}
            disabled={disabled}
            onClick={() => fileRef.current?.click()}
          />
        </div>
      ) : null}
    </>
  );

  return (
    <div
      className={[
        "helpdesk-field",
        "helpdesk-rich-text-field",
        fill ? "helpdesk-rich-text-field--fill" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {onUploadFiles ? (
        <HelpdeskConversationFileDrop
          overlayLabel={HELPDESK_COMPOSE_DROP_OVERLAY}
          accept={accept}
          disabled={Boolean(disabled)}
          onFiles={(files) => {
            void ingestViaEditor(files);
          }}
        >
          {fieldBody}
        </HelpdeskConversationFileDrop>
      ) : (
        fieldBody
      )}
    </div>
  );
});

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
