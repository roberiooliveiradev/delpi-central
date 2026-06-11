import { useCallback, useRef } from "react";

/** Rola suavemente até um formulário/painel recém-aberto acima ou abaixo da viewport. */
export function useScrollToRef<T extends HTMLElement>() {
  const ref = useRef<T>(null);

  const scrollToRef = useCallback(() => {
    requestAnimationFrame(() => {
      ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, []);

  return { ref, scrollToRef };
}
