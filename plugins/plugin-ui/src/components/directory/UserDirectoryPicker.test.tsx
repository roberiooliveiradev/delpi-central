// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { UserDirectoryPicker } from "./UserDirectoryPicker";

const users = [
  { id: "u1", name: "Ana Lima", email: "ana@delpi.com.br" },
  { id: "u2", name: "Bruno Souza", email: "bruno@delpi.com.br" },
];

const searchUsers = vi.fn().mockResolvedValue([]);

afterEach(cleanup);

describe("UserDirectoryPicker", () => {
  it("mostra a lista interna de selecionados por padrão", () => {
    render(
      <UserDirectoryPicker value={users} onChange={() => {}} searchUsers={searchUsers} />,
    );

    expect(screen.getByText("Ana Lima")).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Remover" })).toHaveLength(2);
  });

  it("oculta a lista interna com showSelectedList=false", () => {
    render(
      <UserDirectoryPicker
        value={users}
        onChange={() => {}}
        searchUsers={searchUsers}
        showSelectedList={false}
      />,
    );

    expect(screen.queryByText("Ana Lima")).toBeNull();
    expect(screen.queryByRole("button", { name: "Remover" })).toBeNull();
  });
});
