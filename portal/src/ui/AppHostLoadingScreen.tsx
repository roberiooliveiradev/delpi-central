import "./AppHostLoadingScreen.css";
import { Package } from "lucide-react";
import type { ReactNode } from "react";

type Props = {
  appName: string;
  routeLabel?: string | null;
  icon?: ReactNode;
  exiting?: boolean;
};

export const AppHostLoadingScreen = ({
  appName,
  routeLabel,
  icon,
  exiting = false,
}: Props) => {
  const subtitle = routeLabel && routeLabel !== appName ? routeLabel : "Preparando ambiente…";

  return (
    <div
      className={["app-host-loading-screen", exiting ? "is-exiting" : ""]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label={`Carregando ${appName}`}
    >
      <span className="app-host-loading-screen__orb app-host-loading-screen__orb--one" aria-hidden />
      <span className="app-host-loading-screen__orb app-host-loading-screen__orb--two" aria-hidden />

      <div className="app-host-loading-screen__panel">
        <div className="app-host-loading-screen__icon-wrap">
          <span className="app-host-loading-screen__icon-ring" aria-hidden />
          <span className="app-host-loading-screen__icon" aria-hidden>
            {icon ?? <Package size={30} strokeWidth={1.75} />}
          </span>
        </div>

        <div className="app-host-loading-screen__copy">
          <p className="app-host-loading-screen__title">{appName}</p>
          <p className="app-host-loading-screen__subtitle">{subtitle}</p>
        </div>

        <div className="app-host-loading-screen__track" aria-hidden>
          <span className="app-host-loading-screen__bar" />
        </div>

        <div className="app-host-loading-screen__dots" aria-hidden>
          <span className="app-host-loading-screen__dot" />
          <span className="app-host-loading-screen__dot" />
          <span className="app-host-loading-screen__dot" />
        </div>
      </div>
    </div>
  );
};
