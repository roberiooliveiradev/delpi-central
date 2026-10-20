import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { ApiError } from "../api/httpClient";
import {
  getViewerContext,
  type ViewerCapabilities,
  type ViewerContext,
} from "../api/viewerContextApi";

type ViewerContextValue = {
  viewer: ViewerContext | null;
  loading: boolean;
  /** HTTP status do erro (403 = sem acesso; 5xx = indisponível). */
  errorStatus: number | null;
  reload: () => void;
};

const ViewerContextContext = createContext<ViewerContextValue | null>(null);

const CAPABILITIES_FALLBACK: ViewerCapabilities = { access: false, manage: false };

export function ViewerContextProvider({ children }: { children: ReactNode }) {
  const [viewer, setViewer] = useState<ViewerContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const requestSeq = useRef(0);

  const fetchViewer = useCallback((seq: number) => {
    const controller = new AbortController();
    void getViewerContext({ signal: controller.signal })
      .then((data) => {
        if (requestSeq.current !== seq) return;
        setViewer(data);
      })
      .catch((err: unknown) => {
        if (requestSeq.current !== seq) return;
        setViewer(null);
        setErrorStatus(err instanceof ApiError ? err.status : 0);
      })
      .finally(() => {
        if (requestSeq.current === seq) setLoading(false);
      });
  }, []);

  const reload = useCallback(() => {
    setLoading(true);
    setErrorStatus(null);
    fetchViewer(++requestSeq.current);
  }, [fetchViewer]);

  useEffect(() => {
    fetchViewer(++requestSeq.current);
  }, [fetchViewer]);

  return (
    <ViewerContextContext.Provider
      value={{ viewer, loading, errorStatus, reload }}
    >
      {children}
    </ViewerContextContext.Provider>
  );
}

export function useViewerContext(): ViewerContextValue {
  const ctx = useContext(ViewerContextContext);
  if (!ctx) {
    return { viewer: null, loading: true, errorStatus: null, reload: () => {} };
  }
  return ctx;
}

export function useViewerCapabilities(): ViewerCapabilities {
  return useViewerContext().viewer?.capabilities ?? CAPABILITIES_FALLBACK;
}
