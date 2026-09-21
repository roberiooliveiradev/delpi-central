import { type ComponentProps } from "react";
import {
  createDashboardDataRecordCard,
  createDashboardEmptyState,
  createDashboardFormActions,
  createDashboardLoadingState,
  createDashboardMessageThread,
  createDashboardPageHeader,
  createDashboardSectionCard,
  createDashboardSelectField,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTextAreaField,
  createDashboardTextField,
  emptyStateCardBemClasses,
  formActionsBemClasses,
  loadingStateCardBemClasses,
  pageHeaderTitleRowBemClasses,
  sectionCardPacBemClasses,
  selectFieldPacClasses,
  stateBannerBemClasses,
  textAreaFieldBemClasses,
  textFieldPacClasses,
} from "@delpi/plugin-ui/index";

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
  props: Omit<ComponentProps<typeof HelpdeskMessageThreadView>, "bodyMode" | "showMineIdentity">,
) {
  return <HelpdeskMessageThreadView {...props} bodyMode="plain" showMineIdentity />;
}

export const HelpdeskStatusBadge = createDashboardStatusBadge({ prefix: PREFIX });

export const HelpdeskRecordCard = createDashboardDataRecordCard({ prefix: PREFIX });

export const HelpdeskTextField = createDashboardTextField({
  classNames: textFieldPacClasses(PREFIX),
});

export const HelpdeskTextArea = createDashboardTextAreaField({
  classNames: textAreaFieldBemClasses(PREFIX),
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
