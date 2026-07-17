import { RefreshCw } from "lucide-react";
import { useState } from "react";

import type {
  DataQueryInsertOperation,
  DataQueryMutationAction,
  DataQueryPreview,
} from "../domain/dataQueryTypes";
import {
  DataPrepareRibbonAddColumnPanel,
  DataPrepareRibbonHomePanel,
  DataPrepareRibbonTransformPanel,
} from "./DataPrepareRibbonPanels";

type Tab = "home" | "transform" | "addColumn";

const TABS: ReadonlyArray<readonly [Tab, string]> = [
  ["home", "Página Inicial"],
  ["transform", "Transformar"],
  ["addColumn", "Adicionar coluna"],
];

export function DataPrepareRibbon({
  selectedColumnKey,
  selectedStepName,
  preview,
  loading,
  onMutate,
  onRefresh,
  availableQueries = [],
}: {
  selectedColumnKey: string | null;
  selectedStepName: string | null;
  preview: DataQueryPreview | null;
  loading: boolean;
  onMutate: (action: DataQueryMutationAction) => void;
  onRefresh: () => void;
  availableQueries?: string[];
}) {
  const [tab, setTab] = useState<Tab>("home");
  const insert = (
    stepName: string,
    operation: DataQueryInsertOperation,
    arguments_: Record<string, unknown>,
  ) =>
    onMutate({
      type: "insert_step",
      afterStepName: selectedStepName,
      stepName,
      operation,
      arguments: arguments_,
    });

  return (
    <section className="td-data-pq__ribbon" aria-label="Transformações M">
      <div className="td-data-pq__ribbon-tabs" role="tablist" aria-label="Faixa de opções">
        {TABS.map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-label={id === "home" ? "Início da consulta" : label}
            aria-selected={tab === id}
            aria-controls="td-m-ribbon-panel"
            className={
              tab === id
                ? "td-data-pq__ribbon-tab td-data-pq__ribbon-tab--active"
                : "td-data-pq__ribbon-tab"
            }
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <div
        id="td-m-ribbon-panel"
        className="td-data-pq__ribbon-actions"
        role="tabpanel"
      >
        <div className="td-data-pq__ribbon-primary">
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            disabled={loading}
            onClick={onRefresh}
          >
            <RefreshCw size={16} aria-hidden /> Atualizar
          </button>
        </div>
        {tab === "home" ? (
          <DataPrepareRibbonHomePanel
            selectedColumnKey={selectedColumnKey}
            preview={preview}
            availableQueries={availableQueries}
            insert={insert}
          />
        ) : null}
        {tab === "transform" ? (
          <DataPrepareRibbonTransformPanel
            selectedColumnKey={selectedColumnKey}
            preview={preview}
            insert={insert}
          />
        ) : null}
        {tab === "addColumn" ? (
          <DataPrepareRibbonAddColumnPanel
            selectedColumnKey={selectedColumnKey}
            preview={preview}
            insert={insert}
          />
        ) : null}
      </div>
    </section>
  );
}
