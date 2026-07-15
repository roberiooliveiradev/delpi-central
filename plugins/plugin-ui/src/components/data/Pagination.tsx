import { useEffect, useId, useState, type ReactElement } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import {
  buildVisiblePageItems,
  parsePageJumpInput,
  TABLE_PAGE_SIZE_OPTIONS,
  type PageJumpValidationReason,
} from "../../utils/paginationPages";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type TablePageSizeClassNames = {
  root: string;
  label: string;
  select: string;
  help?: string;
};

export type TablePageSizeLabels = {
  label: string;
  selectAriaLabel: string;
};

export type TablePageSizeSelectProps = {
  pageSize: number;
  pageSizeOptions?: readonly number[];
  onPageSizeChange: (pageSize: number) => void;
  classNames: TablePageSizeClassNames;
  labels: TablePageSizeLabels;
  pageSizeHint?: string;
};

export function TablePageSizeSelect({
  pageSize,
  pageSizeOptions = TABLE_PAGE_SIZE_OPTIONS,
  onPageSizeChange,
  classNames,
  labels,
  pageSizeHint,
}: TablePageSizeSelectProps) {
  return (
    <label className={classNames.root}>
      <span className={classNames.label}>{labels.label}</span>
      <select
        className={classNames.select}
        value={pageSize}
        onChange={(event) => onPageSizeChange(Number(event.target.value))}
        aria-label={labels.selectAriaLabel}
      >
        {pageSizeOptions.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      {pageSizeHint && classNames.help ? (
        <HelpTooltip
          content={pageSizeHint}
          ariaLabel={`Ajuda: ${labels.label.toLowerCase()}`}
          className={classNames.help}
        />
      ) : null}
    </label>
  );
}

export type PaginationClassNames = {
  root: string;
  controls: string;
  action: string;
  actionHelp?: string;
  ghostBtn: string;
  pages: string;
  ellipsis: string;
  page: string;
  pageActive: string;
  jump: string;
  jumpField: string;
  jumpLabel: string;
  jumpInput: string;
  jumpInputInvalid: string;
  jumpHelp?: string;
  jumpError: string;
  info: string;
  infoHelp?: string;
};

export type PaginationHints = {
  previous?: string;
  next?: string;
  info?: string;
  jump?: string;
};

export type PaginationLabels = {
  navigationAriaLabel: string;
  pagesAriaLabel: string;
  previous: string;
  next: string;
  info: (args: {
    rangeStart: number;
    rangeEnd: number;
    total: number;
    page: number;
    totalPages: number;
  }) => string;
  jumpLabel: string;
  jumpInputAriaLabel: string;
  jumpError: (reason: PageJumpValidationReason, totalPages: number) => string;
};

export type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  classNames: PaginationClassNames;
  labels: PaginationLabels;
  hints?: PaginationHints;
};

function PaginationPageJump({
  page,
  totalPages,
  onPageChange,
  classNames,
  labels,
  jumpHint,
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  classNames: PaginationClassNames;
  labels: PaginationLabels;
  jumpHint?: string;
}) {
  const inputId = useId();
  const errorId = `${inputId}-error`;
  const [draft, setDraft] = useState(String(page));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(String(page));
    setError(null);
  }, [page]);

  const commitJump = () => {
    const result = parsePageJumpInput(draft, totalPages);

    if (result.ok === false) {
      setError(labels.jumpError(result.reason, totalPages));
      return;
    }

    setError(null);
    setDraft(String(result.page));

    if (result.page !== page) {
      onPageChange(result.page);
    }
  };

  return (
    <div className={classNames.jump}>
      <label className={classNames.jumpField} htmlFor={inputId}>
        <span className={classNames.jumpLabel}>{labels.jumpLabel}</span>
        <input
          id={inputId}
          className={error ? classNames.jumpInputInvalid : classNames.jumpInput}
          type="text"
          inputMode="numeric"
          autoComplete="off"
          value={draft}
          aria-label={labels.jumpInputAriaLabel}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          onChange={(event) => {
            setDraft(event.target.value);
            if (error) {
              setError(null);
            }
          }}
          onBlur={commitJump}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              commitJump();
            }
          }}
        />
      </label>
      {jumpHint && classNames.jumpHelp ? (
        <HelpTooltip
          content={jumpHint}
          ariaLabel={`Ajuda: ${labels.jumpLabel.toLowerCase()}`}
          className={classNames.jumpHelp}
        />
      ) : null}
      {error ? (
        <span id={errorId} className={classNames.jumpError} role="alert">
          {error}
        </span>
      ) : null}
    </div>
  );
}

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
  classNames,
  labels,
  hints,
}: PaginationProps) {
  const totalPages = pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1;
  const canPrev = page > 1;
  const canNext = page < totalPages;
  const pageItems = buildVisiblePageItems(page, totalPages);
  const rangeStart = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const rangeEnd = Math.min(page * pageSize, total);

  if (total === 0) return null;

  return (
    <div className={classNames.root} role="navigation" aria-label={labels.navigationAriaLabel}>
      <div className={classNames.controls}>
        <div className={classNames.action}>
          <button
            type="button"
            className={classNames.ghostBtn}
            disabled={!canPrev}
            onClick={() => onPageChange(page - 1)}
            aria-disabled={!canPrev}
          >
            {labels.previous}
          </button>
          {hints?.previous && classNames.actionHelp ? (
            <HelpTooltip
              content={hints.previous}
              ariaLabel={`Ajuda: ${labels.previous.toLowerCase()}`}
              className={classNames.actionHelp}
            />
          ) : null}
        </div>

        {totalPages > 1 ? (
          <div className={classNames.pages} role="group" aria-label={labels.pagesAriaLabel}>
            {pageItems.map((item, index) =>
              item === "ellipsis" ? (
                <span key={`ellipsis-${index}`} className={classNames.ellipsis} aria-hidden="true">
                  …
                </span>
              ) : (
                <button
                  key={item}
                  type="button"
                  className={item === page ? classNames.pageActive : classNames.page}
                  aria-current={item === page ? "page" : undefined}
                  onClick={() => onPageChange(item)}
                >
                  {item}
                </button>
              ),
            )}
          </div>
        ) : null}

        {totalPages > 1 ? (
          <PaginationPageJump
            page={page}
            totalPages={totalPages}
            onPageChange={onPageChange}
            classNames={classNames}
            labels={labels}
            jumpHint={hints?.jump}
          />
        ) : null}

        <div className={classNames.action}>
          <button
            type="button"
            className={classNames.ghostBtn}
            disabled={!canNext}
            onClick={() => onPageChange(page + 1)}
            aria-disabled={!canNext}
          >
            {labels.next}
          </button>
          {hints?.next && classNames.actionHelp ? (
            <HelpTooltip
              content={hints.next}
              ariaLabel={`Ajuda: ${labels.next.toLowerCase()}`}
              className={classNames.actionHelp}
            />
          ) : null}
        </div>
      </div>

      <span className={classNames.info}>
        {labels.info({ rangeStart, rangeEnd, total, page, totalPages })}
        {hints?.info && classNames.infoHelp ? (
          <HelpTooltip
            content={hints.info}
            ariaLabel="Ajuda: paginação"
            className={classNames.infoHelp}
          />
        ) : null}
      </span>
    </div>
  );
}

