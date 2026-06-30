import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { fetchMeProfile, type MeProfile } from "../api/meApi";
import {
  canSubmitEffectivenessReview,
  canValidateEffectivenessReview,
  canWriteActionPlans,
} from "../utils/pacPermissions";

type PacPermissionsContextValue = {
  profile: MeProfile | null;
  loading: boolean;
  canWrite: boolean;
  canSubmitEffectiveness: boolean;
  canValidateEffectiveness: boolean;
};

const PacPermissionsContext = createContext<PacPermissionsContextValue | null>(null);

export function PacPermissionsProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<MeProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadProfile() {
      setLoading(true);
      try {
        const nextProfile = await fetchMeProfile();
        if (active) {
          setProfile(nextProfile);
        }
      } catch {
        if (active) {
          setProfile(null);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<PacPermissionsContextValue>(
    () => ({
      profile,
      loading,
      canWrite: canWriteActionPlans(profile),
      canSubmitEffectiveness: canSubmitEffectivenessReview(profile),
      canValidateEffectiveness: canValidateEffectivenessReview(profile),
    }),
    [profile, loading],
  );

  return (
    <PacPermissionsContext.Provider value={value}>
      {children}
    </PacPermissionsContext.Provider>
  );
}

// Hook exportado junto ao provider (padrão React Context).
// eslint-disable-next-line react-refresh/only-export-components
export function usePacPermissions(): PacPermissionsContextValue {
  const context = useContext(PacPermissionsContext);
  if (!context) {
    throw new Error("usePacPermissions deve ser usado dentro de PacPermissionsProvider.");
  }
  return context;
}
