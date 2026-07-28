export type BrandLightningPath = {
  id: string;
  d: string;
  branches: string[];
};

export type BrandLightningOrigin = {
  x: number;
  y: number;
};

export type BrandLightningDensity = "low" | "medium" | "high";

export type GenerateBrandLightningInput = {
  width: number;
  height: number;
  origin: BrandLightningOrigin;
  density?: BrandLightningDensity;
};

function random(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/**
 * Raios elétricos radiando a partir de um ponto âncora (swoosh da marca).
 * Adaptado da linguagem visual do login energia do portal.
 */
export function generateBrandLightning(
  input: GenerateBrandLightningInput,
): BrandLightningPath[] {
  const { width, height, origin } = input;
  const density = input.density ?? "medium";
  const count =
    density === "low"
      ? Math.floor(random(2, 4))
      : density === "high"
        ? Math.floor(random(5, 8))
        : Math.floor(random(3, 6));
  const maxReach = Math.min(width, height) * (density === "low" ? 0.55 : 0.78);
  const segments = density === "high" ? 8 : 6;
  const lines: BrandLightningPath[] = [];

  for (let i = 0; i < count; i++) {
    const baseAngle = (Math.PI * 2 * i) / count + random(-0.4, 0.4);
    const length = maxReach * random(0.42, 1);
    let x = origin.x;
    let y = origin.y;
    let d = `M ${x.toFixed(1)} ${y.toFixed(1)}`;
    const branches: string[] = [];

    for (let s = 0; s < segments; s++) {
      const t = (s + 1) / segments;
      const perp = baseAngle + Math.PI / 2;
      const jitter = random(-22, 22) * (1 - t * 0.25);
      x = origin.x + Math.cos(baseAngle) * length * t + Math.cos(perp) * jitter;
      y = origin.y + Math.sin(baseAngle) * length * t + Math.sin(perp) * jitter;
      d += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;

      if (Math.random() > 0.68) {
        const bx = x + random(-50, 50);
        const by = y + random(-50, 50);
        branches.push(
          `M ${x.toFixed(1)} ${y.toFixed(1)} L ${bx.toFixed(1)} ${by.toFixed(1)}`,
        );
      }
    }

    lines.push({ id: createId(), d, branches });
  }

  return lines;
}

/** True se o path principal começa no origin (tolerância). */
export function lightningPathStartsNearOrigin(
  path: BrandLightningPath,
  origin: BrandLightningOrigin,
  tolerance = 2,
): boolean {
  const match = /^M\s+([\d.-]+)\s+([\d.-]+)/.exec(path.d.trim());
  if (!match) return false;
  const x = Number(match[1]);
  const y = Number(match[2]);
  return Math.abs(x - origin.x) <= tolerance && Math.abs(y - origin.y) <= tolerance;
}
