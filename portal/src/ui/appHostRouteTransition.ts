import { useEffect, useRef, useState } from "react";

/**
 * Animação de entrada do AppHost só ao trocar de aplicativo (appId),
 * não a cada deep-link interno (Voltar / sub-rotas) — evita sensação de
 * “abrir o app de novo”.
 */
export function useAppHostRouteTransition(appId: string | null | undefined): string {
  const previousAppIdRef = useRef<string | null | undefined>(undefined);
  const [className, setClassName] = useState("");

  useEffect(() => {
    const nextId = appId ?? null;

    if (previousAppIdRef.current === undefined) {
      previousAppIdRef.current = nextId;
      return;
    }

    if (previousAppIdRef.current === nextId) {
      return;
    }

    previousAppIdRef.current = nextId;
    setClassName("app-host--route-enter");

    const timer = window.setTimeout(() => {
      setClassName("");
    }, 500);

    return () => window.clearTimeout(timer);
  }, [appId]);

  return className;
}
