import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConversationCodeBlock } from "./ConversationCodeBlock";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function stubClipboard(impl: () => Promise<void>) {
  const writeText = vi.fn(impl);
  vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
  return writeText;
}

describe("ConversationCodeBlock — anatomy (CB-V01)", () => {
  it("renders compact header, language label, copy button and pre>code", () => {
    const { container } = render(
      <ConversationCodeBlock code={"SELECT 1;"} language="sql" />,
    );
    const group = container.querySelector(
      '.delpi-ui-conversation-code-block[role="group"]',
    );
    expect(group?.getAttribute("aria-label")).toBe("Bloco de código SQL");
    expect(
      container.querySelector(".delpi-ui-conversation-code-block__bar"),
    ).toBeTruthy();
    expect(
      container
        .querySelector(".delpi-ui-conversation-code-block__lang")
        ?.textContent,
    ).toContain("SQL");
    expect(
      screen.getByRole("button", { name: "Copiar código" }),
    ).toBeTruthy();
    const pre = container.querySelector(
      "pre.delpi-ui-conversation-code-block__pre",
    ) as HTMLElement;
    expect(pre.getAttribute("role")).toBe("region");
    expect(pre.getAttribute("tabindex")).toBe("0");
    expect(pre.querySelector("code")?.textContent).toBe("SELECT 1;");
  });
});

describe("ConversationCodeBlock — literal preservation (CB-V02)", () => {
  it("preserves indentation, tabs, blank lines and CR/LF verbatim", () => {
    const code = "def f():\n\treturn {\r\n  \r\n}\n";
    const { container } = render(<ConversationCodeBlock code={code} />);
    expect(
      container.querySelector("pre code")?.textContent,
    ).toBe(code);
  });

  it("renders HTML/script/markdown content as inert text (CB-V09)", () => {
    const code =
      '<script>alert("x")</script>\n**bold** [l](https://e.t)\n<img src=x onerror=p>';
    const { container } = render(<ConversationCodeBlock code={code} />);
    const pre = container.querySelector("pre");
    expect(pre?.textContent).toBe(code);
    expect(container.querySelector("script, img, a")).toBeNull();
  });
});

describe("ConversationCodeBlock — languages (CB-V05)", () => {
  it.each([
    ["sql", "SQL"],
    ["python", "Python"],
    ["json", "JSON"],
    ["typescript", "TypeScript"],
    ["javascript", "JavaScript"],
    ["bash", "Bash"],
    ["yaml", "YAML"],
    ["text", "Texto"],
  ])("maps %s to %s", (language, label) => {
    const { container } = render(
      <ConversationCodeBlock code="x" language={language} />,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-code-block__lang")
        ?.textContent,
    ).toContain(label);
  });

  it("shows the sanitized value for a valid unlisted language", () => {
    const { container } = render(
      <ConversationCodeBlock code="x" language="C++" />,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-code-block__lang")
        ?.textContent,
    ).toContain("c++");
  });

  it("falls back to a neutral label when language is absent or unsafe", () => {
    const { container: absent } = render(<ConversationCodeBlock code="x" />);
    expect(
      absent.querySelector(".delpi-ui-conversation-code-block__lang")
        ?.textContent,
    ).toContain("Código");
    expect(
      absent
        .querySelector('.delpi-ui-conversation-code-block[role="group"]')
        ?.getAttribute("aria-label"),
    ).toBe("Bloco de código");

    cleanup();
    const { container: unsafe } = render(
      <ConversationCodeBlock code="x" language="!!!" />,
    );
    expect(
      unsafe.querySelector(".delpi-ui-conversation-code-block__lang")
        ?.textContent,
    ).toContain("Código");
  });

  it("strips unsafe characters from the language label", () => {
    const { container } = render(
      <ConversationCodeBlock code="x" language={'"><img src=x>'} />,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-code-block__lang")
        ?.textContent,
    ).toContain("imgsrcx");
  });

  it("truncates the language label to the 20-char safe bound", () => {
    const { container } = render(
      <ConversationCodeBlock
        code="x"
        language="abcdefghij0123456789EXTRA"
      />,
    );
    const lang = container.querySelector(
      ".delpi-ui-conversation-code-block__lang",
    );
    expect(lang?.textContent).toContain("abcdefghij0123456789");
    expect(lang?.textContent).not.toContain("EXTRA");
  });
});

