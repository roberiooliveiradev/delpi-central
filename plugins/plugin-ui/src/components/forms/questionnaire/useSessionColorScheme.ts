import { useCallback, useEffect, useRef, useState } from "react";

export type SessionColorScheme = "light" | "dark";

export type SessionColorSchemeState = {
  scheme: SessionColorScheme;
  /** Alterna claro/escuro apenas na visita atual; após o primeiro toggle a escolha deixa de seguir o aparelho. */
  toggle: () => void;
  /** `true` depois da primeira troca manual nesta visita. */
  userChosen: boolean;
};

const DARK_MEDIA_QUERY = "(prefers-color-scheme: dark)";

function resolveDeviceColorScheme(): SessionColorScheme {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return "light";
  }
  return window.matchMedia(DARK_MEDIA_QUERY).matches ? "dark" : "light";
}

/**
 * Tema claro/escuro por visita: valor inicial e mudanças vêm do aparelho
 * (`prefers-color-scheme`) até o primeiro `toggle()`; a partir daí a escolha
 * manual vale até o componente ser desmontado. Não lê nem grava storage e
 * não altera `<html>`/`document`.
 */
export function useSessionColorScheme(): SessionColorSchemeState {
  const [scheme, setScheme] = useState<SessionColorScheme>(resolveDeviceColorScheme);
  const [userChosen, setUserChosen] = useState(false);
  const userChosenRef = useRef(false);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const media = window.matchMedia(DARK_MEDIA_QUERY);
    const onChange = (event: MediaQueryListEvent) => {
      if (userChosenRef.current) return;
      setScheme(event.matches ? "dark" : "light");
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  const toggle = useCallback(() => {
    userChosenRef.current = true;
    setUserChosen(true);
    setScheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  return { scheme, toggle, userChosen };
}
