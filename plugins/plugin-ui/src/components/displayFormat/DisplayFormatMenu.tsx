import {
  displayFormatMenuItems,
  specFromPresetId,
  type DisplayFormatSpec,
} from "../../displayFormat";
import { DEFAULT_DISPLAY_FORMAT_CN } from "./displayFormatClasses";

export type DisplayFormatMenuProps = {
  spec: DisplayFormatSpec;
  onSelect: (spec: DisplayFormatSpec) => void;
  onMore: () => void;
  className?: string;
};

export function DisplayFormatMenu({ spec, onSelect, onMore, className }: DisplayFormatMenuProps) {
  const cn = DEFAULT_DISPLAY_FORMAT_CN;
  const items = displayFormatMenuItems();
  return (
    <div className={[cn.menu, className].filter(Boolean).join(" ")} role="listbox" aria-label="Categorias de formato">
      {items.map((item) => {
        const active =
          spec.presetId === item.presetId ||
          (spec.category === item.category && !spec.presetId && item.presetId === item.category);
        return (
          <button
            key={item.id}
            type="button"
            role="option"
            aria-selected={active}
            className={[cn.menuItem, active ? cn.menuItemActive : ""].filter(Boolean).join(" ")}
            onClick={() => onSelect(specFromPresetId(item.presetId))}
          >
            <span>{item.label}</span>
            {item.description ? <span className={cn.menuDesc}>{item.description}</span> : null}
          </button>
        );
      })}
      <button type="button" className={cn.menuMore} onClick={onMore}>
        Mais formatos de número…
      </button>
    </div>
  );
}
