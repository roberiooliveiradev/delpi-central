/**
 * Stub Vitest de `@delpi/plugin-ui/index` — mesmo padrão dos MFEs irmãos:
 * renderiza labels/props essenciais sem carregar o barrel (recharts/xyflow).
 */
import {
  createElement,
  forwardRef,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

type AnyProps = Record<string, unknown>;

function el(tag: string, props: AnyProps | null, ...children: ReactNode[]) {
  return createElement(tag, props, ...children);
}

export function ActionButton(props: {
  children?: ReactNode;
  onClick?: () => void;
  variant?: string;
  type?: "button" | "submit";
  disabled?: boolean;
  "aria-label"?: string;
}) {
  return el(
    "button",
    {
      type: props.type ?? "button",
      disabled: props.disabled,
      onClick: props.onClick,
      "aria-label": props["aria-label"],
    },
    props.children,
  );
}

export function EmptyState(props: { defaultMessage?: string }) {
  return el("p", { "data-testid": "empty-state" }, props.defaultMessage);
}

export function PluginErrorBoundary(props: { children?: ReactNode }) {
  return el("div", null, props.children);
}

export function formatPortalGreeting(input: { firstName?: string | null }) {
  return input.firstName ? `Olá, ${input.firstName}` : "Olá";
}

const passthroughClasses = () => ({});

export const catalogSearchBarBemClasses = passthroughClasses;
export const emptyStateCardBemClasses = passthroughClasses;
export const sectionCardPacBemClasses = passthroughClasses;
export const sectionRouteCardBemClasses = passthroughClasses;
export const stateBannerBemClasses = passthroughClasses;
export const statusBadgeBemClasses = passthroughClasses;
export const titleWithHelpBemClasses = passthroughClasses;

export function createDashboardPageHero() {
  return function PageHero(props: {
    eyebrow?: ReactNode;
    title?: ReactNode;
    description?: ReactNode;
    badge?: ReactNode;
    actions?: ReactNode;
    highlights?: Array<{
      id: string;
      label: ReactNode;
      value: ReactNode;
      description?: ReactNode;
      loading?: boolean;
    }>;
    children?: ReactNode;
    "aria-label"?: string;
  }) {
    return el(
      "header",
      { "aria-label": props["aria-label"] },
      props.eyebrow ? el("p", null, props.eyebrow) : null,
      el("h1", null, props.title),
      props.description ? el("p", null, props.description) : null,
      props.badge,
      props.actions,
      ...(props.highlights ?? []).map((h) =>
        el(
          "div",
          { key: h.id },
          h.label,
          el("span", null, h.loading ? "…" : h.value),
          h.description ?? null,
        ),
      ),
      props.children,
    );
  };
}

export function createDashboardStatusBadge() {
  return function StatusBadge(props: { label?: ReactNode }) {
    return el("span", null, props.label);
  };
}

export function createDashboardSegmentToggle() {
  return function SegmentToggle(props: {
    options?: Array<{ value: string; label: string }>;
    value?: string;
    onChange?: (value: string) => void;
    ariaLabel?: string;
  }) {
    return el(
      "div",
      { role: "group", "aria-label": props.ariaLabel },
      ...(props.options ?? []).map((option) =>
        el(
          "button",
          {
            key: option.value,
            type: "button",
            "aria-pressed": option.value === props.value ? "true" : "false",
            onClick: () => props.onChange?.(option.value),
          },
          option.label,
        ),
      ),
    );
  };
}

export function createDashboardViewTransition() {
  return function ViewTransition(props: { children?: ReactNode }) {
    return el("div", null, props.children);
  };
}

export function createDashboardTitleWithHelp() {
  return function TitleWithHelp(props: { title?: ReactNode; hint?: string }) {
    return el("span", null, props.title);
  };
}

export function createDashboardStateBanner() {
  return function StateBanner(props: {
    children?: ReactNode;
    variant?: string;
  }) {
    return el("div", { role: "status" }, props.children);
  };
}

export function createDashboardLoadingActivityCard() {
  return function LoadingCard(props: { title?: ReactNode }) {
    return el("p", { role: "status" }, props.title);
  };
}

export function createDashboardMetricStrip() {
  return function MetricStrip(props: {
    items?: Array<{
      id: string;
      label?: ReactNode;
      value?: ReactNode;
      description?: ReactNode;
      tone?: string;
      loading?: boolean;
    }>;
    "aria-label"?: string;
  }) {
    return el(
      "div",
      { role: "group", "aria-label": props["aria-label"] },
      (props.items ?? []).map((item) =>
        el(
          "div",
          { key: item.id, "data-tone": item.tone ?? "neutral" },
          el("span", null, item.label),
          el("span", null, item.loading ? "…" : item.value),
          item.description ? el("span", null, item.description) : null,
        ),
      ),
    );
  };
}

export function createMetricKpiCard() {
  return function MetricKpiCard(props: {
    label?: string;
    value?: string;
    hint?: ReactNode;
    icon?: ReactNode;
    tone?: string;
  }) {
    return el(
      "article",
      { "data-tone": props.tone ?? "default" },
      props.icon,
      el("span", null, props.label),
      el("strong", null, props.value),
      props.hint ? el("span", null, props.hint) : null,
    );
  };
}

export function createDashboardSectionCard() {
  return function SectionCard(props: {
    title?: ReactNode;
    subtitle?: ReactNode;
    children?: ReactNode;
  }) {
    return el(
      "section",
      null,
      el("h2", null, props.title),
      props.subtitle,
      props.children,
    );
  };
}

export function createDashboardEventsSection() {
  return function EventsSection(props: {
    title?: ReactNode;
    subtitle?: ReactNode;
    items?: Array<{
      id: string;
      title?: ReactNode;
      description?: ReactNode;
      actionLabel?: string;
      onAction?: () => void;
    }>;
    emptyMessage?: ReactNode;
    listAriaLabel?: string;
  }) {
    const items = props.items ?? [];
    return el(
      "section",
      { "aria-label": props.listAriaLabel },
      el("h2", null, props.title),
      props.subtitle ? el("p", null, props.subtitle) : null,
      items.length === 0
        ? el("p", null, props.emptyMessage)
        : el(
            "ul",
            null,
            items.map((item) =>
              el(
                "li",
                { key: item.id },
                el("span", null, item.title),
                item.description,
                item.actionLabel
                  ? el(
                      "button",
                      { type: "button", onClick: item.onAction },
                      item.actionLabel,
                    )
                  : null,
              ),
            ),
          ),
    );
  };
}

export function createDashboardSectionRouteCard() {
  return function SectionRouteCard(props: {
    title?: ReactNode;
    description?: ReactNode;
    routes?: Array<{ id: string; label: ReactNode; onClick?: () => void }>;
  }) {
    return el(
      "div",
      null,
      el("h3", null, props.title),
      props.description,
      (props.routes ?? []).map((route) =>
        el(
          "button",
          { key: route.id, type: "button", onClick: route.onClick },
          route.label,
        ),
      ),
    );
  };
}

export function createDashboardCatalogSearchBar() {
  return function CatalogSearchBar(props: {
    value?: string;
    onChange?: (value: string) => void;
    hits?: Array<{ id: string; label: ReactNode; groupLabel?: string }>;
    onSelectHit?: (id: string) => void;
    placeholder?: string;
    "aria-label"?: string;
  }) {
    return el("input", {
      "aria-label": props["aria-label"],
      placeholder: props.placeholder,
      value: props.value ?? "",
      onChange: (event: { target: { value: string } }) =>
        props.onChange?.(event.target.value),
    });
  };
}

export function createDashboardRecentAccessStrip() {
  return function RecentStrip(props: {
    label?: ReactNode;
    items?: Array<{ id: string; label: ReactNode }>;
    onSelect?: (id: string) => void;
  }) {
    const items = props.items ?? [];
    if (!items.length) return null;
    return el(
      "div",
      null,
      el("span", null, props.label),
      items.map((item) =>
        el(
          "button",
          {
            key: item.id,
            type: "button",
            onClick: () => props.onSelect?.(item.id),
          },
          item.label,
        ),
      ),
    );
  };
}

export function createDashboardTopBar() {
  return function TopBar(props: {
    items?: Array<{ id: string; label: ReactNode; onSelect?: () => void }>;
    secondary?: ReactNode;
    actions?: ReactNode;
    "aria-label"?: string;
  }) {
    return el(
      "nav",
      { "aria-label": props["aria-label"] },
      (props.items ?? []).map((item) =>
        el(
          "button",
          { key: item.id, type: "button", onClick: item.onSelect },
          item.label,
        ),
      ),
      props.secondary,
      props.actions,
    );
  };
}

export function createDashboardTopBarUtilityCluster() {
  return function Cluster(props: { children?: ReactNode }) {
    return el("div", null, props.children);
  };
}

export function createDashboardTopBarSearchTrigger() {
  return forwardRef<
    HTMLButtonElement,
    { onOpen?: () => void; label?: ReactNode; "aria-label"?: string }
  >(function SearchTrigger(props, ref) {
    return el(
      "button",
      {
        type: "button",
        ref,
        onClick: props.onOpen,
        "aria-label": props["aria-label"],
      },
      props.label,
    );
  });
}

export function createDashboardTopBarUserIdentity() {
  return function Identity(props: {
    displayName?: string | null;
    fallbackLabel?: string;
  }) {
    return el("span", null, props.displayName ?? props.fallbackLabel);
  };
}

export function createDashboardCommandPalette() {
  return function Palette(props: {
    open?: boolean;
    title?: ReactNode;
    value?: string;
    onChange?: (value: string) => void;
    hits?: Array<{ id: string; label: ReactNode }>;
    onSelectHit?: (id: string) => void;
  }) {
    if (!props.open) return null;
    return el(
      "div",
      { role: "dialog" },
      el("h2", null, props.title),
      el("input", {
        value: props.value ?? "",
        onChange: (event: { target: { value: string } }) =>
          props.onChange?.(event.target.value),
      }),
      (props.hits ?? []).map((hit) =>
        el(
          "button",
          {
            key: hit.id,
            type: "button",
            onClick: () => props.onSelectHit?.(hit.id),
          },
          hit.label,
        ),
      ),
    );
  };
}

export const TABLE_PAGE_SIZE_OPTIONS = [25, 50, 100];

export function createDashboardPaginationKit() {
  function Pagination(props: {
    page?: number;
    totalPages?: number;
    onPageChange?: (page: number) => void;
  }) {
    return el(
      "nav",
      { "aria-label": "Paginação" },
      el(
        "button",
        {
          type: "button",
          onClick: () => props.onPageChange?.((props.page ?? 1) - 1),
        },
        "Anterior",
      ),
      el(
        "button",
        {
          type: "button",
          onClick: () => props.onPageChange?.((props.page ?? 1) + 1),
        },
        "Próxima",
      ),
    );
  }
  function TablePageSizeSelect() {
    return null;
  }
  return { Pagination, TablePageSizeSelect };
}

export function createDashboardDataRecordCard() {
  return function DataRecordCard(props: {
    title?: ReactNode;
    subtitle?: ReactNode;
    status?: ReactNode;
    fields?: Array<{ id: string; label?: ReactNode; value?: ReactNode }>;
    context?: ReactNode;
    href?: string;
    onNavigate?: (event: { preventDefault: () => void }) => void;
    "aria-label"?: string;
    ariaLabel?: string;
  }) {
    const content = el(
      "div",
      null,
      el("span", null, props.title),
      props.subtitle ? el("span", null, props.subtitle) : null,
      props.status ? el("span", null, props.status) : null,
      (props.fields ?? []).map((field) =>
        el(
          "span",
          { key: field.id },
          el("span", null, field.label),
          el("span", null, field.value),
        ),
      ),
      props.context ?? null,
    );
    if (props.href != null) {
      return el(
        "a",
        {
          href: props.href,
          onClick: props.onNavigate,
          "aria-label": props.ariaLabel,
        },
        content,
      );
    }
    return el("article", { "aria-label": props.ariaLabel }, content);
  };
}

export function createDashboardDataTableKit() {
  function DataTableSection<T>(props: {
    title?: ReactNode;
    titleHint?: string;
    columns?: Array<{
      key: string;
      header: ReactNode;
      render?: (row: T) => ReactNode;
      sortable?: boolean;
      sortValue?: (row: T) => string | number | null | undefined;
      rowClick?: "stop" | "propagate";
    }>;
    rows?: T[];
    rowKey?: (row: T) => string;
    loading?: boolean;
    emptyMessage?: string;
    headerActions?: ReactNode;
    onRowClick?: (row: T) => void;
    renderCard?: (row: T) => ReactNode;
    viewLayoutPreferencesKey?: string;
    columnPreferencesKey?: string;
    getSearchText?: (row: T) => string;
    hideSearch?: boolean;
    searchPlaceholder?: string;
    toolbarPortalTarget?: HTMLElement | null;
    tableLayout?: "section" | "scroll";
    serverPagination?: {
      page: number;
      pageSize: number;
      total: number;
      onPageChange: (page: number) => void;
    };
  }) {
    const columns = props.columns ?? [];
    const rows = props.rows ?? [];
    const pager = props.serverPagination;
    const totalPages = pager ? Math.max(1, Math.ceil(pager.total / pager.pageSize)) : 1;
    const [sortKey, setSortKey] = useState<string | null>(null);
    const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
    const [cardsOn, setCardsOn] = useState(false);
    const [search, setSearch] = useState("");
    const canToggleCards = Boolean(
      props.viewLayoutPreferencesKey && props.renderCard,
    );

    const filteredRows = (() => {
      const query = search.trim().toLowerCase();
      if (!query) return rows;
      const searchText = props.getSearchText ?? (() => "");
      return rows.filter((row) =>
        searchText(row).toLowerCase().includes(query),
      );
    })();

    const sortedRows = (() => {
      if (!sortKey) return filteredRows;
      const column = columns.find((c) => c.key === sortKey);
      if (!column?.sortValue) return filteredRows;
      const factor = sortDir === "asc" ? 1 : -1;
      return [...filteredRows].sort((a, b) => {
        const va = column.sortValue?.(a);
        const vb = column.sortValue?.(b);
        if (va == null && vb == null) return 0;
        if (va == null) return factor;
        if (vb == null) return -factor;
        if (typeof va === "number" && typeof vb === "number")
          return (va - vb) * factor;
        return String(va).localeCompare(String(vb), "pt-BR") * factor;
      });
    })();

    const toolbarNode = el(
      "div",
      { className: "cf-table-toolbar" },
      canToggleCards
        ? el(
            "button",
            {
              type: "button",
              "aria-pressed": cardsOn,
              onClick: () => setCardsOn((v) => !v),
            },
            cardsOn ? "Tabela" : "Cards",
          )
        : null,
      props.columnPreferencesKey
        ? el(
            "button",
            { type: "button", "aria-label": "Colunas" },
            "Colunas",
          )
        : null,
      props.hideSearch
        ? null
        : el("input", {
            type: "search",
            role: "search",
            value: search,
            placeholder:
              props.searchPlaceholder ?? "Buscar…",
            "aria-label": "Buscar",
            onChange: (event: { target: { value: string } }) =>
              setSearch(event.target.value),
          }),
    );

    const body = cardsOn ? null : (
      sortedRows.length > 0
        ? el(
            "table",
            null,
            el(
              "thead",
              null,
              el(
                "tr",
                null,
                columns.map((c) =>
                  c.sortable
                    ? el(
                        "th",
                        { key: c.key },
                        el(
                          "button",
                          {
                            type: "button",
                            "aria-label": `Ordenar por ${typeof c.header === "string" ? c.header : c.key}`,
                            onClick: () => {
                              if (sortKey === c.key) {
                                setSortDir((d) =>
                                  d === "asc" ? "desc" : "asc",
                                );
                              } else {
                                setSortKey(c.key);
                                setSortDir("asc");
                              }
                            },
                          },
                          c.header,
                        ),
                      )
                    : el("th", { key: c.key }, c.header),
                ),
              ),
            ),
            el(
              "tbody",
              null,
              sortedRows.map((row, index) =>
                el(
                  "tr",
                  {
                    key: props.rowKey?.(row) ?? String(index),
                    onClick: props.onRowClick
                      ? () => props.onRowClick?.(row)
                      : undefined,
                    tabIndex: props.onRowClick ? 0 : undefined,
                  },
                  columns.map((c) =>
                    el(
                      "td",
                      {
                        key: c.key,
                        onClick:
                          c.rowClick === "stop"
                            ? (event: { stopPropagation: () => void }) =>
                                event.stopPropagation()
                            : undefined,
                      },
                      c.render
                        ? c.render(row)
                        : String((row as Record<string, unknown>)[c.key] ?? ""),
                    ),
                  ),
                ),
              ),
            ),
          )
        : null
    );

    return el(
      "section",
      null,
      el("h2", null, props.title),
      props.headerActions ?? null,
      props.toolbarPortalTarget
        ? createPortal(toolbarNode, props.toolbarPortalTarget)
        : toolbarNode,
      pager
        ? el(
            "span",
            { className: "cf-table-section__meta delpi-ui-table-section__meta" },
            `${pager.total.toLocaleString("pt-BR")} ${pager.total === 1 ? "registro" : "registros"}`,
          )
        : null,
      props.loading ? el("p", { role: "status" }, "Carregando…") : null,
      !props.loading && sortedRows.length === 0
        ? el("p", null, props.emptyMessage)
        : null,
      cardsOn
        ? el(
            "div",
            { "data-view": "cards" },
            sortedRows.map((row, index) =>
              el(
                "div",
                { key: props.rowKey?.(row) ?? String(index) },
                props.renderCard?.(row),
              ),
            ),
          )
        : null,
      body,
      pager
        ? el(
            "nav",
            { "aria-label": "Paginação da tabela" },
            el(
              "button",
              {
                type: "button",
                disabled: pager.page <= 1,
                onClick: () => pager.onPageChange(pager.page - 1),
              },
              "Anterior",
            ),
            el(
              "button",
              {
                type: "button",
                disabled: pager.page >= totalPages,
                onClick: () => pager.onPageChange(pager.page + 1),
              },
              "Próxima",
            ),
          )
        : null,
    );
  }
  return { DataTableSection };
}

export function createDashboardFiltersKit() {
  function FiltersRow(props: { children?: ReactNode; ariaLabel?: string }) {
    return el("div", { role: "group", "aria-label": props.ariaLabel }, props.children);
  }
  function FilterInputField(props: {
    label: string;
    hint?: string;
    id?: string;
    type?: string;
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
  }) {
    return el("input", {
      id: props.id,
      type: props.type ?? "text",
      "aria-label": props.label,
      placeholder: props.placeholder,
      value: props.value,
      onChange: (event: { target: { value: string } }) =>
        props.onChange(event.target.value),
    });
  }
  function FilterSelectField(props: {
    label: string;
    value: string;
    onChange: (value: string) => void;
    options?: Array<{ value: string; label: string }>;
    placeholderOption?: string;
  }) {
    return el(
      "select",
      {
        "aria-label": props.label,
        value: props.value,
        onChange: (event: { target: { value: string } }) =>
          props.onChange(event.target.value),
      },
      props.placeholderOption
        ? el("option", { value: "" }, props.placeholderOption)
        : null,
      (props.options ?? []).map((option) =>
        el("option", { key: option.value, value: option.value }, option.label),
      ),
    );
  }
  return { FiltersRow, FilterInputField, FilterSelectField };
}

export const fileDropzoneBemClasses = passthroughClasses;
export const attachmentFileListBemClasses = passthroughClasses;

export function FileDropzone(props: {
  labels?: { title?: string; hint?: string };
  onFilesSelected?: (files: File[]) => void;
  disabled?: boolean;
  busy?: boolean;
  ariaLabel?: string;
}) {
  return el(
    "button",
    {
      type: "button",
      disabled: props.disabled || props.busy,
      "aria-label": props.ariaLabel ?? props.labels?.title,
      onClick: () =>
        props.onFilesSelected?.([
          new File(["%PDF-1.4 teste"], "evidencia.pdf", {
            type: "application/pdf",
          }),
        ]),
    },
    props.labels?.title,
  );
}

export function AttachmentFileList(props: {
  items?: Array<{ id: string; fileName: string; detail?: string }>;
  labels?: { empty?: string; download?: string };
  emptyMessage?: string;
  onDownload?: (item: { id: string; fileName: string }) => void;
  itemActions?: (item: {
    id: string;
    fileName: string;
  }) => ReactNode;
}) {
  const items = props.items ?? [];
  if (items.length === 0) {
    return el("p", null, props.emptyMessage ?? props.labels?.empty ?? "");
  }
  return el(
    "ul",
    null,
    items.map((item) =>
      el(
        "li",
        { key: item.id },
        el("span", null, item.fileName),
        el(
          "button",
          { type: "button", onClick: () => props.onDownload?.(item) },
          props.labels?.download ?? "Baixar",
        ),
        props.itemActions?.(item) ?? null,
      ),
    ),
  );
}

export function createHostContainedModalShell() {
  return function HostContainedModalShell(props: {
    open?: boolean;
    title?: string;
    onClose?: () => void;
    closeAriaLabel?: string;
    children?: ReactNode;
  }) {
    if (!props.open) return null;
    return el(
      "div",
      { role: "dialog", "aria-label": props.title },
      el("h2", null, props.title),
      el(
        "button",
        {
          type: "button",
          "aria-label": props.closeAriaLabel ?? "Fechar",
          onClick: props.onClose,
        },
        "×",
      ),
      props.children,
    );
  };
}

export const confirmModalBemClasses = passthroughClasses;
export const textFieldBemClasses = passthroughClasses;
export const textAreaFieldBemClasses = passthroughClasses;
export const dateFieldBemClasses = passthroughClasses;
export const selectFieldPacClasses = () => ({
  field: passthroughClasses(),
  control: passthroughClasses(),
});

type MockFieldProps = {
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
};

export function createDashboardTextField() {
  return function MockTextField(
    props: MockFieldProps & { type?: string; fullWidth?: boolean },
  ) {
    return el("input", {
      type: props.type ?? "text",
      "aria-label": props.label,
      value: props.value,
      disabled: props.disabled,
      placeholder: props.placeholder,
      onChange: (event: { target: { value: string } }) =>
        props.onChange(event.target.value),
    });
  };
}

export function createDashboardTextAreaField() {
  return function MockTextAreaField(
    props: MockFieldProps & { rows?: number; fullWidth?: boolean },
  ) {
    return el("textarea", {
      "aria-label": props.label,
      rows: props.rows,
      value: props.value,
      disabled: props.disabled,
      onChange: (event: { target: { value: string } }) =>
        props.onChange(event.target.value),
    });
  };
}

export function createDashboardDateField() {
  return function MockDateField(
    props: MockFieldProps & { type?: string; wide?: boolean },
  ) {
    return el("input", {
      type: props.type ?? "text",
      "aria-label": props.label,
      value: props.value,
      disabled: props.disabled,
      onChange: (event: { target: { value: string } }) =>
        props.onChange(event.target.value),
    });
  };
}

export function createDashboardSelectField() {
  return function MockSelectField(
    props: MockFieldProps & {
      options?: Array<{ value: string; label: string }>;
    },
  ) {
    return el(
      "select",
      {
        "aria-label": props.label,
        value: props.value,
        disabled: props.disabled,
        onChange: (event: { target: { value: string } }) =>
          props.onChange(event.target.value),
      },
      (props.options ?? []).map((option) =>
        el(
          "option",
          { key: option.value, value: option.value },
          option.label,
        ),
      ),
    );
  };
}

export function ContextMenu(props: {
  open?: boolean;
  "aria-label"?: string;
  children?: ReactNode;
}) {
  if (!props.open) return null;
  return el(
    "div",
    { role: "menu", "aria-label": props["aria-label"] },
    props.children,
  );
}

export function ContextMenuItem(props: {
  label?: string;
  disabled?: boolean;
  onSelect?: () => void;
}) {
  return el(
    "button",
    {
      type: "button",
      role: "menuitem",
      disabled: props.disabled,
      onClick: props.onSelect,
    },
    props.label,
  );
}

export function ContextMenuDivider() {
  return el("hr", null);
}

export function ConfirmModalPanel(props: {
  message?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmBusy?: boolean;
  onConfirm?: () => void;
  onCancel?: () => void;
}) {
  return el(
    "div",
    null,
    el("p", null, props.message),
    el(
      "button",
      {
        type: "button",
        disabled: props.confirmBusy,
        onClick: props.onConfirm,
      },
      props.confirmLabel ?? "Confirmar",
    ),
    el(
      "button",
      { type: "button", onClick: props.onCancel },
      props.cancelLabel ?? "Cancelar",
    ),
  );
}

export function createDashboardInteractiveDataCard() {
  return function InteractiveDataCard(props: {
    fields?: Array<{
      id: string;
      label: string;
      value?: ReactNode;
      present?: boolean;
    }>;
    ariaLabel?: string;
    openHint?: ReactNode;
    onActivate?: () => void;
    children?: ReactNode;
  }) {
    return el(
      "button",
      {
        type: "button",
        "aria-label": props.ariaLabel,
        onClick: props.onActivate,
      },
      ...(props.fields ?? []).map((field) =>
        el(
          "span",
          { key: field.id },
          el("span", null, field.label),
          el("strong", null, field.value),
          el("span", null, (field as { hint?: string }).hint),
        ),
      ),
      props.openHint,
      props.children,
    );
  };
}

export const pagePathBemClasses = passthroughClasses;

export function createDashboardPagePath() {
  return function PagePath(props: {
    back?: { label?: ReactNode; onNavigate?: (e: unknown) => void };
    items?: Array<{
      id: string;
      label?: ReactNode;
      onNavigate?: (e: unknown) => void;
    }>;
    current?: ReactNode;
    ariaLabel?: string;
  }) {
    return el(
      "nav",
      { "aria-label": props.ariaLabel ?? "Caminho da página" },
      props.back
        ? el(
            "button",
            { type: "button", onClick: props.back.onNavigate },
            props.back.label,
          )
        : null,
      ...(props.items ?? []).map((item) =>
        el(
          "button",
          { key: item.id, type: "button", onClick: item.onNavigate },
          item.label,
        ),
      ),
      el("span", { "aria-current": "page" }, props.current),
    );
  };
}

type MockPreviewState = {
  kind: string;
  loading: boolean;
  error: string | null;
  previewUrl: string | null;
  textContent: string | null;
  textTruncated: boolean;
  spreadsheetData: null;
  docxData: null;
};

const MOCK_PREVIEW_EMPTY: MockPreviewState = {
  kind: "none",
  loading: false,
  error: null,
  previewUrl: null,
  textContent: null,
  textTruncated: false,
  spreadsheetData: null,
  docxData: null,
};

/**
 * Réplica fiel do comportamento relevante do hook real: resolve `source`
 * em efeito dependente da IDENTIDADE de `source` — uma closure nova por
 * render provocaria refetch a cada render (regressão real do U4).
 */
export function useFilePreviewLoader(options?: {
  source?: (() => Promise<Blob>) | Blob | null;
  mimeType?: string | null;
  fileName?: string | null;
  enabled?: boolean;
}): MockPreviewState {
  const enabled = options?.enabled !== false && Boolean(options?.source);
  const [state, setState] = useState<MockPreviewState>({
    ...MOCK_PREVIEW_EMPTY,
    kind: enabled ? "pdf" : "none",
    loading: enabled,
  });
  useEffect(() => {
    let cancelled = false;
    const source = enabled ? (options?.source ?? null) : null;
    Promise.resolve()
      .then(() => {
        if (cancelled) return null;
        if (!source) {
          setState({ ...MOCK_PREVIEW_EMPTY });
          return null;
        }
        setState((current) => ({
          ...current,
          kind: "pdf",
          loading: true,
          error: null,
          previewUrl: null,
        }));
        return typeof source === "function" ? source() : source;
      })
      .then((blob) => {
        if (cancelled || !blob) return;
        setState({
          ...MOCK_PREVIEW_EMPTY,
          kind: "pdf",
          previewUrl: "blob:mock-preview",
        });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setState({
          ...MOCK_PREVIEW_EMPTY,
          kind: "pdf",
          error: err instanceof Error ? err.message : "load_failed",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [options?.source, enabled]);
  return state;
}

export function FilePreviewView(props: {
  state?: { kind?: string; loading?: boolean; error?: unknown };
  title?: string;
}) {
  const state = props.state;
  const content = state?.loading
    ? "Carregando pré-visualização..."
    : state?.error
      ? `Falha na pré-visualização: ${String(state.error)}`
      : (props.title ?? state?.kind ?? "");
  return el("div", { "data-testid": "file-preview" }, content);
}

// -- Colaboração (U9) — render simples e controlado --------------------------

export type MockMessageThreadItem = {
  id: string;
  bodyText: string;
  createdAtLabel?: string;
  authorName?: string | null;
  authorUserId?: string | null;
  authorSrc?: string | null;
  mine?: boolean;
};

export function createDashboardMessageThread() {
  return function MessageThread(props: {
    messages?: readonly MockMessageThreadItem[];
    emptyLabel?: string;
    listAriaLabel?: string;
  }) {
    const items = props.messages ?? [];
    return el(
      "ul",
      { "aria-label": props.listAriaLabel },
      items.length === 0 ? el("li", null, props.emptyLabel) : null,
      items.map((item) =>
        el(
          "li",
          {
            key: item.id,
            "data-mine": item.mine ? "true" : "false",
            "data-author-id": item.authorUserId ?? "",
            "data-author-src": item.authorSrc ?? "",
          },
          `${item.authorName ?? ""} ${item.createdAtLabel ?? ""} ${item.bodyText}`,
        ),
      ),
    );
  };
}

export function createDashboardMentionComposer() {
  return function MentionComposer(props: {
    value?: string;
    onChange?: (value: string) => void;
    onSubmit?: (markdown: string) => void;
    disabled?: boolean;
    submitting?: boolean;
    labels?: { placeholder?: string; sendAriaLabel?: string };
  }) {
    return el(
      "div",
      null,
      el("textarea", {
        "aria-label": props.labels?.placeholder,
        value: props.value ?? "",
        disabled: props.disabled,
        onChange: (event: { target: { value: string } }) =>
          props.onChange?.(event.target.value),
      }),
      el(
        "button",
        {
          type: "button",
          "aria-label": props.labels?.sendAriaLabel,
          disabled: props.disabled,
          onClick: () => props.onSubmit?.(props.value ?? ""),
        },
        props.submitting ? "Enviando…" : "Enviar mensagem",
      ),
    );
  };
}

// -- Linha do tempo + avatar (UX-009) ---------------------------------------

export type MockTimelineItem = {
  id: string;
  title?: unknown;
  timeLabel?: unknown;
  detail?: unknown;
  meta?: unknown;
  marker?: unknown;
};

export function createTimeline() {
  return function Timeline(props: {
    items?: readonly MockTimelineItem[];
    emptyMessage?: string;
    "aria-label"?: string;
  }) {
    const items = props.items ?? [];
    return el(
      "ol",
      { "aria-label": props["aria-label"] },
      items.length === 0
        ? el("li", null, props.emptyMessage)
        : null,
      items.map((item) =>
        el(
          "li",
          { key: item.id },
          item.marker as never,
          el("strong", null, item.title as never),
          el("span", null, `${item.timeLabel ?? ""}`),
          el("span", null, `${item.detail ?? ""}`),
          el("span", null, `${item.meta ?? ""}`),
        ),
      ),
    );
  };
}

export function UnifiedAvatar(props: {
  kind?: string;
  imageUrl?: string | null;
  fallbackText?: string | null;
}) {
  return el("span", {
    "data-avatar-kind": props.kind ?? "",
    "data-avatar-src": props.imageUrl ?? "",
    "data-avatar-name": props.fallbackText ?? "",
  });
}

