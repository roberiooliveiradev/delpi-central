import { createDashboardFormGrid } from "@delpi/plugin-ui/index";

export const FormGrid = createDashboardFormGrid({
  classNames: { root: "kz-form-grid" },
});

export const ReadOnlyGrid = createDashboardFormGrid({
  classNames: { root: "kz-read-grid" },
});
