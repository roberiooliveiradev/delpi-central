import { useEffect, useState } from "react";

import {
  generateBrandLightning,
  type BrandLightningDensity,
  type BrandLightningOrigin,
  type BrandLightningPath,
} from "./brandLightning";

export type BrandLightningLayerProps = {
  width: number;
  height: number;
  origin: BrandLightningOrigin;
  density?: BrandLightningDensity;
  className?: string;
  lineClassName?: string;
  branchClassName?: string;
  intervalMs?: number;
  reducedMotion?: boolean;
};

/**
 * Camada SVG de raios brandados — regenera paths a partir do origin.
 */
export function BrandLightningLayer({
  width,
  height,
  origin,
  density = "medium",
  className,
  lineClassName,
  branchClassName,
  intervalMs = 2200,
  reducedMotion = false,
}: BrandLightningLayerProps) {
  const [paths, setPaths] = useState<BrandLightningPath[]>([]);
  const [flashKey, setFlashKey] = useState(0);

  useEffect(() => {
    if (width < 32 || height < 32) return;

    function burst() {
      setPaths(generateBrandLightning({ width, height, origin, density }));
      setFlashKey((key) => key + 1);
    }

    burst();
    if (reducedMotion) return;

    const id = window.setInterval(burst, intervalMs);
    return () => window.clearInterval(id);
  }, [width, height, origin.x, origin.y, density, intervalMs, reducedMotion]);

  if (width < 32 || height < 32 || paths.length === 0) return null;

  return (
    <svg
      className={className}
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      aria-hidden="true"
      focusable="false"
    >
      <g key={flashKey}>
        {paths.map((line) => (
          <g key={line.id}>
            <path className={lineClassName} d={line.d} />
            {line.branches.map((branch, index) => (
              <path key={`${line.id}-b-${index}`} className={branchClassName} d={branch} />
            ))}
          </g>
        ))}
      </g>
    </svg>
  );
}
