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
};

export function runPortalTourConfetti(durationMs = 2200): () => void {
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

  const particles: ConfettiParticle[] = Array.from({ length: 72 }, () => ({
    x: window.innerWidth * (0.35 + Math.random() * 0.3),
    y: window.innerHeight * 0.22,
    vx: (Math.random() - 0.5) * 7,
    vy: Math.random() * -9 - 4,
    size: 4 + Math.random() * 5,
    color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
    rotation: Math.random() * Math.PI,
    spin: (Math.random() - 0.5) * 0.25,
    life: 1,
  }));

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

      ctx.save();
      ctx.translate(particle.x, particle.y);
      ctx.rotate(particle.rotation);
      ctx.globalAlpha = particle.life;
      ctx.fillStyle = particle.color;
      ctx.fillRect(
        -particle.size / 2,
        -particle.size / 2,
        particle.size,
        particle.size * 0.6,
      );
      ctx.restore();
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
