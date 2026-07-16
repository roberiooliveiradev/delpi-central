import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";

import type { DataSourceDuplicatePolicy } from "@delpi/tv-dashboard-presentation";

import { Modal } from "../components/ui/Modal";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

type ChoiceResult = DataSourceDuplicatePolicy | null;

type DataSourceDuplicateChoiceContextValue = {
  chooseDataSourceDuplicatePolicy: () => Promise<ChoiceResult>;
};

const DataSourceDuplicateChoiceContext =
  createContext<DataSourceDuplicateChoiceContextValue | null>(null);

const H = TV_DASHBOARD_HELP_TOOLTIPS.data.duplicateSourceChoice;

export function DataSourceDuplicateChoiceProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const resolverRef = useRef<((value: ChoiceResult) => void) | null>(null);

  const chooseDataSourceDuplicatePolicy = useCallback((): Promise<ChoiceResult> => {
    return new Promise((resolve) => {
      resolverRef.current = resolve;
      setOpen(true);
    });
  }, []);

  const finish = (value: ChoiceResult) => {
    setOpen(false);
    resolverRef.current?.(value);
    resolverRef.current = null;
  };

  return (
    <DataSourceDuplicateChoiceContext.Provider value={{ chooseDataSourceDuplicatePolicy }}>
      {children}
      <Modal open={open} title={H.title} onClose={() => finish(null)} className="td-modal--confirm">
        <p className="td-deck-inspector__meta">{H.message}</p>
        <div className="td-modal-actions td-modal-actions--stack">
          <button type="button" className="td-btn td-btn--primary" onClick={() => finish("share_source")}>
            {H.shareLabel}
          </button>
          <button type="button" className="td-btn" onClick={() => finish("clone_source")}>
            {H.cloneLabel}
          </button>
          <button type="button" className="td-btn td-btn--ghost" onClick={() => finish(null)}>
            {H.cancelLabel}
          </button>
        </div>
      </Modal>
    </DataSourceDuplicateChoiceContext.Provider>
  );
}

export function useDataSourceDuplicateChoice() {
  const context = useContext(DataSourceDuplicateChoiceContext);
  if (!context) {
    throw new Error(
      "useDataSourceDuplicateChoice deve ser usado dentro de DataSourceDuplicateChoiceProvider",
    );
  }
  return context.chooseDataSourceDuplicatePolicy;
}

export function useOptionalDataSourceDuplicateChoice() {
  return useContext(DataSourceDuplicateChoiceContext)?.chooseDataSourceDuplicatePolicy ?? null;
}
