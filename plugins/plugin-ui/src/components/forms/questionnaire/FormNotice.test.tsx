import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FormNotice } from "./FormNotice";

afterEach(cleanup);

describe("FormNotice", () => {
  it("warning é o tom padrão e o papel é note", () => {
    const { getByRole } = render(<FormNotice>Atenção ao prazo.</FormNotice>);
    const note = getByRole("note");
    expect(note.className).toContain("delpi-ui-form-notice--warning");
    expect(note.textContent).toBe("Atenção ao prazo.");
  });

  it("tone=info aplica a classe --info", () => {
    const { getByRole } = render(
      <FormNotice tone="info">Informação útil.</FormNotice>,
    );
    expect(getByRole("note").className).toContain(
      "delpi-ui-form-notice--info",
    );
  });
});
