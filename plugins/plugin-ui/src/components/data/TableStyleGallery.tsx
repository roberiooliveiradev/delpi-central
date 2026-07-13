import { Table2 } from "lucide-react";
import { useRef, useState, type CSSProperties } from "react";

import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { useClickOutside } from "../shape/useClickOutside";

export type TableStylePresetCategory = "light" | "medium" | "dark" | string;

/** Thumb visual da galeria — o host mapeia a options/preset do domínio. */
export type TableStylePreset = {
  id: string;
  label: string;
  category: TableStylePresetCategory;
  headerBg: string;
  cellBg: string;
  borderColor: string;
};

export type TableStyleGalleryLabels = {
  light?: string;
  medium?: string;
  dark?: string;
  clear?: string;
  more?: string;
  galleryAria?: string;
  stripAria?: string;
};

const DEFAULT_LABELS: Required<TableStyleGalleryLabels> = {
  light: "Claros",
  medium: "Médios",
  dark: "Escuros",
  clear: "Limpar tabela",
  more: "Mais",
  galleryAria: "Galeria de estilos de tabela",
  stripAria: "Estilos de tabela",
};

function mergeLabels(labels?: TableStyleGalleryLabels): Required<TableStyleGalleryLabels> {
  return { ...DEFAULT_LABELS, ...labels };
}

function thumbStyle(preset: TableStylePreset): CSSProperties {
  return {
    ["--delpi-ui-table-thumb-header" as string]: preset.headerBg,
    ["--delpi-ui-table-thumb-cell" as string]: preset.cellBg,
    ["--delpi-ui-table-thumb-border" as string]: preset.borderColor,
  };
}

function categoryHeading(
  category: TableStylePresetCategory,
  L: Required<TableStyleGalleryLabels>,
): string {
  if (category === "light") return L.light;
  if (category === "medium") return L.medium;
  if (category === "dark") return L.dark;
  return String(category);
}

export type TableStyleGalleryProps = {
  presets: TableStylePreset[];
  selectedId?: string;
  onSelect: (preset: TableStylePreset) => void;
  onClear?: () => void;
  labels?: TableStyleGalleryLabels;
};

export function TableStyleGallery({
  presets,
  selectedId,
  onSelect,
  onClear,
  labels,
}: TableStyleGalleryProps) {
  const L = mergeLabels(labels);
  const categories = Array.from(new Set(presets.map((preset) => preset.category)));

  return (
    <div className="delpi-ui-table-style-gallery" role="menu" aria-label={L.galleryAria}>
      {categories.map((category) => {
        const items = presets.filter((preset) => preset.category === category);
        if (items.length === 0) return null;
        return (
          <section key={String(category)} className="delpi-ui-table-style-gallery__section">
            <h4 className="delpi-ui-table-style-gallery__heading">
              {categoryHeading(category, L)}
            </h4>
            <div className="delpi-ui-table-style-gallery__grid" role="list">
              {items.map((preset) => {
                const active = selectedId === preset.id;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    role="listitem"
                    className={[
                      "delpi-ui-table-style-gallery__item",
                      active ? "delpi-ui-table-style-gallery__item--active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    aria-label={preset.label}
                    aria-pressed={active}
                    title={preset.label}
                    onClick={() => onSelect(preset)}
                    style={thumbStyle(preset)}
                  >
                    <span className="delpi-ui-table-style-gallery__preview" aria-hidden="true" />
                  </button>
                );
              })}
            </div>
          </section>
        );
      })}
      {onClear ? (
        <button
          type="button"
          className="delpi-ui-table-style-gallery__clear"
          onClick={onClear}
        >
          {L.clear}
        </button>
      ) : null}
    </div>
  );
}

export type TableStyleMenuProps = TableStyleGalleryProps & {
  triggerLabel?: string;
};

/** Gatilho «Mais» com galeria completa em portal (evita clip por overflow da ribbon). */
export function TableStyleMenu({
  triggerLabel,
  labels,
  onSelect,
  ...galleryProps
}: TableStyleMenuProps) {
  const L = mergeLabels(labels);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  useClickOutside([rootRef, panelRef], open, () => setOpen(false));

  return (
    <div className="delpi-ui-shape-menu" ref={rootRef}>
      <button
        type="button"
        className="delpi-ui-shape-menu__trigger"
        aria-label={L.galleryAria}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="delpi-ui-shape-menu__trigger-icon" aria-hidden="true">
          <Table2 size={18} />
        </span>
        <span className="delpi-ui-shape-menu__trigger-label">{triggerLabel ?? L.more}</span>
      </button>
      {open ? (
        <AnchoredPanelPortal open={open} anchorRef={rootRef} panelRef={panelRef} role="menu">
          <TableStyleGallery
            {...galleryProps}
            labels={labels}
            onSelect={(preset) => {
              onSelect(preset);
              setOpen(false);
            }}
            onClear={
              galleryProps.onClear
                ? () => {
                    galleryProps.onClear?.();
                    setOpen(false);
                  }
                : undefined
            }
          />
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}

export type TableStyleRibbonStripProps = TableStyleMenuProps & {
  maxVisible?: number;
};

/** Faixa horizontal na ribbon (thumbs + Mais → galeria completa). */
export function TableStyleRibbonStrip({
  presets,
  selectedId,
  onSelect,
  onClear,
  labels,
  maxVisible = 7,
  triggerLabel,
}: TableStyleRibbonStripProps) {
  const L = mergeLabels(labels);
  const visible = presets.slice(0, Math.max(1, maxVisible));

  return (
    <div className="delpi-ui-table-style-strip" role="list" aria-label={L.stripAria}>
      {visible.map((preset) => {
        const active = selectedId === preset.id;
        return (
          <button
            key={preset.id}
            type="button"
            role="listitem"
            className={[
              "delpi-ui-table-style-strip__thumb",
              active ? "delpi-ui-table-style-strip__thumb--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-label={preset.label}
            aria-pressed={active}
            title={preset.label}
            onClick={() => onSelect(preset)}
            style={thumbStyle(preset)}
          >
            <span className="delpi-ui-table-style-strip__preview" aria-hidden="true" />
          </button>
        );
      })}
      <TableStyleMenu
        presets={presets}
        selectedId={selectedId}
        onSelect={onSelect}
        onClear={onClear}
        labels={labels}
        triggerLabel={triggerLabel ?? L.more}
      />
    </div>
  );
}
