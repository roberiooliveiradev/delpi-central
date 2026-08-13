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
});
