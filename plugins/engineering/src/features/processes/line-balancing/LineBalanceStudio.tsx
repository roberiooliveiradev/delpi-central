/** Mount React do elemento `<delpi-line-balance-studio>` — o Studio é
 * biblioteca independente (`plugins/delpi-line-balance-studio`); o host
 * alimenta `study` e `routingState`, e responde às intenções emitidas
 * pelo elemento (busca de roteiro, contexto, estudo manual, troca de
 * origem). Estado oficial, AuthN/AuthZ, HTTP e cancelamento continuam
 * aqui — nunca dentro do elemento. */

import { useEffect, useRef } from "react";
import { registerLineBalanceStudio, STUDIO_EVENTS } from "@delpi/line-balance-studio/ui";
import type {
  StudioAnalysisState,
  StudioDraftSaveState,
  StudioOfficialOperation,
  StudioRoutingState,
} from "@delpi/line-balance-studio/ui";
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

type StudioElement = HTMLElement & {
  study?: StudioStudyInput;
  routingState?: StudioRoutingState;
  analysisState?: StudioAnalysisState;
  officialOperations?: readonly StudioOfficialOperation[];
  draftSave?: StudioDraftSaveState;
};

type StudioHandlers = {
  onStudyChange?: (study: StudioStudyInput) => void;
  onRoutingSearch?: (productCode: string) => void;
  onRoutingContext?: (context: { branch: string; stage: string }) => void;
  onManualStudy?: (name: string) => void;
  onOriginReset?: () => void;
  onAnalysisRun?: () => void;
  onExport?: (format: "csv" | "xlsx" | "pdf") => void;
  onClearStudy?: () => void;
};

let registered = false;

export function LineBalanceStudioMount({
  study,
  routingState,
  analysisState,
  officialOperations,
  draftSave,
  onStudyChange,
  onRoutingSearch,
  onRoutingContext,
  onManualStudy,
  onOriginReset,
  onAnalysisRun,
  onExport,
  onClearStudy,
}: {
  study: StudioStudyInput | undefined;
  routingState?: StudioRoutingState;
  analysisState?: StudioAnalysisState;
  officialOperations?: readonly StudioOfficialOperation[];
  draftSave?: StudioDraftSaveState;
} & StudioHandlers) {
  const ref = useRef<StudioElement | null>(null);
  const handlersRef = useRef<StudioHandlers>({});
  handlersRef.current = {
    onStudyChange, onRoutingSearch, onRoutingContext, onManualStudy,
    onOriginReset, onAnalysisRun, onExport, onClearStudy,
  };

  useEffect(() => {
    if (!registered) {
      registerLineBalanceStudio();
      registered = true;
    }
  }, []);

  useEffect(() => {
    if (ref.current) ref.current.study = study;
  }, [study]);

  useEffect(() => {
    if (ref.current) ref.current.routingState = routingState;
  }, [routingState]);

  useEffect(() => {
    if (ref.current) ref.current.analysisState = analysisState;
  }, [analysisState]);

  useEffect(() => {
    if (ref.current) ref.current.officialOperations = officialOperations;
  }, [officialOperations]);

  useEffect(() => {
    if (ref.current) ref.current.draftSave = draftSave;
  }, [draftSave]);

  useEffect(() => {
    const element = ref.current;
    if (!element) return undefined;
    const detail = <T,>(event: Event) => (event as CustomEvent<T>).detail;
    const listeners: [string, (event: Event) => void][] = [
      ["study-change", event => {
        const data = detail<{ study?: StudioStudyInput }>(event);
        if (data?.study) handlersRef.current.onStudyChange?.(data.study);
      }],
      [STUDIO_EVENTS.routingSearch, event => {
        const data = detail<{ productCode?: string }>(event);
        if (data?.productCode) handlersRef.current.onRoutingSearch?.(data.productCode);
      }],
      [STUDIO_EVENTS.routingContext, event => {
        const data = detail<{ branch: string; stage: string }>(event);
        handlersRef.current.onRoutingContext?.({ branch: data.branch, stage: data.stage });
      }],
      [STUDIO_EVENTS.manualStudy, event => {
        const data = detail<{ name?: string }>(event);
        handlersRef.current.onManualStudy?.(data?.name?.trim() || "Estudo manual");
      }],
      [STUDIO_EVENTS.originReset, () => handlersRef.current.onOriginReset?.()],
      [STUDIO_EVENTS.analysisRun, () => handlersRef.current.onAnalysisRun?.()],
      [STUDIO_EVENTS.exportRequest, event => {
        const data = detail<{ format?: string }>(event);
        if (data?.format === "csv" || data?.format === "xlsx" || data?.format === "pdf") {
          handlersRef.current.onExport?.(data.format);
        }
      }],
      [STUDIO_EVENTS.clearRequest, () => handlersRef.current.onClearStudy?.()],
    ];
    for (const [type, listener] of listeners) element.addEventListener(type, listener);
    return () => {
      for (const [type, listener] of listeners) element.removeEventListener(type, listener);
    };
  }, []);

  return <delpi-line-balance-studio ref={ref} />;
}
