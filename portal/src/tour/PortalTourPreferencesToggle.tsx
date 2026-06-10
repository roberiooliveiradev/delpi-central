import { useEffect, useState } from "react";
import {
  getPortalTourAnimationsEnabled,
  setPortalTourAnimationsEnabled,
} from "./portalTourPreferences";

export function PortalTourPreferencesToggle() {
  const [enabled, setEnabled] = useState(() => getPortalTourAnimationsEnabled());

  useEffect(() => {
    const onChange = () => setEnabled(getPortalTourAnimationsEnabled());
    window.addEventListener("DELPI_PORTAL_TOUR_PREFERENCES_CHANGED", onChange);
    return () =>
      window.removeEventListener("DELPI_PORTAL_TOUR_PREFERENCES_CHANGED", onChange);
  }, []);

  return (
    <label className="portal-tour-preferences-toggle">
      <span className="portal-tour-preferences-toggle__control">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(event) => {
            const next = event.target.checked;
            setEnabled(next);
            setPortalTourAnimationsEnabled(next);
          }}
        />
      </span>
      <span className="portal-tour-preferences-toggle__text">
        <strong>Animações do tour</strong>
        <span>Confete, destaques e barra de XP durante a exploração.</span>
      </span>
    </label>
  );
}
