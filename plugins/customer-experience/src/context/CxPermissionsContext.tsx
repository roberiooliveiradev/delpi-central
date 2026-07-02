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
  canManageForms,
  canManageParticipants,
  canReadForms,
  canReadParticipants,
  canWriteForms,
  canWriteParticipants,
} from "../utils/cxPermissions";

type CxPermissionsContextValue = {
  profile: MeProfile | null;
  loading: boolean;
  canReadParticipants: boolean;
  canWriteParticipants: boolean;
  canManageParticipants: boolean;
  canReadForms: boolean;
  canWriteForms: boolean;
  canManageForms: boolean;
};

const CxPermissionsContext = createContext<CxPermissionsContextValue | null>(null);

export function CxPermissionsProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<MeProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadProfile() {
      setLoading(true);
      try {
        const nextProfile = await fetchMeProfile();
        if (active) setProfile(nextProfile);
      } catch {
        if (active) setProfile(null);
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadProfile();

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<CxPermissionsContextValue>(
    () => ({
      profile,
      loading,
      canReadParticipants: canReadParticipants(profile),
      canWriteParticipants: canWriteParticipants(profile),
      canManageParticipants: canManageParticipants(profile),
      canReadForms: canReadForms(profile),
      canWriteForms: canWriteForms(profile),
      canManageForms: canManageForms(profile),
    }),
    [profile, loading],
  );

  return (
    <CxPermissionsContext.Provider value={value}>{children}</CxPermissionsContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useCxPermissions(): CxPermissionsContextValue {
  const context = useContext(CxPermissionsContext);
  if (!context) {
    throw new Error("useCxPermissions deve ser usado dentro de CxPermissionsProvider.");
  }
  return context;
}
