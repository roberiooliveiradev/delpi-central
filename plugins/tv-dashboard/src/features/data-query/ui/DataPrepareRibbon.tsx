import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import { ArrowDownAZ, Filter, RefreshCw, Type } from "lucide-react";
import { useState } from "react";

import type { DataQueryMutationAction, DataQueryPreview } from "../domain/dataQueryTypes";

type Tab = "home" | "transform" | "addColumn";

export function DataPrepareRibbon({
  selectedColumnKey,
  selectedStepName,
  preview,
  loading,
  onMutate,
  onRefresh,
}: {
  selectedColumnKey: string | null;
  selectedStepName: string | null;
  preview: DataQueryPreview | null;
  loading: boolean;
  onMutate: (action: DataQueryMutationAction) => void;
  onRefresh: () => void;
}) {
  const [tab, setTab] = useState<Tab>("home");
  const [value, setValue] = useState("");
  const [renameTo, setRenameTo] = useState("");
  const [direction, setDirection] = useState<"asc" | "desc">("asc");
  const insert = (
    stepName: string,
    operation: string,
    args: Record<string, unknown>,
  ) =>
    onMutate({
      type: "insert_step",
      afterStepName: selectedStepName,
      stepName,
      operation,
      arguments: args,
    });
  const column = selectedColumnKey ?? "";

  return (
    <section className="td-data-pq__ribbon" aria-label="Transformações M">
      <div className="td-data-pq__ribbon-tabs" role="tablist" aria-label="Faixa de opções">
        {(
          [
            ["home", "Página Inicial"],
            ["transform", "Transformar"],
            ["addColumn", "Adicionar coluna"],
          ] as const
        ).map(([id, label]) => (
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
        <button
          type="button"
          className="td-data-pq__ribbon-action"
          disabled={loading}
          onClick={onRefresh}
        >
          <RefreshCw size={16} aria-hidden /> Atualizar
        </button>
        {tab === "home" ? (
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            onClick={() => insert("Cabeçalhos promovidos", "firstRowAsHeader", {})}
          >
            Cabeçalhos promovidos
          </button>
        ) : null}
        {tab === "transform" ? (
          <>
            <FormSelectControl
              id="td-m-selected-column"
              ariaLabel="Coluna ativa"
              value={column}
              onChange={() => undefined}
              options={[
                { value: "", label: "Selecione no grid" },
                ...(preview?.columns ?? []).map((item) => ({
                  value: item.key,
                  label: item.label,
                })),
              ]}
            />
            <FormSelectControl
              id="td-m-sort-direction"
              ariaLabel="Direção"
              value={direction}
              onChange={(next) => setDirection(next === "desc" ? "desc" : "asc")}
              options={[
                { value: "asc", label: "A→Z" },
                { value: "desc", label: "Z→A" },
              ]}
            />
            <button
              type="button"
              className="td-data-pq__ribbon-action"
              disabled={!column}
              onClick={() =>
                insert("Linhas ordenadas", "sort", { column, direction })
              }
            >
              <ArrowDownAZ size={16} aria-hidden /> Ordenar
            </button>
            <NativeTextControl
              id="td-m-filter-value"
              aria-label="Valor do filtro"
              placeholder="Valor do filtro"
              value={value}
              onChange={setValue}
            />
            <button
              type="button"
              className="td-data-pq__ribbon-action"
              disabled={!column}
              onClick={() =>
                insert("Linhas filtradas", "filter", {
                  column,
                  cmp: "eq",
                  value,
                })
              }
            >
              <Filter size={16} aria-hidden /> Filtrar
            </button>
            <NativeTextControl
              id="td-m-rename-column"
              aria-label="Novo nome da coluna"
              placeholder="Novo nome"
              value={renameTo}
              onChange={setRenameTo}
            />
            <button
              type="button"
              className="td-data-pq__ribbon-action"
              disabled={!column || !renameTo.trim()}
              onClick={() =>
                insert("Colunas renomeadas", "rename", {
                  from: column,
                  to: renameTo.trim(),
                })
              }
            >
              Renomear
            </button>
            <button
              type="button"
              className="td-data-pq__ribbon-action"
              disabled={!column}
              onClick={() =>
                insert("Tipo alterado", "changeType", {
                  column,
                  to: "number",
                })
              }
            >
              <Type size={16} aria-hidden /> Número
            </button>
          </>
        ) : null}
        {tab === "addColumn" ? (
          <p className="td-data-pq__ribbon-hint">
            Use a barra fx para editar expressões M existentes. Novas colunas personalizadas entram
            na Fase 5.
          </p>
        ) : null}
      </div>
    </section>
  );
}
