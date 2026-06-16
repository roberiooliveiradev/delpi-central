import { renderToStaticMarkup } from "react-dom/server";
import { Pencil } from "lucide-react";
import { describe, expect, it } from "vitest";

import { DropdownMenuTrigger } from "./DropdownMenuTrigger";

describe("DropdownMenuTrigger", () => {
  it("renderiza gatilho com menu de ações", () => {
    const html = renderToStaticMarkup(
      <DropdownMenuTrigger
        items={[
          {
            id: "rename",
            label: "Renomear",
            icon: <Pencil size={17} aria-hidden="true" />,
            onSelect: () => undefined,
          },
        ]}
        menuLabel="Opções do item"
        ariaLabel="Abrir opções"
      />,
    );

    expect(html).toContain("mdc-dropdown-menu-trigger__button");
    expect(html).toContain('aria-haspopup="menu"');
    expect(html).toContain('aria-expanded="false"');
    expect(html).toContain('aria-label="Abrir opções"');
  });
});
