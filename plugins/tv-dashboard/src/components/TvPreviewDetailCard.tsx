import {
  createDashboardPreviewDetailCard,
  previewDetailCardBemClasses,
} from "@delpi/plugin-ui/index";

/** Card capa+detalhe da home / biblioteca — CSS no plugin-ui. */
export const TvPreviewDetailCard = createDashboardPreviewDetailCard({
  classNames: previewDetailCardBemClasses("td"),
});
