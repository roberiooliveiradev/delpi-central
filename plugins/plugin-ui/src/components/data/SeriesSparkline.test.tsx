import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SeriesSparkline, seriesSparklineBemClasses } from "./SeriesSparkline";

describe("SeriesSparkline", () => {
  it("renderiza path SVG com dois ou mais pontos", () => {
    const classNames = seriesSparklineBemClasses("test");
    const { container } = render(
      <SeriesSparkline classNames={classNames} points={[10, 20, 15]} aria-label="Teste" />,
    );
    expect(container.querySelector("path")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-series-sparkline")).toBeTruthy();
  });

  it("não renderiza com menos de dois pontos", () => {
    const classNames = seriesSparklineBemClasses("test");
    const { container } = render(<SeriesSparkline classNames={classNames} points={[10]} />);
    expect(container.firstChild).toBeNull();
  });
});
