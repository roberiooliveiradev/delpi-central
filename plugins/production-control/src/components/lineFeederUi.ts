import { createDashboardMultiSelectField } from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";

const texts = copy.lineFeeder.collectModal;

/** Multiseleção de postos — kit compartilhado, escopo do Production Control. */
export const LineFeederWorkCenterMultiSelect = createDashboardMultiSelectField({
  prefix: "ppc",
  portalScopeClassName: "dashboard-production-control",
  labels: {
    emptyLabel: texts.workCentersEmptyLabel,
    searchPlaceholder: texts.workCentersSearch,
    selectVisible: texts.selectAllVisible,
    clear: texts.clearSelection,
    emptyOptions: texts.workCentersNoOptions,
    multipleSelected: (count) => texts.selectedCount(count),
    searchAriaLabel: (label) => texts.searchAria(label),
    selectedCountLabel: (count) => texts.selectedCount(count),
    removeTagAriaLabel: (value) => texts.removeTagAria(value),
  },
});
