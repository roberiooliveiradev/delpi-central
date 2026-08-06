import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type HomeHeroMetrics = {
  /** null = ainda carregando / indisponível */
  valorAberto: number | null;
  atrasos: number | null;
  followUps: number | null;
  ready: boolean;
};

const EMPTY_METRICS: HomeHeroMetrics = {
  valorAberto: null,
  atrasos: null,
  followUps: null,
  ready: false,
};

type HomeHeroMetricsContextValue = {
  metrics: HomeHeroMetrics;
  setMetrics: (next: HomeHeroMetrics) => void;
  resetMetrics: () => void;
};

const HomeHeroMetricsContext = createContext<HomeHeroMetricsContextValue | null>(null);

export function HomeHeroMetricsProvider({ children }: { children: ReactNode }) {
  const [metrics, setMetricsState] = useState<HomeHeroMetrics>(EMPTY_METRICS);

  const setMetrics = useCallback((next: HomeHeroMetrics) => {
    setMetricsState(next);
  }, []);

  const resetMetrics = useCallback(() => {
    setMetricsState(EMPTY_METRICS);
  }, []);

  const value = useMemo(
    () => ({ metrics, setMetrics, resetMetrics }),
    [metrics, setMetrics, resetMetrics],
  );

  return (
    <HomeHeroMetricsContext.Provider value={value}>{children}</HomeHeroMetricsContext.Provider>
  );
}

export function useHomeHeroMetrics(): HomeHeroMetricsContextValue {
  const ctx = useContext(HomeHeroMetricsContext);
  if (!ctx) {
    throw new Error("useHomeHeroMetrics deve ser usado dentro de HomeHeroMetricsProvider");
  }
  return ctx;
}

export function useHomeHeroMetricsOptional(): HomeHeroMetricsContextValue | null {
  return useContext(HomeHeroMetricsContext);
}
