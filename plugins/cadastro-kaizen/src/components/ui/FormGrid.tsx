import { createDashboardFormGrid } from "@delpi/plugin-ui";

export const FormGrid = createDashboardFormGrid({
  classNames: { root: "kz-form-grid" },
});

export const ReadOnlyGrid = createDashboardFormGrid({
  classNames: { root: "kz-read-grid" },
});
