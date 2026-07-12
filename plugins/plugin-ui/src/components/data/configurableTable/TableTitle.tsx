import type { CSSProperties } from "react";

import { useConfigurableTableClasses } from "../configurableTableClasses";
import {
  bindTablePartPointer,
  getTablePartState,
  resolveTablePartPaintStyle,
  type TableInteraction,
  type TablePartsMap,
} from "../configurableTableParts";

export type TableTitleProps = {
  title?: string;
  visible?: boolean;
  interaction?: TableInteraction | null;
  tableParts?: TablePartsMap | null;
};

export function TableTitle({
  title,
  visible = true,
  interaction,
  tableParts,
}: TableTitleProps) {
  const cn = useConfigurableTableClasses();
  const ref = { kind: "title" as const };
  const partVisible = getTablePartState(tableParts, ref)?.visible !== false;
  if (!visible || !partVisible) return null;
  const display = getTablePartState(tableParts, ref)?.content?.trim() || title?.trim();
  if (!display) return null;

  const { selected, onPointerDown, onDoubleClick, editing: _e, ...dom } = bindTablePartPointer(
    ref,
    interaction,
  );
  const paint = resolveTablePartPaintStyle(tableParts, ref);
  const style: CSSProperties | undefined =
    paint.backgroundColor || paint.color || paint.fontWeight != null
      ? {
          ...(paint.backgroundColor ? { backgroundColor: paint.backgroundColor } : {}),
          ...(paint.color ? { color: paint.color } : {}),
          ...(paint.fontWeight != null ? { fontWeight: paint.fontWeight } : {}),
        }
      : undefined;

  return (
    <div
      className={[cn.title, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      style={style}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {display}
    </div>
  );
}
