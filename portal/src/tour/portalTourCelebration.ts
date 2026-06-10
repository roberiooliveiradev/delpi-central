import {
  getPortalTourAnimationsEnabled,
  prefersReducedMotion,
} from "./portalTourPreferences";

export { prefersReducedMotion };

const CONFETTI_COLORS = [
  "#2563eb",
  "#7c3aed",
  "#059669",
  "#d97706",
  "#db2777",
  "#eab308",
  "#06b6d4",
];

type ConfettiParticle = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  rotation: number;
  spin: number;
  life: number;
  shape: "rect" | "circle";
};

export type PortalTourConfettiOptions = {
  intensity?: "normal" | "levelUp";
  durationMs?: number;
};

function spawnParticles(
  count: number,
  originXRatio: number,
  originYRatio: number,
  spreadRatio: number,
): ConfettiParticle[] {
  return Array.from({ length: count }, () => ({
    x:
      window.innerWidth *
      (originXRatio - spreadRatio / 2 + Math.random() * spreadRatio),
    y: window.innerHeight * originYRatio,
    vx: (Math.random() - 0.5) * (spreadRatio > 0.4 ? 9 : 7),
    vy: Math.random() * -9 - 4,
    size: 4 + Math.random() * (spreadRatio > 0.4 ? 7 : 5),
    color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
    rotation: Math.random() * Math.PI,
    spin: (Math.random() - 0.5) * 0.28,
    life: 1,
    shape: Math.random() > 0.35 ? "rect" : "circle",
  }));
}

function buildParticles(intensity: "normal" | "levelUp"): ConfettiParticle[] {
  if (intensity === "normal") {
    return spawnParticles(72, 0.5, 0.22, 0.3);
  }

  return [
    ...spawnParticles(56, 0.5, 0.18, 0.42),
    ...spawnParticles(36, 0.22, 0.28, 0.22),
    ...spawnParticles(36, 0.78, 0.28, 0.22),
    ...spawnParticles(24, 0.5, 0.08, 0.55),
  ];
}

function drawParticle(ctx: CanvasRenderingContext2D, particle: ConfettiParticle) {
  ctx.save();
  ctx.translate(particle.x, particle.y);
  ctx.rotate(particle.rotation);
  ctx.globalAlpha = particle.life;
  ctx.fillStyle = particle.color;

  if (particle.shape === "circle") {
    ctx.beginPath();
    ctx.arc(0, 0, particle.size / 2, 0, Math.PI * 2);
    ctx.fill();
  } else {
    ctx.fillRect(
      -particle.size / 2,
      -particle.size / 2,
      particle.size,
      particle.size * 0.6,
    );
  }

  ctx.restore();
}

export function runPortalTourConfetti(
  options: PortalTourConfettiOptions | number = {},
): () => void {
  const normalized: PortalTourConfettiOptions =
    typeof options === "number" ? { durationMs: options } : options;
  const intensity = normalized.intensity ?? "normal";
  const durationMs =
    normalized.durationMs ?? (intensity === "levelUp" ? 4200 : 2800);

  if (prefersReducedMotion() || !getPortalTourAnimationsEnabled()) {
    return () => undefined;
  }

  const canvas = document.createElement("canvas");
  canvas.className = "portal-tour-confetti-canvas";
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  canvas.style.width = `${window.innerWidth}px`;
  canvas.style.height = `${window.innerHeight}px`;
  document.body.appendChild(canvas);

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    canvas.remove();
    return () => undefined;
  }

  const particles = buildParticles(intensity);
  const startedAt = performance.now();
  let frameId = 0;

  const tick = (now: number) => {
    const elapsed = now - startedAt;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const particle of particles) {
      particle.x += particle.vx;
      particle.y += particle.vy;
      particle.vy += 0.22;
      particle.rotation += particle.spin;
      particle.life = Math.max(0, 1 - elapsed / durationMs);
      drawParticle(ctx, particle);
    }

    if (elapsed < durationMs) {
      frameId = window.requestAnimationFrame(tick);
      return;
    }

    canvas.remove();
  };

  frameId = window.requestAnimationFrame(tick);

  return () => {
    window.cancelAnimationFrame(frameId);
    canvas.remove();
  };
}

export function runPortalTourLevelUpCelebration(): () => void {
  if (prefersReducedMotion() || !getPortalTourAnimationsEnabled()) {
    return () => undefined;
  }

  const cleanups: Array<() => void> = [];

  const flash = document.createElement("div");
  flash.className = "portal-tour-level-up-flash";
  flash.setAttribute("aria-hidden", "true");
  document.body.appendChild(flash);

  cleanups.push(runPortalTourConfetti({ intensity: "levelUp" }));

  const secondBurstId = window.setTimeout(() => {
    cleanups.push(
      runPortalTourConfetti({ intensity: "levelUp", durationMs: 3200 }),
    );
  }, 680);

  const flashRemoveId = window.setTimeout(() => {
    flash.remove();
  }, 900);

  return () => {
    window.clearTimeout(secondBurstId);
    window.clearTimeout(flashRemoveId);
    flash.remove();
    for (const cleanup of cleanups) cleanup();
  };
}
