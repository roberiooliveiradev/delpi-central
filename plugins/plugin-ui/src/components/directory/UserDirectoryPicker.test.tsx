// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { UserDirectoryPicker } from "./UserDirectoryPicker";

const users = [
  { id: "u1", name: "Ana Lima", email: "ana@delpi.com.br" },
  { id: "u2", name: "Bruno Souza", email: "bruno@delpi.com.br" },
];

const searchUsers = vi.fn().mockResolvedValue([]);

afterEach(cleanup);

describe("UserDirectoryPicker", () => {
  it("mostra chips dos selecionados com × por padrão", () => {
    render(
      <UserDirectoryPicker value={users} onChange={() => {}} searchUsers={searchUsers} />,
    );

    expect(screen.getByText("Ana Lima · ana@delpi.com.br")).toBeTruthy();
    expect(document.querySelectorAll(".delpi-ui-tag-chip")).toHaveLength(2);
    expect(
      screen.getByRole("button", { name: "Remover Ana Lima · ana@delpi.com.br" }),
    ).toBeTruthy();
  });

  it("oculta chips com showSelectedList=false", () => {
    render(
      <UserDirectoryPicker
        value={users}
        onChange={() => {}}
        searchUsers={searchUsers}
        showSelectedList={false}
      />,
    );

    expect(screen.queryByText("Ana Lima")).toBeNull();
    expect(document.querySelector(".delpi-ui-tag-chip")).toBeNull();
  });

  it("com showEmail=false lista só o nome", () => {
    render(
      <UserDirectoryPicker
        value={users}
        onChange={() => {}}
        searchUsers={searchUsers}
        showEmail={false}
      />,
    );

    expect(screen.getByText("Ana Lima")).toBeTruthy();
    expect(screen.queryByText(/ana@delpi\.com\.br/)).toBeNull();
  });

  it("com maxSelected=1 substitui a seleção ao escolher outro", async () => {
    const onChange = vi.fn();
    searchUsers.mockResolvedValueOnce([
      { id: "u3", name: "Carla Dias", email: "carla@delpi.com.br" },
    ]);

    render(
      <UserDirectoryPicker
        value={[users[0]]}
        onChange={onChange}
        searchUsers={searchUsers}
        maxSelected={1}
        showEmail={false}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Buscar por nome"), {
      target: { value: "Carla" },
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Carla Dias" })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Carla Dias" }));
    expect(onChange).toHaveBeenCalledWith([
      { id: "u3", name: "Carla Dias", email: "carla@delpi.com.br" },
    ]);
  });

  it("omite da lista quem já está selecionado", async () => {
    searchUsers.mockResolvedValueOnce([
      users[0],
      { id: "u3", name: "Carla Dias", email: "carla@delpi.com.br" },
    ]);

    render(
      <UserDirectoryPicker
        value={[users[0]]}
        onChange={() => {}}
        searchUsers={searchUsers}
        showEmail={false}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Buscar por nome"), {
      target: { value: "Ana" },
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Carla Dias" })).toBeTruthy();
    });
    expect(screen.queryByRole("button", { name: "Ana Lima" })).toBeNull();
  });

  it("renderiza leading nas sugestões e chip customizado", async () => {
    searchUsers.mockResolvedValueOnce([
      { id: "u3", name: "Carla Dias", email: "carla@delpi.com.br" },
    ]);

    render(
      <UserDirectoryPicker
        value={[users[0]]}
        onChange={() => {}}
        searchUsers={searchUsers}
        showEmail={false}
        renderOptionLeading={(user) => (
          <span data-testid={`lead-${user.id}`}>A</span>
        )}
        renderSelectedChip={({ user, label, onRemove }) => (
          <button type="button" data-testid={`chip-${user.id}`} onClick={onRemove}>
            {label}
          </button>
        )}
      />,
    );

    expect(screen.getByTestId("chip-u1")).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText("Buscar por nome"), {
      target: { value: "Carla" },
    });

    await waitFor(() => {
      expect(screen.getByTestId("lead-u3")).toBeTruthy();
    });
  });

  it("mantém resultados quando o pai recria searchUsers a cada render", async () => {
    let resolveSearch!: (value: typeof users) => void;
    const pending = new Promise<(typeof users)[number][]>((resolve) => {
      resolveSearch = resolve;
    });
    const firstSearch = vi.fn(() => pending);

    const { rerender } = render(
      <UserDirectoryPicker
        value={[]}
        onChange={() => {}}
        searchUsers={firstSearch}
        showEmail={false}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Buscar por nome"), {
      target: { value: "Ana" },
    });

    await waitFor(() => {
      expect(firstSearch).toHaveBeenCalled();
    });

    rerender(
      <UserDirectoryPicker
        value={[]}
        onChange={() => {}}
        searchUsers={vi.fn(() => pending)}
        showEmail={false}
      />,
    );

    resolveSearch([users[0]]);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Ana Lima" })).toBeTruthy();
    });
  });
});
