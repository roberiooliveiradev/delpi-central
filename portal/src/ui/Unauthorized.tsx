// src/ui/Unauthorized.tsx

import { motion } from "framer-motion";
import { ArrowLeft, Home, ShieldAlert, UserCircle } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import "./Unauthorized.css";

type UnauthorizedLocationState = {
  from?: string;
  permission?: string;
};

export const Unauthorized = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state ?? {}) as UnauthorizedLocationState;
  const fromPath = typeof state.from === "string" ? state.from : null;

  return (
    <div className="unauthorized-page">
      <motion.article
        className="unauthorized-card"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.22 }}
        aria-labelledby="unauthorized-title"
      >
        <span className="unauthorized-badge">Acesso restrito</span>

        <div className="unauthorized-icon" aria-hidden>
          <ShieldAlert size={30} strokeWidth={1.75} />
        </div>

        <h1 id="unauthorized-title" className="unauthorized-title">
          Acesso negado
        </h1>

        <p className="unauthorized-message">
          Você não possui permissão para acessar esta área. Se acredita que isso é um
          engano, peça ao administrador para revisar seus papéis e grupos.
        </p>

        {fromPath ? (
          <code className="unauthorized-route" title="Rota solicitada">
            {fromPath}
          </code>
        ) : null}

        <p className="unauthorized-hint">
          Use os aplicativos liberados no menu lateral ou abra <strong>Apps</strong> na
          barra para ver o que está disponível para você.
        </p>

        <div className="unauthorized-actions">
          <button
            type="button"
            className="unauthorized-btn unauthorized-btn--primary"
            onClick={() => navigate("/")}
          >
            <Home size={18} aria-hidden />
            Ir para o início
          </button>

          <button
            type="button"
            className="unauthorized-btn unauthorized-btn--secondary"
            onClick={() => navigate("/profile")}
          >
            <UserCircle size={18} aria-hidden />
            Meu perfil
          </button>

          <button
            type="button"
            className="unauthorized-btn unauthorized-btn--secondary"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft size={18} aria-hidden />
            Voltar
          </button>
        </div>
      </motion.article>
    </div>
  );
};
