// src/pages/DelpiHealthPage.tsx

import React, { useState } from "react";
import { useDelpiHealth } from "../hooks/useDelpiHealth";
import "./DelpiHealthPage.css"

export const DelpiHealthPage: React.FC = () => {
  const { data, loading, error } = useDelpiHealth();
  const [lastChecked] = useState(() => new Date());

  const isOnline = data?.status === "online";

  return (
    <div className="delpi-health-page">
      <h1 className="page-title">API DELPI — Health</h1>

      <div className="health-card">
        {loading && (
          <div className="health-loading">
            Verificando status da API DELPI...
          </div>
        )}

        {error && (
          <div className="health-error">
            Erro ao consultar health: {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <div
              className={`health-status ${
                isOnline ? "online" : "offline"
              }`}
            >
              {isOnline ? "🟢 Online" : "🔴 Offline"}
            </div>

            <div className="health-meta">
              Última verificação:{" "}
              {lastChecked.toLocaleTimeString()}
            </div>

            <pre className="health-json">
              {JSON.stringify(data, null, 2)}
            </pre>
          </>
        )}
      </div>
    </div>
  );
};