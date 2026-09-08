// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EntityDirectoryPicker } from "./EntityDirectoryPicker";

const entities = [
  { id: "p1", label: "ACME Indústria", secondary: "001/01" },
  { id: "p2", label: "Beta Comércio", secondary: "002/01" },
];

const searchEntities = vi.fn().mockResolvedValue([]);

afterEach(cleanup);

describe("EntityDirectoryPicker", () => {
  it("mostra chips dos selecionados com × por padrão", () => {
    render(
      <EntityDirectoryPicker
        value={entities}
        onChange={() => {}}
        searchEntities={searchEntities}
      />,
    );

    expect(screen.getByText("ACME Indústria · 001/01")).toBeTruthy();
    expect(document.querySelectorAll(".delpi-ui-tag-chip")).toHaveLength(2);
    expect(
      screen.getByRole("button", { name: "Remover ACME Indústria · 001/01" }),
    ).toBeTruthy();
  });

  it("com maxSelected=1 substitui a seleção ao escolher outro", async () => {
    const onChange = vi.fn();
    searchEntities.mockResolvedValueOnce([
      { id: "p3", label: "Carla Dias", secondary: "003/01" },
    ]);

    render(
      <EntityDirectoryPicker
        value={[entities[0]]}
        onChange={onChange}
        searchEntities={searchEntities}
        maxSelected={1}
        labels={{ placeholder: "Buscar entidade" }}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Buscar entidade"), {
      target: { value: "Carla" },
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Carla Dias · 003/01" })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Carla Dias · 003/01" }));
    expect(onChange).toHaveBeenCalledWith([
      { id: "p3", label: "Carla Dias", secondary: "003/01" },
    ]);
  });

  it("permite multi-seleção até maxSelected", async () => {
    const onChange = vi.fn();
    searchEntities.mockResolvedValueOnce([
      { id: "p3", label: "Gamma", secondary: "G1" },
    ]);

    render(
      <EntityDirectoryPicker
        value={[entities[0]]}
        onChange={onChange}
        searchEntities={searchEntities}
        maxSelected={20}
        labels={{ placeholder: "Buscar produto" }}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Buscar produto"), {
      target: { value: "Gam" },
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Gamma · G1" })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Gamma · G1" }));
    expect(onChange).toHaveBeenCalledWith([
      entities[0],
      { id: "p3", label: "Gamma", secondary: "G1" },
    ]);
  });

  it("desabilita novas escolhas quando atLimit e maxSelected>1", async () => {
    searchEntities.mockResolvedValueOnce([
      { id: "p3", label: "Gamma", secondary: "G1" },
    ]);

    render(
      <EntityDirectoryPicker
        value={entities}
        onChange={() => {}}
        searchEntities={searchEntities}
        maxSelected={2}
        labels={{ placeholder: "Buscar produto" }}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Buscar produto"), {
      target: { value: "Gam" },
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Gamma · G1" })).toBeTruthy();
    });

    expect(
      (screen.getByRole("button", { name: "Gamma · G1" }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });

  it("omite da lista quem já está selecionado", async () => {
    searchEntities.mockResolvedValueOnce([
      entities[0],
      { id: "p3", label: "Carla Dias", secondary: "003/01" },
    ]);

    render(
      <EntityDirectoryPicker
        value={[entities[0]]}
        onChange={() => {}}
        searchEntities={searchEntities}
        labels={{ placeholder: "Buscar" }}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Buscar"), {
      target: { value: "AC" },
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Carla Dias · 003/01" })).toBeTruthy();
    });
    expect(screen.queryByRole("button", { name: "ACME Indústria · 001/01" })).toBeNull();
  });

  it("aborta busca anterior ao digitar de novo", async () => {
    const first = vi.fn(
      () =>
        new Promise<typeof entities>(() => {
          /* never resolves */
        }),
    );
    const second = vi.fn().mockResolvedValue([entities[1]]);

    const { rerender } = render(
      <EntityDirectoryPicker
        value={[]}
        onChange={() => {}}
        searchEntities={first}
        labels={{ placeholder: "Buscar" }}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Buscar"), {
      target: { value: "Ab" },
    });

    await waitFor(() => {
      expect(first).toHaveBeenCalled();
    });

    rerender(
      <EntityDirectoryPicker
        value={[]}
        onChange={() => {}}
        searchEntities={second}
        labels={{ placeholder: "Buscar" }}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Buscar"), {
      target: { value: "Beta" },
    });

    await waitFor(() => {
      expect(second).toHaveBeenCalled();
      expect(screen.getByRole("button", { name: "Beta Comércio · 002/01" })).toBeTruthy();
    });
  });

  it("renderiza leading e chip customizado", async () => {
    searchEntities.mockResolvedValueOnce([
      { id: "p3", label: "Carla Dias", secondary: "003/01" },
    ]);

    render(
      <EntityDirectoryPicker
        value={[entities[0]]}
        onChange={() => {}}
        searchEntities={searchEntities}
        labels={{ placeholder: "Buscar" }}
        renderOptionLeading={(entity) => (
          <span data-testid={`lead-${entity.id}`}>A</span>
        )}
        renderSelectedChip={({ entity, label, onRemove }) => (
          <button type="button" data-testid={`chip-${entity.id}`} onClick={onRemove}>
            {label}
          </button>
        )}
      />,
    );

    expect(screen.getByTestId("chip-p1")).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText("Buscar"), {
      target: { value: "Carla" },
    });

    await waitFor(() => {
      expect(screen.getByTestId("lead-p3")).toBeTruthy();
    });
  });
});
