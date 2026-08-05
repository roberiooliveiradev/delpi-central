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
  export const SelectField: ComponentType<LooseProps>;
  export const MultiSelectField: ComponentType<LooseProps>;
  export const TextField: ComponentType<LooseProps>;
  export const TextAreaField: ComponentType<LooseProps>;
  export const DetailFieldGrid: ComponentType<LooseProps>;
  export const InitialsAvatar: ComponentType<LooseProps>;
  export const FiltersRow: ComponentType<LooseProps>;
  export const FilterInputField: ComponentType<LooseProps>;
  export const FilterSelectField: ComponentType<LooseProps>;

  export type DirectoryUserOption = {
    id: string;
    name: string;
    email: string;
  };

  export type UserDirectoryPickerProps = {
    value: DirectoryUserOption[];
    onChange: (users: DirectoryUserOption[]) => void;
    searchUsers: (
      query: string,
      limit?: number,
      signal?: AbortSignal,
    ) => Promise<DirectoryUserOption[]>;
    disabled?: boolean;
    showSelectedList?: boolean;
    showEmail?: boolean;
    maxSelected?: number;
    labels?: {
      title?: string;
      hint?: string;
      placeholder?: string;
    };
    className?: string;
  };

  export const UserDirectoryPicker: ComponentType<UserDirectoryPickerProps>;

  export type DetailField = {
    label: string;
    hint?: string;
    value: ReactNode;
    wide?: boolean;
  };

  export function pageHeaderBrandBemClasses(prefix: string): Record<string, string>;
  export function navigationCardBemClasses(prefix: string): Record<string, string>;
  export function sectionCardPacBemClasses(prefix: string): Record<string, string>;
  export function dataTableBemClasses(prefix: string): Record<string, string>;
  export function emptyStateCardBemClasses(prefix: string): Record<string, unknown>;
  export function loadingActivityBemClasses(prefix: string): Record<string, unknown>;
  export function stateBannerBemClasses(prefix: string): Record<string, string>;
  export function statusBadgeBemClasses(prefix: string): Record<string, string>;
  export function selectControlBemClasses(prefix: string): Record<string, unknown>;
  export function selectFieldPacClasses(prefix: string): Record<string, unknown>;
  export function multiSelectBemClasses(prefix: string): Record<string, unknown>;
  export function textFieldBemClasses(prefix: string): Record<string, unknown>;
  export function textAreaFieldBemClasses(prefix: string): Record<string, unknown>;
  export function detailFieldGridBemClasses(prefix: string): Record<string, unknown>;
  export function initialsAvatarBemClasses(prefix: string): Record<string, unknown>;
  export function filtersRowBemClasses(prefix: string): Record<string, unknown>;

  export function createDashboardLoadingActivityCard(
    config: Record<string, unknown>,
  ): ComponentType<LooseProps>;
  export function createDashboardSelectField(
    config: Record<string, unknown>,
  ): ComponentType<LooseProps>;
  export function createDashboardMultiSelectField(
    config: Record<string, unknown>,
  ): ComponentType<LooseProps>;
  export function createDashboardTextField(
    config: Record<string, unknown>,
  ): ComponentType<LooseProps>;
  export function createDashboardTextAreaField(
    config: Record<string, unknown>,
  ): ComponentType<LooseProps>;
  export function createDashboardDetailFieldGrid(
    config: Record<string, unknown>,
  ): ComponentType<LooseProps>;
  export function createInitialsAvatar(prefix: string): ComponentType<LooseProps>;
  export function createDashboardFiltersKit(config: Record<string, unknown>): {
    FiltersRow: ComponentType<LooseProps>;
    FilterInputField: ComponentType<LooseProps>;
    FilterSelectField: ComponentType<LooseProps>;
  };

  export type DataTableColumn<T> = {
    key: string;
    header: string;
    render: (row: T) => ReactNode;
    align?: "left" | "right" | "center";
  };

  export type TableExportColumn = {
    key: string;
    label: string;
  };

  export type TableExportPayload = {
    title: string;
    columns: TableExportColumn[];
    rows: Array<Record<string, unknown>>;
  };

  export function exportPayloadToCsv(payload: TableExportPayload): void;
}

declare module "@delpi/plugin-ui/styles";

declare module "@delpi/plugin-ui" {
  export * from "@delpi/plugin-ui/index";
}