describe("ConversationCodeBlock — copy behavior (CB-V03, CB-V04)", () => {
  it("shows Copiado only after clipboard resolves, then resets", async () => {
    vi.useFakeTimers();
    let resolve!: () => void;
    const writeText = stubClipboard(
      () => new Promise<void>((r) => (resolve = r)),
    );
    render(<ConversationCodeBlock code={"line 1\nline 2"} />);
    fireEvent.click(screen.getByRole("button", { name: "Copiar código" }));
    expect(writeText).toHaveBeenCalledWith("line 1\nline 2");
    // No early success announcement while the promise is pending.
    expect(screen.queryByText("Copiado")).toBeNull();
    await act(async () => resolve());
    expect(screen.getByText("Copiado")).toBeTruthy();
    await act(async () => {
      vi.advanceTimersByTime(1600);
    });
    expect(screen.queryByText("Copiado")).toBeNull();
  });

  it("shows honest error state when clipboard rejects (CB-V04)", async () => {
    stubClipboard(() => Promise.reject(new Error("denied")));
    render(<ConversationCodeBlock code="x" />);
    fireEvent.click(screen.getByRole("button", { name: "Copiar código" }));
    await waitFor(() =>
      expect(screen.getByText("Não foi possível copiar")).toBeTruthy(),
    );
    expect(screen.queryByText("Copiado")).toBeNull();
  });

  it("shows error state when clipboard API is unavailable", async () => {
    vi.stubGlobal("navigator", { ...navigator, clipboard: undefined });
    render(<ConversationCodeBlock code="x" />);
    fireEvent.click(screen.getByRole("button", { name: "Copiar código" }));
    await waitFor(() =>
      expect(screen.getByText("Não foi possível copiar")).toBeTruthy(),
    );
  });

  it("announces feedback through a single aria-live region", async () => {
    stubClipboard(() => Promise.resolve());
    const { container } = render(<ConversationCodeBlock code="x" />);
    fireEvent.click(screen.getByRole("button", { name: "Copiar código" }));
    await waitFor(() => expect(screen.getByText("Copiado")).toBeTruthy());
    const live = container.querySelectorAll('[aria-live="polite"]');
    expect(live).toHaveLength(1);
  });

  it("keeps independent copy state across multiple blocks (CB-V06)", async () => {
    const writeText = stubClipboard(() => Promise.resolve());
    render(
      <>
        <ConversationCodeBlock code="first" language="sql" />
        <ConversationCodeBlock code="second" language="json" />
      </>,
    );
    const buttons = screen.getAllByRole("button", { name: "Copiar código" });
    expect(buttons).toHaveLength(2);
    fireEvent.click(buttons[0]);
    await waitFor(() => expect(screen.getByText("Copiado")).toBeTruthy());
    expect(writeText).toHaveBeenCalledWith("first");
    expect(writeText).not.toHaveBeenCalledWith("second");
    // Second block stays idle.
    expect(screen.getAllByText("Copiado")).toHaveLength(1);
  });

  it("latest click wins when responses resolve out of order", async () => {
    vi.useFakeTimers();
    const resolvers: Array<() => void> = [];
    const writeText = stubClipboard(
      () => new Promise<void>((r) => resolvers.push(r)),
    );
    render(<ConversationCodeBlock code="x" />);
    const button = screen.getByRole("button", { name: "Copiar código" });
    fireEvent.click(button);
    fireEvent.click(button);
    expect(writeText).toHaveBeenCalledTimes(2);
    // First (stale) response must not corrupt the newer operation state.
    await act(async () => resolvers[0]());
    await act(async () => resolvers[1]());
    expect(screen.getByText("Copiado")).toBeTruthy();
  });

  it("omits the copy button when copyEnabled=false", () => {
    render(<ConversationCodeBlock code="x" copyEnabled={false} />);
    expect(
      screen.queryByRole("button", { name: "Copiar código" }),
    ).toBeNull();
  });

  it("allows overriding labels via the labels prop", () => {
    render(
      <ConversationCodeBlock
        code="x"
        labels={{ copyCode: "Copiar trecho", blockLabel: "Trecho de código" }}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Copiar trecho" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("group", { name: "Trecho de código" }),
    ).toBeTruthy();
  });
});
