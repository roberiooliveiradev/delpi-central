import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

import { ColorPickerPopover, ColorPickerPopoverTrigger, ShapeFillMenu } from "./ColorPickerPopover";
import { ShapeOutlineMenu } from "./ShapeOutlineMenu";
import * as eyedropper from "./pickColorWithEyedropper";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ColorPickerPopover", () => {
  it("mostra Sem fundo no variant fill e aplica transparent", () => {
    const onChange = vi.fn();
    const { container } = render(
      <ColorPickerPopover variant="fill" value="#ef4444" onChange={onChange} />,
    );
    const view = within(container);

    fireEvent.click(view.getByRole("button", { name: "Sem fundo" }));
    expect(onChange).toHaveBeenCalledWith("transparent");
  });

  it("com value transparent destaca Sem fundo e não o swatch preto", () => {
    const { container } = render(
      <ColorPickerPopover variant="fill" value="transparent" onChange={vi.fn()} />,
    );
    const view = within(container);
    const noFill = view.getByRole("button", { name: "Sem fundo" });
    expect(noFill.getAttribute("aria-pressed")).toBe("true");
    expect(noFill.className).toContain("delpi-ui-color-picker__action--selected");
    expect(view.queryAllByRole("button", { pressed: true }).filter((el) => el !== noFill)).toHaveLength(
      0,
    );
  });

  it("gatilho com transparent mostra prévia com linha vermelha (sem cor)", () => {
    const { container } = render(
      <ColorPickerPopoverTrigger
        triggerLabel="Cor de preenchimento"
        variant="fill"
        value="transparent"
        onChange={vi.fn()}
      />,
    );
    const preview = container.querySelector(".delpi-ui-color-picker-trigger__preview");
    expect(preview?.className).toContain("delpi-ui-color-picker-trigger__preview--none");
  });

  it("com value transparent em outline destaca Sem contorno", () => {
    const { container } = render(
      <ColorPickerPopover variant="outline" value="transparent" onChange={vi.fn()} />,
    );
    const noOutline = within(container).getByRole("button", { name: "Sem contorno" });
    expect(noOutline.getAttribute("aria-pressed")).toBe("true");
  });

  it("mostra Automático no variant text e grava sentinel auto", () => {
    const onChange = vi.fn();
    const { container } = render(
      <ColorPickerPopover
        variant="text"
        value="#111111"
        contrastBackground="#0f172a"
        onChange={onChange}
      />,
    );
    const view = within(container);

    fireEvent.click(view.getByRole("button", { name: "Automático" }));
    expect(onChange).toHaveBeenCalledWith("auto");
  });

  it("mostra Sem contorno no variant outline", () => {
    const onChange = vi.fn();
    const { container } = render(
      <ColorPickerPopover variant="outline" value="#089bdb" onChange={onChange} />,
    );
    const view = within(container);

    expect(view.getByRole("button", { name: "Sem contorno" })).toBeTruthy();
    expect(view.queryByRole("button", { name: "Sem fundo" })).toBeNull();
    expect(view.queryByRole("button", { name: "Automático" })).toBeNull();
  });

  it("Mais cores abre popover (não modal) e confirma a cor", () => {
    const onChange = vi.fn();
    render(<ColorPickerPopover variant="fill" value="#089bdb" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Mais cores…" }));
    expect(document.querySelector(".delpi-ui-color-more-popover")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-shape-dialog-overlay")).toBeNull();
    expect(screen.getByRole("dialog", { name: "Cores" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(onChange).toHaveBeenCalled();
    expect(document.querySelector(".delpi-ui-color-more-popover")).toBeNull();
  });

  it("Conta-gotas usa EyeDropper quando disponível", async () => {
    vi.spyOn(eyedropper, "isEyedropperSupported").mockReturnValue(true);
    vi.spyOn(eyedropper, "pickColorWithEyedropper").mockResolvedValue("#aabbcc");
    const onChange = vi.fn();
    render(<ColorPickerPopover variant="fill" value="#089bdb" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Conta-gotas" }));
    await waitFor(() => expect(onChange).toHaveBeenCalledWith("#aabbcc"));
  });

  it("sem onFillChange não mostra aba Gradiente", () => {
    render(<ColorPickerPopover variant="fill" value="#ef4444" onChange={vi.fn()} />);
    expect(screen.queryByRole("tab", { name: "Gradiente" })).toBeNull();
    expect(screen.queryByRole("tab", { name: "Cor" })).toBeNull();
  });

  it("com onFillChange e allowedFillKinds gradient mostra abas e emite fill", () => {
    const onChange = vi.fn();
    const onFillChange = vi.fn();
    render(
      <ColorPickerPopover
        variant="fill"
        value="#ef4444"
        onChange={onChange}
        onFillChange={onFillChange}
        allowedFillKinds={["solid", "gradient"]}
      />,
    );

    expect(screen.getByRole("tab", { name: "Cor" })).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: "Gradiente" }));
    expect(onFillChange).toHaveBeenCalledWith(
      expect.objectContaining({
        kind: "gradient",
        angle: 180,
        stops: expect.arrayContaining([
          expect.objectContaining({ color: "#ef4444", position: 0 }),
        ]),
      }),
    );
  });

  it("re-clicar Gradiente não zera ângulo nem stops", () => {
    const onFillChange = vi.fn();
    const fill = {
      kind: "gradient" as const,
      angle: 45,
      stops: [
        { color: "#111111", position: 0 },
        { color: "#abcdef", position: 50 },
        { color: "#eeeeee", position: 100 },
      ],
    };
    render(
      <ColorPickerPopover
        variant="fill"
        value="#111111"
        fill={fill}
        onChange={vi.fn()}
        onFillChange={onFillChange}
        allowedFillKinds={["solid", "gradient"]}
      />,
    );
    fireEvent.click(screen.getByRole("tab", { name: "Gradiente" }));
    expect(onFillChange).toHaveBeenCalledWith(fill);
    expect(onFillChange.mock.calls.some((call) => call[0]?.angle === 180)).toBe(false);
  });

  it("trocar para aba Cor não aplica sólido enquanto o fill é gradiente", () => {
    const onChange = vi.fn();
    const onFillChange = vi.fn();
    render(
      <ColorPickerPopover
        variant="outline"
        value="#089bdb"
        fill={{
          kind: "gradient",
          angle: 135,
          stops: [
            { color: "#089bdb", position: 0 },
            { color: "#be123c", position: 100 },
          ],
        }}
        onChange={onChange}
        onFillChange={onFillChange}
        allowedFillKinds={["solid", "gradient"]}
      />,
    );
    fireEvent.click(screen.getByRole("tab", { name: "Cor" }));
    expect(onFillChange).not.toHaveBeenCalled();
    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByRole("tab", { name: "Cor" }).getAttribute("aria-selected")).toBe("true");
  });

  it("aba Cor só aplica sólido ao escolher uma cor", () => {
    const onChange = vi.fn();
    const onFillChange = vi.fn();
    render(
      <ColorPickerPopover
        variant="fill"
        value="#089bdb"
        fill={{
          kind: "gradient",
          angle: 135,
          stops: [
            { color: "#089bdb", position: 0 },
            { color: "#be123c", position: 100 },
          ],
        }}
        onChange={onChange}
        onFillChange={onFillChange}
        allowedFillKinds={["solid", "gradient"]}
      />,
    );
    fireEvent.click(screen.getByRole("tab", { name: "Cor" }));
    fireEvent.click(screen.getByRole("button", { name: "#ff0000" }));
    expect(onFillChange).toHaveBeenCalledWith({ kind: "solid", color: "#ff0000" });
    expect(onChange).toHaveBeenCalledWith("#ff0000");
  });

  it("menu de preenchimento usa fill sólido na prévia mesmo sem value", () => {
    const { container } = render(
      <ShapeFillMenu value={undefined} fill={{ kind: "solid", color: "#089bdb" }} onChange={vi.fn()} />,
    );
    const preview = container.querySelector(".delpi-ui-shape-menu__trigger-swatch");
    expect((preview as HTMLElement).style.background).toMatch(/#089bdb|rgb\(8,\s*155,\s*219\)/i);
  });

  it("menu de contorno pinta prévia com background (gradiente válido)", () => {
    const { container } = render(
      <ShapeOutlineMenu
        color={undefined}
        fill={{
          kind: "gradient",
          angle: 135,
          stops: [
            { color: "#089bdb", position: 0 },
            { color: "#be123c", position: 100 },
          ],
        }}
        onColorChange={vi.fn()}
      />,
    );
    const preview = container.querySelector(".delpi-ui-shape-menu__trigger-swatch");
    const style = preview?.getAttribute("style") ?? "";
    expect(style).toContain("linear-gradient");
    expect(style).not.toContain("border-color");
  });

  it("gatilho com fill sólido usa a cor do fill mesmo sem value", () => {
    const { container } = render(
      <ColorPickerPopoverTrigger
        triggerLabel="Cor de preenchimento"
        fill={{ kind: "solid", color: "#166534" }}
        onChange={vi.fn()}
      />,
    );
    const preview = container.querySelector(".delpi-ui-color-picker-trigger__preview");
    expect((preview as HTMLElement).style.background).toMatch(/#166534|rgb\(22,\s*101,\s*52\)/i);
  });

  it("gatilho com fill gradient usa preview CSS do helper", () => {
    const { container } = render(
      <ColorPickerPopoverTrigger
        triggerLabel="Cor de preenchimento"
        value="#0f172a"
        fill={{
          kind: "gradient",
          angle: 180,
          stops: [
            { color: "#0f172a", position: 0 },
            { color: "#1e3a5f", position: 100 },
          ],
        }}
        onChange={vi.fn()}
        onFillChange={vi.fn()}
        allowedFillKinds={["solid", "gradient"]}
      />,
    );
    const preview = container.querySelector(".delpi-ui-color-picker-trigger__preview");
    expect(preview?.getAttribute("style") ?? "").toContain("linear-gradient");
  });
});
