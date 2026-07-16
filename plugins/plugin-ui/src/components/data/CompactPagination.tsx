import { useMemo } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { ToolbarSelectControl } from "../forms/ToolbarSelectField";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type CompactPaginationClassNames = {
  root: string;
  left: string;
  info: string;
  pageSize: string;
  actions: string;
  ghostBtn: string;
  action?: string;
  infoHelp?: string;
  actionHelp?: string;
};

export type CompactPaginationLayout = "grouped" | "flat";

export type CompactPaginationLabels = {
  info: (args: { page: number; totalPages: number; total: number; pageSize: number }) => string;
  pageSizeLabel?: string;
  previous: string;
  next: string;
  navigationAriaLabel: string;
};

export type CompactPaginationHints = {
  info?: string;
  previous?: string;
  next?: string;
};

export type CompactPaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  totalPages?: number;
  pageSizeOptions?: readonly number[];
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  layout?: CompactPaginationLayout;
  hints?: CompactPaginationHints;
  hideWhenSinglePage?: boolean;
  /** Desabilita nav e page-size (ex.: fetch em andamento). */
  disabled?: boolean;
  classNames: CompactPaginationClassNames;
  labels: CompactPaginationLabels;
};

export function compactPaginationBemClasses(
  prefix: string,
  options?: { ghostBtnModifier?: string; ghostBtn?: string; withHints?: boolean },
): CompactPaginationClassNames {
  const base = `${prefix}-pagination`;
  const ui = "delpi-ui-pagination";
  const uiCompact = "delpi-ui-pagination--compact";
  const ghostModifier = options?.ghostBtnModifier ?? "ghost";
  const withHints = options?.withHints ?? false;
  const ghostBtn = options?.ghostBtn
    ? delpiUiClass(options.ghostBtn, "delpi-ui-ghost-btn")
    : delpiUiClass(`${prefix}-btn ${prefix}-btn--${ghostModifier}`, "delpi-ui-ghost-btn");

  return {
    root: delpiUiClass(base, `${ui} ${uiCompact}`),
    left: delpiUiClass(`${base}__left`, `${ui}__left`),
    info: delpiUiClass(`${base}__info`, `${ui}__info`),
    pageSize: delpiUiClass(`${base}__size`, `${ui}__size`),
    actions: delpiUiClass(`${base}__actions`, `${ui}__actions`),
    ghostBtn,
    action: withHints ? delpiUiClass(`${base}__action`, `${ui}__action`) : undefined,
    infoHelp: withHints ? delpiUiClass(`${base}__help`, `${ui}__help`) : undefined,
    actionHelp: withHints
      ? delpiUiClass(`${base}__action-help`, `${ui}__action-help`)
      : undefined,
  };
}

export function CompactPagination({
  page,
  pageSize,
  total,
  totalPages,
  pageSizeOptions,
  onPageChange,
  onPageSizeChange,
  layout = "grouped",
  hints,
  hideWhenSinglePage = false,
  disabled = false,
  classNames,
  labels,
}: CompactPaginationProps) {
  const resolvedTotalPages =
    totalPages ?? (pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1);
  const canPrev = !disabled && page > 1;
  const canNext = !disabled && page < resolvedTotalPages;
  const showPageSize =
    onPageSizeChange != null && pageSizeOptions != null && pageSizeOptions.length > 0;
  const pageSizeSelectOptions = useMemo(
    () =>
      (pageSizeOptions ?? []).map((option) => ({
        value: String(option),
        label: String(option),
      })),
    [pageSizeOptions],
  );

  if (total === 0) return null;
  if (hideWhenSinglePage && resolvedTotalPages <= 1) return null;

  const infoNode = (
    <span className={classNames.info}>
      {labels.info({ page, totalPages: resolvedTotalPages, total, pageSize })}
      {hints?.info && classNames.infoHelp ? (
        <HelpTooltip
          content={hints.info}
          ariaLabel="Ajuda: paginação"
          className={classNames.infoHelp}
        />
      ) : null}
    </span>
  );

  function renderNavButton(
    label: string,
    disabled: boolean,
    onClick: () => void,
    hint?: string,
    hintAriaLabel?: string,
  ) {
    const button = (
      <button type="button" className={classNames.ghostBtn} disabled={disabled} onClick={onClick}>
        {label}
      </button>
    );

    if (hint && classNames.action && classNames.actionHelp) {
      return (
        <div className={classNames.action}>
          {button}
          <HelpTooltip
            content={hint}
            ariaLabel={hintAriaLabel ?? `Ajuda: ${label.toLowerCase()}`}
            className={classNames.actionHelp}
          />
        </div>
      );
    }

    return button;
  }

  const actionsNode = (
    <div className={classNames.actions}>
      {renderNavButton(
        labels.previous,
        !canPrev,
        () => onPageChange(page - 1),
        hints?.previous,
        "Ajuda: página anterior",
      )}
      {renderNavButton(
        labels.next,
        !canNext,
        () => onPageChange(page + 1),
        hints?.next,
        "Ajuda: próxima página",
      )}
    </div>
  );

  if (layout === "flat") {
    return (
      <div className={classNames.root} role="navigation" aria-label={labels.navigationAriaLabel}>
        {infoNode}
        {actionsNode}
      </div>
    );
  }

  return (
    <div className={classNames.root} role="navigation" aria-label={labels.navigationAriaLabel}>
      <div className={classNames.left}>
        {infoNode}
        {showPageSize ? (
          <label className={classNames.pageSize}>
            <span>{labels.pageSizeLabel}</span>
            <ToolbarSelectControl
              value={String(pageSize)}
              disabled={disabled}
              onChange={(value) => onPageSizeChange?.(Number(value))}
              options={pageSizeSelectOptions}
              allowEmpty={false}
              searchable={false}
              ariaLabel={labels.pageSizeLabel ?? "Itens por página"}
            />
          </label>
        ) : null}
      </div>
      {actionsNode}
    </div>
  );
}

export type DashboardCompactPaginationProps = Omit<
  CompactPaginationProps,
  "classNames" | "labels" | "layout" | "hints"
>;

export function createCompactPagination(config: {
  prefix: string;
  labels: CompactPaginationLabels;
  hints?: CompactPaginationHints;
  ghostBtnModifier?: string;
  ghostBtn?: string;
  withHints?: boolean;
  layout?: CompactPaginationLayout;
}) {
  const classNames = compactPaginationBemClasses(config.prefix, {
    ghostBtnModifier: config.ghostBtnModifier,
    ghostBtn: config.ghostBtn,
    withHints: config.withHints,
  });

  return function DashboardCompactPagination(props: DashboardCompactPaginationProps) {
    return (
      <CompactPagination
        classNames={classNames}
        labels={config.labels}
        hints={config.hints}
        layout={config.layout}
        {...props}
      />
    );
  };
}