export function paginationBemClasses(prefix: string) {
  const base = `${prefix}-pagination`;
  const ui = "delpi-ui-pagination";
  const pageSize = `${prefix}-table-page-size`;
  const uiPageSize = "delpi-ui-table-page-size";
  return {
    pagination: {
      root: delpiUiClass(base, ui),
      controls: delpiUiClass(`${base}__controls`, `${ui}__controls`),
      action: delpiUiClass(`${base}__action`, `${ui}__action`),
      actionHelp: delpiUiClass(`${base}__action-help`, `${ui}__action-help`),
      ghostBtn: delpiUiClass(`${prefix}-ghost-btn`, "delpi-ui-ghost-btn"),
      pages: delpiUiClass(`${base}__pages`, `${ui}__pages`),
      ellipsis: delpiUiClass(`${base}__ellipsis`, `${ui}__ellipsis`),
      page: delpiUiClass(`${base}__page`, `${ui}__page`),
      pageActive: delpiUiClass(
        `${base}__page ${base}__page--active`,
        `${ui}__page ${ui}__page--active`,
      ),
      jump: delpiUiClass(`${base}__jump`, `${ui}__jump`),
      jumpField: delpiUiClass(`${base}__jump-field`, `${ui}__jump-field`),
      jumpLabel: delpiUiClass(`${base}__jump-label`, `${ui}__jump-label`),
      jumpInput: delpiUiClass(`${base}__jump-input`, `${ui}__jump-input`),
      jumpInputInvalid: delpiUiClass(
        `${base}__jump-input ${base}__jump-input--invalid`,
        `${ui}__jump-input ${ui}__jump-input--invalid`,
      ),
      jumpHelp: delpiUiClass(`${base}__jump-help`, `${ui}__jump-help`),
      jumpError: delpiUiClass(`${base}__jump-error`, `${ui}__jump-error`),
      info: delpiUiClass(`${base}__info`, `${ui}__info`),
      infoHelp: delpiUiClass(`${base}__help`, `${ui}__help`),
    } satisfies PaginationClassNames,
    tablePageSize: {
      root: delpiUiClass(pageSize, uiPageSize),
      label: delpiUiClass(`${pageSize}__label`, `${uiPageSize}__label`),
      select: delpiUiClass(`${pageSize}__select`, `${uiPageSize}__select`),
      help: delpiUiClass(`${pageSize}__help`, `${uiPageSize}__help`),
    } satisfies TablePageSizeClassNames,
  };
}

export type DashboardPaginationKit = {
  Pagination: (props: Omit<PaginationProps, "classNames" | "labels" | "hints">) => ReactElement;
  TablePageSizeSelect: (
    props: Omit<TablePageSizeSelectProps, "classNames" | "labels" | "pageSizeHint">,
  ) => ReactElement;
};

export function createDashboardPaginationKit(config: {
  prefix: string;
  labels: PaginationLabels;
  tablePageSizeLabels: TablePageSizeLabels;
  hints?: PaginationHints & { pageSize?: string };
}): DashboardPaginationKit {
  const classNames = paginationBemClasses(config.prefix);

  return {
    Pagination(props) {
      return (
        <Pagination classNames={classNames.pagination} labels={config.labels} hints={config.hints} {...props} />
      );
    },
    TablePageSizeSelect(props) {
      return (
        <TablePageSizeSelect
          classNames={classNames.tablePageSize}
          labels={config.tablePageSizeLabels}
          pageSizeHint={config.hints?.pageSize}
          {...props}
        />
      );
    },
  };
}
