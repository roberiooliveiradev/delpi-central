import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MessageBodyReadonly } from "./MessageBodyReadonly";

describe("MessageBodyReadonly", () => {
  it("renderiza markdown rico", () => {
    const { container } = render(
      <MessageBodyReadonly markdown="**forte** e `code`" />,
    );
    expect(container.innerHTML.toLowerCase()).toMatch(/<(strong|b)\b/);
    expect(container.innerHTML.toLowerCase()).toMatch(/<code\b/);
  });

  it("renderiza chip @ com mentions", () => {
    render(
      <MessageBodyReadonly
        markdown="Oi @Ana Silva"
        mentions={[
          {
            kind: "user",
            label: "@Ana Silva",
            ref: { user_id: "u2" },
          },
        ]}
      />,
    );
    expect(screen.getByText("Ana Silva")).toBeTruthy();
  });

  it("resolve src de attachment e dispara clique", () => {
    const onClick = vi.fn();
    const { container } = render(
      <MessageBodyReadonly
        markdown="![img](attachment:11111111-2222-3333-4444-555555555555)"
        resolveAttachmentImageSrc={(id) => `/files/${id}`}
        onAttachmentImageClick={onClick}
      />,
    );
    const img = container.querySelector("img[data-attachment-id]");
    expect(img?.getAttribute("src")).toBe(
      "/files/11111111-2222-3333-4444-555555555555",
    );
    if (img) fireEvent.click(img);
    expect(onClick).toHaveBeenCalledWith("11111111-2222-3333-4444-555555555555");
  });
});
