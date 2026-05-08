// portal/src/pages/LoginPage.tsx

import { useContext, useEffect, useState } from "react";
import { AuthContext } from "../state/AuthContext";
import { motion } from "framer-motion";
import { Shield, ArrowRight, Activity } from "lucide-react";

type LightningPath = {
  id: string;
  d: string;
  branches: string[];
};

type ViewportSize = {
  width: number;
  height: number;
};

function random(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

function createId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getViewportSize(): ViewportSize {
  if (typeof window === "undefined") {
    return {
      width: 1440,
      height: 900,
    };
  }

  return {
    width: Math.max(window.innerWidth, 320),
    height: Math.max(window.innerHeight, 320),
  };
}

function generateLightning(width: number, height: number): LightningPath[] {
  const isSmallScreen = width <= 640;
  const isLowHeight = height <= 520;

  const lines: LightningPath[] = [];
  const count = isSmallScreen || isLowHeight
    ? Math.floor(random(2, 4))
    : Math.floor(random(3, 6));

  for (let i = 0; i < count; i++) {
    const startLeft = Math.random() > 0.5;
    const yBase = random(height * 0.28, height * 0.72);
    const segments = isSmallScreen ? 6 : 8;

    let x = startLeft ? 0 : width;
    let y = yBase;

    let d = `M ${x} ${y}`;
    const branches: string[] = [];

    for (let s = 0; s < segments; s++) {
      const stepX = width / segments;
      const dir = startLeft ? 1 : -1;

      x += stepX * dir;
      y += random(isSmallScreen ? -20 : -30, isSmallScreen ? 20 : 30);

      d += ` L ${x} ${y}`;

      if (!isSmallScreen && Math.random() > 0.7) {
        const branchX = x + random(-60, 60);
        const branchY = y + random(-60, 60);
        branches.push(`M ${x} ${y} L ${branchX} ${branchY}`);
      }
    }

    lines.push({
      id: createId(),
      d,
      branches,
    });
  }

  return lines;
}

export function LoginPage() {
  const { login, loading } = useContext(AuthContext);

  const [viewport, setViewport] = useState<ViewportSize>(() => getViewportSize());
  const [lightning, setLightning] = useState<LightningPath[]>([]);
  const [shock, setShock] = useState(false);

  useEffect(() => {
    function updateViewport() {
      setViewport(getViewportSize());
    }

    updateViewport();

    window.addEventListener("resize", updateViewport);
    window.addEventListener("orientationchange", updateViewport);

    return () => {
      window.removeEventListener("resize", updateViewport);
      window.removeEventListener("orientationchange", updateViewport);
    };
  }, []);

  useEffect(() => {
    function updateLightning() {
      setLightning(generateLightning(viewport.width, viewport.height));

      setShock(true);
      window.setTimeout(() => setShock(false), 350);
    }

    updateLightning();

    const interval = window.setInterval(updateLightning, 2200);

    return () => window.clearInterval(interval);
  }, [viewport.width, viewport.height]);

  return (
    <div className="login-energy">
      <div className="login-energy-grid" />
      <div className="login-energy-glow" />

      <svg
        className="lightning-svg"
        viewBox={`0 0 ${viewport.width} ${viewport.height}`}
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {lightning.map((line) => (
          <g key={line.id}>
            <path className="lightning-line" d={line.d} />

            {line.branches.map((branch, index) => (
              <path
                key={`${line.id}-${index}`}
                className="lightning-branch"
                d={branch}
              />
            ))}
          </g>
        ))}
      </svg>

      <motion.div
        className={`login-energy-card ${shock ? "lightning-hit" : ""}`}
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <div className="login-energy-brand">
          <div className="login-energy-logo">
            <img
              src="/logoMinhaDelpi.svg"
              alt="Minha DELPI"
            />
          </div>

          <div className="login-energy-brand-text">
            <div className="login-energy-kicker">
              <Activity size={16} />
              <span>Energia & Conectividade</span>
            </div>

            <p className="login-energy-subtitle">
              Plataforma corporativa de governança, aplicações e integrações.
            </p>
          </div>
        </div>

        <button
          className="login-energy-action"
          onClick={login}
          disabled={loading}
          type="button"
        >
          <Shield size={18} />
          <span>
            {loading ? "Conectando..." : "Entrar com DELPI SSO"}
          </span>
          <ArrowRight size={16} />
        </button>

        <div className="login-energy-hint">
          Você será redirecionado para autenticação segura (SSO).
        </div>

        <div className="login-energy-footer">
          <span className="login-energy-dot" />
          <span>Ambiente protegido • Tokens curtos • Refresh automático</span>
        </div>
      </motion.div>
    </div>
  );
}