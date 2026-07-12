import type { ReactNode } from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";
import {
  bindTablePartPointer,
  getTablePartState,
  type TableInteraction,
  type TablePartsMap,
} from "../configurableTableParts";

export type TableHeaderCellProps = {
  children: ReactNode;
  colIndex?: number;
  interaction?: TableInteraction | null;
};

export function TableHeaderCell({ children, colIndex = 0, interaction }: TableHeaderCellProps) {
  const cn = useConfigurableTableClasses();
  const ref = { kind: "headerCell" as const, colIndex };
  const { selected, onPointerDown, onDoubleClick, editing: _e, ...dom } = bindTablePartPointer(
    ref,
    interaction,
  );
  return (
    <th
      className={[cn.headerCell, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {children}
    </th>
  );
}

export type TableHeaderProps = {
  visible?: boolean;
  children: ReactNode;
  interaction?: TableInteraction | null;
  tableParts?: TablePartsMap | null;
};

export function TableHeader({
  visible = true,
  children,
  interaction,
  tableParts,
}: TableHeaderProps) {
  const cn = useConfigurableTableClasses();
  const ref = { kind: "header" as const };
  const partVisible = getTablePartState(tableParts, ref)?.visible !== false;
  if (!visible || !partVisible) return null;

  const { selected, onPointerDown, onDoubleClick, editing: _e, ...dom } = bindTablePartPointer(
    ref,
    interaction,
  );

  return (
    <thead
      className={[cn.header, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      <tr className={`${cn.row} ${cn.rowHeader}`}>{children}</tr>
    </thead>
  );
}
