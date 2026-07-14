import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CanalDenunciaPage } from "./CanalDenunciaPage";
import * as api from "../api/canalDenunciaApi";
import {
  ERROR_MESSAGE,
  MAX_DESCRIPTION_LENGTH,
  SUCCESS_MESSAGE,
} from "../constants/form";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("CanalDenunciaPage", () => {
  it("renderiza título, logo oficial e orientações iniciais", () => {
    render(<CanalDenunciaPage />);
    expect(screen.getByRole("heading", { name: "Canal de Denúncia" })).toBeTruthy();
    expect(screen.getByRole("img", { name: "Minha DELPI" })).toBeTruthy();
    expect(screen.getByTestId("canal-denuncia-logo").getAttribute("src")).toBeTruthy();
    expect(
      screen.getByText(/forma anônima/i),
    ).toBeTruthy();
    expect(
      screen.getAllByText(/canal-denuncia@delpi\.com\.br/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("list", { name: /como funciona/i }),
    ).toBeTruthy();
    expect(screen.getByText("Escreva o relato")).toBeTruthy();
    expect(screen.getByText("Análise responsável")).toBeTruthy();



    expect(
      (screen.getByRole("button", { name: "Enviar denúncia" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });

  it("mantém botão desabilitado com menos de 10 caracteres úteis", () => {
    render(<CanalDenunciaPage />);
    fireEvent.change(screen.getByLabelText("Relato da denúncia"), {
      target: { value: "   curto   " },
    });
    expect(
      (screen.getByRole("button", { name: "Enviar denúncia" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });

  it("atualiza contador de caracteres", () => {
    render(<CanalDenunciaPage />);
    fireEvent.change(screen.getByLabelText("Relato da denúncia"), {
      target: { value: "1234567890" },
    });
    expect(screen.getByTestId("char-counter").textContent).toBe(
      `10 / ${MAX_DESCRIPTION_LENGTH}`,
    );
  });

  it("envia somente description no body e limpa formulário no sucesso", async () => {
    const spy = vi.spyOn(api, "createAnonymousDenuncia").mockResolvedValue({
      id: "11111111-1111-1111-1111-111111111111",
      createdAt: "2026-07-14T12:00:00+00:00",
    });

    render(<CanalDenunciaPage />);
    const textarea = screen.getByLabelText("Relato da denúncia");
    fireEvent.change(textarea, {
      target: { value: "  Relato anônimo completo para a Ouvidoria.  " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar denúncia" }));

    await waitFor(() => {
      expect(spy).toHaveBeenCalledTimes(1);
    });
    expect(spy.mock.calls[0]?.[0]).toEqual({
      description: "Relato anônimo completo para a Ouvidoria.",
    });
    expect(Object.keys(spy.mock.calls[0]?.[0] ?? {})).toEqual(["description"]);

    await waitFor(() => {
      expect(screen.getByRole("status").textContent).toContain(SUCCESS_MESSAGE);
    });
    expect((textarea as HTMLTextAreaElement).value).toBe("");
    expect(screen.queryByText(/11111111/i)).toBeNull();
  });

  it("em erro preserva o texto e mostra mensagem genérica", async () => {
    vi.spyOn(api, "createAnonymousDenuncia").mockRejectedValue(new Error("boom"));

    render(<CanalDenunciaPage />);
    const textarea = screen.getByLabelText("Relato da denúncia");
    const text = "Relato que deve permanecer após falha de envio.";
    fireEvent.change(textarea, { target: { value: text } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar denúncia" }));

    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(ERROR_MESSAGE);
    });
    expect((textarea as HTMLTextAreaElement).value).toBe(text);
    expect(screen.queryByText(/boom/i)).toBeNull();
  });

  it("impede envio duplicado enquanto enviando", async () => {
    let resolvePromise: ((value: api.CreateAnonymousDenunciaResult) => void) | undefined;
    const spy = vi.spyOn(api, "createAnonymousDenuncia").mockImplementation(
      () =>
        new Promise((resolve) => {
          resolvePromise = resolve;
        }),
    );

    render(<CanalDenunciaPage />);
    fireEvent.change(screen.getByLabelText("Relato da denúncia"), {
      target: { value: "Texto válido para testar envio duplicado." },
    });
    const button = screen.getByRole("button", { name: "Enviar denúncia" });
    fireEvent.click(button);
    fireEvent.click(button);

    await waitFor(() => {
      const button = screen.getByRole("button", {
        name: "Enviando...",
      }) as HTMLButtonElement;
      expect(button.disabled).toBe(true);
    });
    expect(spy).toHaveBeenCalledTimes(1);

    resolvePromise?.({
      id: "22222222-2222-2222-2222-222222222222",
      createdAt: "2026-07-14T12:00:00+00:00",
    });
    await waitFor(() => {
      expect(screen.getByRole("status")).toBeTruthy();
    });
  });
});
