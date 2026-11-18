/** Mount React do elemento `<delpi-line-balance-studio>` — o Studio é
 * biblioteca independente (`plugins/delpi-line-balance-studio`); o host
 * alimenta `study` e escuta `study-change` para persistir o rascunho.
 * Estado oficial, AuthN/AuthZ, HTTP e cancelamento continuam aqui —
 * nunca dentro do elemento. */

import { useEffect, useRef } from "react";
import { registerLineBalanceStudio } from "@delpi/line-balance-studio/ui";
import type { StudioStudyInput } from "@delpi/line-balance-studio";

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace React {
    // eslint-disable-next-line @typescript-eslint/no-namespace
    namespace JSX {
      interface IntrinsicElements {
        "delpi-line-balance-studio": React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement>;
      }
    }
  }
}

let registered = false;

export function LineBalanceStudioMount({
  study,
  onStudyChange,
}: {
  study: StudioStudyInput | undefined;
  onStudyChange?: (study: StudioStudyInput) => void;
}) {
  const ref = useRef<HTMLElement | null>(null);
  const changeRef = useRef(onStudyChange);
  changeRef.current = onStudyChange;

  useEffect(() => {
    if (!registered) {
      registerLineBalanceStudio();
      registered = true;
    }
  }, []);

  useEffect(() => {
    const element = ref.current as (HTMLElement & { study?: StudioStudyInput }) | null;
    if (element) element.study = study;
  }, [study]);

  useEffect(() => {
    const element = ref.current;
    if (!element) return undefined;
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ study?: StudioStudyInput }>).detail;
      if (detail?.study) changeRef.current?.(detail.study);
    };
    element.addEventListener("study-change", handler);
    return () => element.removeEventListener("study-change", handler);
  }, []);

  return <delpi-line-balance-studio ref={ref} />;
}
