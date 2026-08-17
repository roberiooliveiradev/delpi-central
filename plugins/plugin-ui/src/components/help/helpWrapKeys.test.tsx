import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DataTable, dataTableBemClasses } from "../data/DataTable";
import { FieldLabel } from "./FieldLabel";
import { HelpTooltip } from "./HelpTooltip";
import { SectionHintLabel } from "./SectionHintLabel";
import { SectionCard, sectionCardPacBemClasses } from "../layout/SectionCard";
import { SegmentToggle, segmentToggleBemClasses } from "../forms/SegmentToggle";

afterEach(() => {
  cleanup();
});

function keyWarnings(spy: ReturnType<typeof vi.spyOn>) {
  return spy.mock.calls.filter((c) => {
    const msg = String(c[0] ?? "");
    return msg.includes("unique") && msg.includes("key");
  });
}

describe("help wrap key warnings", () => {
  it("SectionCard com hint no título", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <SectionCard
        title="Pedidos em aberto"
        hint="ajuda"
        classNames={sectionCardPacBemClasses("cm")}
        labels={{ titleHelpAriaLabel: (t) => `Ajuda: ${t}` }}
      >
        <div>body</div>
      </SectionCard>,
    );
    expect(keyWarnings(spy)).toEqual([]);
    spy.mockRestore();
  });

  it("DataTable com headerHint + sort", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <DataTable
        rows={[{ id: "1", name: "x" }]}
        rowKey={(r) => r.id}
        classNames={dataTableBemClasses("cm")}
        labels={{
          emptyMessage: "vazio",
          headerHelpAriaLabel: (h) => `Ajuda ${h}`,
          sortByAriaLabel: (h) => `Ordenar ${h}`,
        }}
        columns={[
          {
            key: "name",
            header: "Nome",
            headerHint: "ajuda nome",
            sortable: true,
            render: (r) => r.name,
          },
          { key: "id", header: "Id", headerHint: "ajuda id", render: (r) => r.id },
        ]}
        onSortChange={() => {}}
        sortKey="name"
        sortDirection="asc"
      />,
    );
    expect(keyWarnings(spy)).toEqual([]);
    spy.mockRestore();
  });

  it("HelpTooltip wrap em SegmentToggle", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { container } = render(
      <HelpTooltip content="ajuda layout" wrap>
        <SegmentToggle
          classNames={segmentToggleBemClasses("cm")}
          ariaLabel="Modo"
          idPrefix="layout"
          value="table"
          onChange={() => {}}
          options={[
            { value: "table", label: "Tabela" },
            { value: "cards", label: "Cards" },
          ]}
        />
      </HelpTooltip>,
    );
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-help-tooltip")!);
    expect(keyWarnings(spy)).toEqual([]);
    spy.mockRestore();
  });

  it("lista de FieldLabel", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <div>
        {["Cliente", "Pedido", "Produto"].map((label) => (
          <FieldLabel key={label} label={label} hint={`Ajuda ${label}`} />
        ))}
      </div>,
    );
    expect(keyWarnings(spy)).toEqual([]);
    spy.mockRestore();
  });

  it("SectionHintLabel", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(<SectionHintLabel label="Pedidos em aberto" hint="ajuda" />);
    expect(keyWarnings(spy)).toEqual([]);
    spy.mockRestore();
  });
});
