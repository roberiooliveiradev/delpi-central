import { useConfigurableTableClasses } from "../configurableTableClasses";
import {
  bindTablePartPointer,
  getTablePartState,
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

  return (
    <div
      className={[cn.title, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {display}
    </div>
  );
}
