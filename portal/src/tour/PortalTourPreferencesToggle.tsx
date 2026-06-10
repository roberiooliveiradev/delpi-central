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
      <input
        type="checkbox"
        checked={enabled}
        onChange={(event) => {
          const next = event.target.checked;
          setEnabled(next);
          setPortalTourAnimationsEnabled(next);
        }}
      />
      <span>Animações do tour (confete, destaques e barra de XP)</span>
    </label>
  );
}
