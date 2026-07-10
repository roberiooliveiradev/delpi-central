import { useContext, useEffect } from "react";

import {
  ComunicadoEditorContext,
  type ComunicadoEditorContextValue,
} from "../components/comunicadoEditorContextCore";

export type ComunicadoRibbonTabRequest = NonNullable<ComunicadoEditorContextValue["ribbonTabRequest"]>;

export function useComunicadoRibbonTabSync(
  setActiveTab: (tab: ComunicadoRibbonTabRequest) => void,
) {
  const ctx = useContext(ComunicadoEditorContext);
  const request = ctx?.ribbonTabRequest ?? null;

  useEffect(() => {
    if (!request || !ctx) return;
    setActiveTab(request);
    ctx.clearRibbonTabRequest();
  }, [ctx, request, setActiveTab]);
}
