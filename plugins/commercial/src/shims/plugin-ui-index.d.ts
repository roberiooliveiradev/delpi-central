declare module "@delpi/plugin-ui/index" {
  import type { ComponentType, ReactNode } from "react";

  type LooseProps = Record<string, unknown>;

  export const ActionButton: ComponentType<LooseProps>;
  export const BackLink: ComponentType<LooseProps>;
  export const DataTable: ComponentType<LooseProps>;
  export const EmptyState: ComponentType<LooseProps>;
  export const LoadingActivityCard: ComponentType<LooseProps>;
  export const NavigationCard: ComponentType<LooseProps>;
  export const PageHeader: ComponentType<LooseProps>;
  export const SectionCard: ComponentType<LooseProps>;
  export const StateBanner: ComponentType<LooseProps>;
  export const StatusBadge: ComponentType<LooseProps>;

  export function pageHeaderBrandBemClasses(prefix: string): Record<string, string>;
  export function navigationCardBemClasses(prefix: string): Record<string, string>;
  export function sectionCardPacBemClasses(prefix: string): Record<string, string>;
  export function dataTableBemClasses(prefix: string): Record<string, string>;
  export function emptyStateCardBemClasses(prefix: string): Record<string, unknown>;
  export function loadingActivityBemClasses(prefix: string): Record<string, unknown>;
  export function stateBannerBemClasses(prefix: string): Record<string, string>;
  export function statusBadgeBemClasses(prefix: string): Record<string, string>;
  export function createDashboardLoadingActivityCard(
    config: Record<string, unknown>,
  ): ComponentType<LooseProps>;

  export type DataTableColumn<T> = {
    key: string;
    header: string;
    render: (row: T) => ReactNode;
    align?: "left" | "right" | "center";
  };
}

declare module "@delpi/plugin-ui/styles";

declare module "@delpi/plugin-ui" {
  export * from "@delpi/plugin-ui/index";
}
