// src/components/AppLauncher.tsx


import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";

interface Props {
  onClose: () => void;
}

export const AppLauncher = ({ onClose }: Props) => {
  const { apps } = useContext(AuthContext);
  const navigate = useNavigate();

  return (
    <div className="launcher-overlay" onClick={onClose}>
      <div
        className="launcher-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ marginBottom: 20 }}>Aplicações</h3>

        <div className="launcher-grid">
          {apps.map((app) => (
            <div
              key={app.id}
              className="launcher-card"
              onClick={() => {
                navigate(app.basePath);
                onClose();
              }}
            >
              <div className="launcher-icon">
                {app.name.charAt(0).toUpperCase()}
              </div>
              <span>{app.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
