/**
 * Curated, domain-neutral UI package for reusable tool workspaces.
 * Kept separate from the large plugin-ui index / host-specific apps.
 * All exports are public UI surfaces; no navigation, RBAC or domain logic.
 */
export {
  NavigationCard,
  navigationCardBemClasses,
  type NavigationCardProps,
  type NavigationCardClassNames,
} from "./components/layout/NavigationCard";
export {
  CollapsibleToolRail,
  type ToolRailItem,
  type ToolRailGroup,
  type CollapsibleToolRailProps,
} from "./components/navigation/CollapsibleToolRail";
export { ActionButton, type ActionButtonProps } from "./components/actions/ActionButton";
export { IconButton, type IconButtonProps } from "./components/actions/IconButton";
export { NativeTextControl, type NativeTextControlProps } from "./components/forms/NativeTextControl";
export { NATIVE_CONTROL_COMPACT_CLASS } from "./components/forms/nativeControlClasses";
export { ModernSelectControl } from "./components/forms/FormSelectControl";
export { NumberStepperControl, type NumberStepperControlProps } from "./components/forms/NumberStepperControl";
export { SegmentToggle, type SegmentToggleProps } from "./components/forms/SegmentToggle";
export { DataTable, dataTableBemClasses, type DataTableColumn } from "./components/data/DataTable";
export { SectionCard, sectionCardKaizenBemClasses } from "./components/layout/SectionCard";
export { SimpleKpiCard, simpleKpiCardBemClasses } from "./components/layout/SimpleKpiCard";
export { StateBox } from "./components/feedback/StateBox";
export { StatusBadge, statusBadgeBemClasses } from "./components/feedback/StatusBadge";
export { StackedColumnChart, type StackedColumnChartProps } from "./components/charts/StackedColumnChart";
