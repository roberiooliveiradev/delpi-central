import { useEffect, useState } from "react";
import {
  SI_LAYOUT_BREAKPOINT,
  siMaxWidthQuery,
} from "../shared/strategicIndicatorsLayout";

export function useSiPhoneViewport(): boolean {
  const [isPhone, setIsPhone] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }
    return window.matchMedia(siMaxWidthQuery(SI_LAYOUT_BREAKPOINT.phone)).matches;
  });

  useEffect(() => {
    const media = window.matchMedia(siMaxWidthQuery(SI_LAYOUT_BREAKPOINT.phone));
    const sync = () => setIsPhone(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  return isPhone;
}
