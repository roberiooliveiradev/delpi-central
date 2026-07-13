import { CatalogStub } from "../CatalogStub";
import type { CatalogEntry } from "../types";

/** Shape menus dependem de âncora/ribbon — stubs com nota até demos dedicadas. */
export const shapeCatalogEntries: CatalogEntry[] = [
  "ShapeFillMenu",
  "ShapeOutlineMenu",
  "ShapeEffectsMenu",
  "ShapeShadowMenu",
  "ShapeStyleMenu",
  "ShapeStyleGallery",
  "ColorDialog",
  "ColorPickerPopover",
  "RibbonColorPicker",
  "ColorThemeGrid",
  "ColorStandardRow",
  "ColorSwatch",
].map((exportName) => ({
  id: `shape.${exportName}`,
  family: "shape" as const,
  exportName,
  title: exportName,
  description: "Controle de forma/cor do editor (ribbon).",
  demos: [
    {
      id: "stub",
      label: "Stub",
      render: () => (
        <CatalogStub
          name={exportName}
          note="Menus de shape/cor precisam de âncora e estado do editor. Ver TV dashboard."
        />
      ),
    },
  ],
}));
