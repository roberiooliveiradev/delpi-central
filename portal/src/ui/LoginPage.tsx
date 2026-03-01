import { useContext, useEffect, useState } from "react";
import { AuthContext } from "../state/AuthContext";
import { motion } from "framer-motion";
import { Shield, ArrowRight, Activity } from "lucide-react";

type LightningPath = {
  id: string;
  d: string;
  branches: string[];
};

function random(min: number, max: number) {
  return Math.random() * (max - min) + min;
}

function generateLightning(width: number, height: number): LightningPath[] {
  const lines: LightningPath[] = [];

  const count = Math.floor(random(3, 6));

  for (let i = 0; i < count; i++) {
    const startLeft = Math.random() > 0.5;
    const yBase = random(height * 0.3, height * 0.7);
    const segments = 8;

    let x = startLeft ? 0 : width;
    let y = yBase;

    let d = `M ${x} ${y}`;
    const branches: string[] = [];

    for (let s = 0; s < segments; s++) {
      const stepX = width / segments;
      const dir = startLeft ? 1 : -1;

      x += stepX * dir;
      y += random(-30, 30);

      d += ` L ${x} ${y}`;

      // chance de ramificação
      if (Math.random() > 0.7) {
        const branchX = x + random(-60, 60);
        const branchY = y + random(-60, 60);
        branches.push(`M ${x} ${y} L ${branchX} ${branchY}`);
      }
    }

    lines.push({
      id: crypto.randomUUID(),
      d,
      branches,
    });
  }

  return lines;
}

export function LoginPage() {
  const { login, loading } = useContext(AuthContext);
  const [lightning, setLightning] = useState<LightningPath[]>([]);
  const [shock, setShock] = useState(false);

  useEffect(() => {
    const update = () => {
      setLightning(generateLightning(window.innerWidth, window.innerHeight));

      // 🔥 ativa efeito no card
      setShock(true);
      setTimeout(() => setShock(false), 350);
    };

    update();
    const interval = setInterval(update, 2000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const width = 1440;
    const height = 900;

    const update = () => {
      setLightning(generateLightning(width, height));
    };

    update();
    const interval = setInterval(update, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="login-energy">

      {/* SVG DINÂMICO */}
      <svg
        className="lightning-svg"
        viewBox="0 0 1440 900"
        preserveAspectRatio="none"
      >
        {lightning.map((line) => (
          <g key={line.id}>
            <path className="lightning-line" d={line.d} />
            {line.branches.map((b, i) => (
              <path key={i} className="lightning-branch" d={b} />
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
              src="/logoDelpi.svg"
              alt="DELPI"
            />
          </div>

          <div className="login-energy-brand-text">
            <div className="login-energy-kicker">
              <Activity size={16} />
              <span>Energia & Conectividade</span>
            </div>

            <h1 className="login-energy-title">
              Central DELPI
            </h1>

            <p className="login-energy-subtitle">
              Plataforma corporativa de governança,
              aplicações e integrações.
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