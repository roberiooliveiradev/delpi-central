import type { ComponentProps } from "react";

import {
  MaintenanceLoadingCard,
  MaintenanceScreenLoading,
} from "../app/maintenanceUi";
import { MAINTENANCE_LOADING_TITLES } from "../content/loadingLabels";

type LoadingTitleKey = keyof typeof MAINTENANCE_LOADING_TITLES;

type MaintenanceTableLoadingProps = {
  titleKey?: LoadingTitleKey;
  title?: string;
  description?: string;
  variant?: ComponentProps<typeof MaintenanceLoadingCard>["variant"];
  sticky?: boolean;
  progressPercent?: number;
};

/** Loading compacto para seção/tabela/chart — usa `MaintenanceLoadingCard` do kit. */
export function MaintenanceTableLoading({
  titleKey = "default",
  title,
  description,
  variant = "compact",
  sticky,
  progressPercent,
}: MaintenanceTableLoadingProps) {
  return (
    <MaintenanceLoadingCard
      title={title ?? MAINTENANCE_LOADING_TITLES[titleKey]}
      description={description ?? "Aguarde enquanto os dados são obtidos."}
      variant={variant}
      sticky={sticky}
      progressPercent={progressPercent}
    />
  );
}

type MaintenanceScreenLoadingStateProps = {
  labelKey?: LoadingTitleKey;
  label?: string;
};

/** Loading de página ou bloco grande — usa `MaintenanceScreenLoading` do kit. */
export function MaintenanceScreenLoadingState({
  labelKey = "default",
  label,
}: MaintenanceScreenLoadingStateProps) {
  return <MaintenanceScreenLoading label={label ?? MAINTENANCE_LOADING_TITLES[labelKey]} />;
}
