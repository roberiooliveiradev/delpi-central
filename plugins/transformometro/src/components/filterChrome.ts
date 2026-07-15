import {
  delpiUiClass,
  filterBoxBemClasses,
  filtersRowBemClasses,
} from "@delpi/plugin-ui/index";

const FILTERS = filtersRowBemClasses("ds");

/** Linha de filtros dual `ds-filters-row` + `.delpi-ui-filters-row`. */
export const DS_FILTERS_ROW = FILTERS.row;

/** Variante extended (grid mais denso). */
export const DS_FILTERS_ROW_EXTENDED = FILTERS.rowExtended;

/** Campo de filtro dual (inclui `ds-field`). */
export const DS_FILTER_BOX = FILTERS.filterBox;

/** Shell sem `ds-field` — formulários / checkbox. */
export const DS_FILTER_BOX_PLAIN = filterBoxBemClasses("ds");

export const DS_FILTER_BOX_WIDE = filterBoxBemClasses("ds", "wide");

export const DS_FILTER_BOX_CHECKBOX = filterBoxBemClasses("ds", "checkbox");

/** Só o modificador `--wide` (quando o root já tem filter-box). */
export const DS_FILTER_BOX_WIDE_MOD = delpiUiClass(
  "ds-filter-box--wide",
  "delpi-ui-filter-box--wide",
);
