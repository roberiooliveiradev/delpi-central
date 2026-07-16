import { FormSelectControl, HintAction, NativeTextControl } from "@delpi/plugin-ui/index";
import type {
  DataTransformAgg,
  DataTransformCmp,
  DataTransformStep,
} from "@delpi/tv-dashboard-presentation";
import {
  ArrowDownAZ,
  Columns3,
  Filter,
  FunctionSquare,
  GitMerge,
  Layers2,
  RefreshCw,
  Replace,
  Sparkles,
  Type,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";

const H = TV_DASHBOARD_HELP_TOOLTIPS.dataPrepare;

export type RibbonTab = "home" | "transform" | "addColumn" | "combine";

export type TransformAction =
  | "rename"
  | "filter"
  | "replace"
  | "sort"
  | "keepRows"
  | "removeRows"
  | "changeType"
  | "fillDown";

type AddColumnAction = "custom" | "fx" | "groupBy" | "pivot" | "unpivot";

type CombineAction = "merge";

/** Abre formulário de ação a partir do menu de contexto. */
export type DataPrepareRibbonOpenRequest =
  | { tab: "home"; showSelect?: boolean }
  | { tab: "transform"; action: TransformAction }
  | { tab: "addColumn"; action: Exclude<AddColumnAction, "fx"> }
  | { tab: "combine"; action: CombineAction };

const CMP_OPTIONS: Array<{ value: DataTransformCmp; label: string }> = [
  { value: "eq", label: "igual a" },
  { value: "neq", label: "diferente de" },
  { value: "gt", label: "maior que" },
  { value: "lt", label: "menor que" },
  { value: "contains", label: "contém" },
  { value: "startsWith", label: "começa com" },
  { value: "notNull", label: "não nulo" },
];

const AGG_OPTIONS: Array<{ value: DataTransformAgg; label: string }> = [
  { value: "sum", label: "Soma" },
  { value: "avg", label: "Média" },
  { value: "min", label: "Mín" },
  { value: "max", label: "Máx" },
  { value: "count", label: "Contagem" },
  { value: "first", label: "Primeiro" },
];

function RibbonHintButton({
  hint,
  label,
  active = false,
  disabled,
  onClick,
  children,
}: {
  hint: string;
  label: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
  children?: ReactNode;
}) {
  return (
    <HintAction hint={hint} ariaLabel={`Ajuda: ${label}`} placement="bottom">
      <button
        type="button"
        className={
          active
            ? "td-data-pq__ribbon-action td-data-pq__ribbon-action--active"
            : "td-data-pq__ribbon-action"
        }
        disabled={disabled}
        onClick={onClick}
        aria-label={label}
      >
        {children}
        {label}
      </button>
    </HintAction>
  );
}

type Props = {
  tab: RibbonTab;
  onTabChange: (tab: RibbonTab) => void;
  columnOptions: Array<{ value: string; label: string }>;
  activeColumn: string;
  onActiveColumnChange: (column: string) => void;
  siblingOptions: Array<{ value: string; label: string }>;
  previewLoading: boolean;
  hasPreset: boolean;
  onRefresh: () => void;
  onAddStep: (step: DataTransformStep) => void;
  onStartFxColumn: () => void;
  onApplyPreset: () => void;
  /** Token + pedido para abrir ação (menu de contexto). */
  openRequestToken?: number;
  openRequest?: DataPrepareRibbonOpenRequest | null;
};

/**
 * Ribbon estilo Power Query: abas → botões de ação → formulário só da ação ativa.
 */
export function DataPrepareRibbon({
  tab,
  onTabChange,
  columnOptions,
  activeColumn,
  onActiveColumnChange,
  siblingOptions,
  previewLoading,
  hasPreset,
  onRefresh,
  onAddStep,
  onStartFxColumn,
  onApplyPreset,
  openRequestToken = 0,
  openRequest = null,
}: Props) {
  const [transformAction, setTransformAction] = useState<TransformAction | null>(null);
  const [addAction, setAddAction] = useState<AddColumnAction | null>(null);
  const [combineAction, setCombineAction] = useState<CombineAction | null>(null);

  const [renameTo, setRenameTo] = useState("");
  const [filterCmp, setFilterCmp] = useState<DataTransformCmp>("eq");
  const [filterValue, setFilterValue] = useState("");
  const [replaceFind, setReplaceFind] = useState("");
  const [replaceWith, setReplaceWith] = useState("");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [rowCount, setRowCount] = useState("10");
  const [rowFrom, setRowFrom] = useState<"top" | "bottom">("top");
  const [typeTo, setTypeTo] = useState<"number" | "string">("number");
  const [addName, setAddName] = useState("");
  const [addExpr, setAddExpr] = useState("");
  const [groupKeys, setGroupKeys] = useState("");
  const [groupAggCol, setGroupAggCol] = useState("");
  const [groupAggFn, setGroupAggFn] = useState<DataTransformAgg>("sum");
  const [groupAggAs, setGroupAggAs] = useState("");
  const [pivotCol, setPivotCol] = useState("");
  const [pivotValue, setPivotValue] = useState("");
  const [unpivotCols, setUnpivotCols] = useState("");
  const [mergeSource, setMergeSource] = useState("");
  const [mergeLeft, setMergeLeft] = useState("");
  const [mergeRight, setMergeRight] = useState("");
  const [selectCols, setSelectCols] = useState("");
  const [showSelectForm, setShowSelectForm] = useState(false);

  useEffect(() => {
    setTransformAction(null);
    setAddAction(null);
    setCombineAction(null);
    setShowSelectForm(false);
  }, [tab]);

  useEffect(() => {
    if (!openRequestToken || !openRequest) return;
    if (openRequest.tab === "home") {
      setShowSelectForm(Boolean(openRequest.showSelect));
      setTransformAction(null);
      setAddAction(null);
      setCombineAction(null);
      return;
    }
    if (openRequest.tab === "transform") {
      setTransformAction(openRequest.action);
      setAddAction(null);
      setCombineAction(null);
      setShowSelectForm(false);
      return;
    }
    if (openRequest.tab === "addColumn") {
      setAddAction(openRequest.action);
      setTransformAction(null);
      setCombineAction(null);
      setShowSelectForm(false);
      return;
    }
    setCombineAction(openRequest.action);
    setTransformAction(null);
    setAddAction(null);
    setShowSelectForm(false);
  }, [openRequestToken, openRequest]);

  useEffect(() => {
    if (activeColumn && !groupAggCol) setGroupAggCol(activeColumn);
    if (activeColumn && !pivotCol) setPivotCol(activeColumn);
    if (activeColumn && !mergeLeft) setMergeLeft(activeColumn);
  }, [activeColumn, groupAggCol, pivotCol, mergeLeft]);

  const col = activeColumn.trim();
  const colSelect = (
    <HintAction hint={H.columnHeader} ariaLabel="Ajuda: coluna ativa" placement="bottom">
      <div className="td-data-pq__ribbon-hint-wrap">
        <FormSelectControl
          id="td-pq-active-col"
          ariaLabel="Coluna ativa"
          value={activeColumn}
          onChange={onActiveColumnChange}
          options={[{ value: "", label: "Coluna (ou clique no grid)…" }, ...columnOptions]}
        />
      </div>
    </HintAction>
  );

  const applyAndClear = (step: DataTransformStep) => {
    onAddStep(step);
    setTransformAction(null);
    setAddAction(null);
    setCombineAction(null);
  };

  const tabHints: Record<RibbonTab, string> = {
    home: H.tabHome,
    transform: H.tabTransform,
    addColumn: H.tabAddColumn,
    combine: H.tabCombine,
  };

  return (
    <div className="td-data-pq__ribbon" role="toolbar" aria-label="Transformações" title={H.ribbon}>
      <div className="td-data-pq__ribbon-tabs">
          {(
            [
              ["home", "Página Inicial"],
              ["transform", "Transformar"],
              ["addColumn", "Adicionar coluna"],
              ["combine", "Combinar"],
            ] as const
          ).map(([id, label]) => (
            <HintAction
              key={id}
              hint={tabHints[id]}
              ariaLabel={`Ajuda: ${label}`}
              placement="bottom"
            >
              <button
                type="button"
                className={
                  tab === id
                    ? "td-data-pq__ribbon-tab td-data-pq__ribbon-tab--active"
                    : "td-data-pq__ribbon-tab"
                }
                onClick={() => onTabChange(id)}
              >
                {label}
              </button>
            </HintAction>
          ))}
      </div>

      <div className="td-data-pq__ribbon-actions">
        {tab === "home" ? (
          <>
            <RibbonHintButton
              hint={H.refresh}
              label="Atualizar"
              disabled={previewLoading}
              onClick={onRefresh}
            >
              <RefreshCw size={16} aria-hidden />
            </RibbonHintButton>
            <RibbonHintButton
              hint={H.selectColumns}
              label="Escolher colunas"
              active={showSelectForm}
              onClick={() => setShowSelectForm((open) => !open)}
            >
              <Columns3 size={16} aria-hidden />
            </RibbonHintButton>
            <RibbonHintButton
              hint={H.promoteHeaders}
              label="Cabeçalhos promovidos"
              onClick={() => applyAndClear({ op: "firstRowAsHeader" })}
            />
            {hasPreset ? (
              <RibbonHintButton
                hint={H.routePreset}
                label="Preset da rota"
                onClick={onApplyPreset}
              >
                <Sparkles size={16} aria-hidden />
              </RibbonHintButton>
            ) : null}
          </>
        ) : null}

        {tab === "transform" ? (
          <>
            {(
              [
                ["rename", "Renomear", H.actionRename, null],
                ["filter", "Filtrar", H.actionFilter, "filter"],
                ["replace", "Substituir", H.actionReplace, "replace"],
                ["sort", "Ordenar", H.actionSort, "sort"],
                ["keepRows", "Manter linhas", H.actionKeepRows, null],
                ["removeRows", "Remover linhas", H.actionRemoveRows, null],
                ["changeType", "Tipo", H.actionChangeType, "type"],
                ["fillDown", "Preencher ↓", H.actionFillDown, null],
              ] as const
            ).map(([id, label, hint, icon]) => (
              <RibbonHintButton
                key={id}
                hint={hint}
                label={label}
                active={transformAction === id}
                onClick={() => setTransformAction(id)}
              >
                {icon === "filter" ? <Filter size={14} aria-hidden /> : null}
                {icon === "replace" ? <Replace size={14} aria-hidden /> : null}
                {icon === "sort" ? <ArrowDownAZ size={14} aria-hidden /> : null}
                {icon === "type" ? <Type size={14} aria-hidden /> : null}
              </RibbonHintButton>
            ))}
          </>
        ) : null}

        {tab === "addColumn" ? (
          <>
            {(
              [
                ["custom", "Coluna personalizada", H.actionCustomColumn, "fx"],
                ["fx", "Inserir etapa (fx)", H.actionFx, "fx"],
                ["groupBy", "Agrupar por", H.actionGroupBy, "group"],
                ["pivot", "Pivot", H.actionPivot, null],
                ["unpivot", "Unpivot", H.actionUnpivot, null],
              ] as const
            ).map(([id, label, hint, icon]) => (
              <RibbonHintButton
                key={id}
                hint={hint}
                label={label}
                active={addAction === id}
                onClick={() => {
                  if (id === "fx") {
                    onStartFxColumn();
                    setAddAction(null);
                    return;
                  }
                  setAddAction(id);
                }}
              >
                {icon === "fx" ? <FunctionSquare size={14} aria-hidden /> : null}
                {icon === "group" ? <Layers2 size={14} aria-hidden /> : null}
              </RibbonHintButton>
            ))}
          </>
        ) : null}

        {tab === "combine" ? (
          <RibbonHintButton
            hint={H.actionMerge}
            label="Mesclar consultas"
            active={combineAction === "merge"}
            onClick={() => setCombineAction("merge")}
          >
            <GitMerge size={14} aria-hidden />
          </RibbonHintButton>
        ) : null}
      </div>

      {tab === "home" && showSelectForm ? (
        <div className="td-data-pq__ribbon-form">
          <p className="td-data-pq__ribbon-form-title">Escolher colunas</p>
          <NativeTextControl
            id="td-pq-select-cols"
            className="td-data-pq__ribbon-input td-data-pq__ribbon-input--wide"
            placeholder="col1, col2, col3"
            value={selectCols}
            onChange={setSelectCols}
            aria-label="Colunas a manter"
          />
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={!selectCols.trim()}
            onClick={() => {
              const columns = selectCols
                .split(",")
                .map((item) => item.trim())
                .filter(Boolean);
              if (!columns.length) return;
              applyAndClear({ op: "select", columns });
              setSelectCols("");
              setShowSelectForm(false);
            }}
          >
            Aplicar
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => setShowSelectForm(false)}
          >
            Cancelar
          </button>
        </div>
      ) : null}

      {tab === "transform" && transformAction ? (
        <div className="td-data-pq__ribbon-form">
          <p className="td-data-pq__ribbon-form-title">
            {transformAction === "rename" && "Renomear coluna"}
            {transformAction === "filter" && "Filtrar linhas"}
            {transformAction === "replace" && "Substituir valores"}
            {transformAction === "sort" && "Ordenar"}
            {transformAction === "keepRows" && "Manter linhas"}
            {transformAction === "removeRows" && "Remover linhas"}
            {transformAction === "changeType" && "Alterar tipo"}
            {transformAction === "fillDown" && "Preencher abaixo"}
          </p>
          {["rename", "filter", "replace", "sort", "changeType", "fillDown"].includes(
            transformAction,
          )
            ? colSelect
            : null}
          {transformAction === "rename" ? (
            <>
              <NativeTextControl
                id="td-pq-rename-to"
                className="td-data-pq__ribbon-input"
                placeholder="Novo nome"
                value={renameTo}
                onChange={setRenameTo}
              />
              <button
                type="button"
                className="td-btn td-btn--sm"
                disabled={!col || !renameTo.trim()}
                onClick={() => {
                  applyAndClear({ op: "rename", from: col, to: renameTo.trim() });
                  setRenameTo("");
                }}
              >
                Aplicar
              </button>
            </>
          ) : null}
          {transformAction === "filter" ? (
            <>
              <FormSelectControl
                id="td-pq-filter-cmp"
                ariaLabel="Comparação"
                value={filterCmp}
                onChange={(value) => setFilterCmp(value as DataTransformCmp)}
                options={CMP_OPTIONS}
              />
              {filterCmp !== "notNull" ? (
                <NativeTextControl
                  id="td-pq-filter-value"
                  className="td-data-pq__ribbon-input"
                  placeholder="Valor"
                  value={filterValue}
                  onChange={setFilterValue}
                />
              ) : null}
              <button
                type="button"
                className="td-btn td-btn--sm"
                disabled={!col}
                onClick={() => {
                  applyAndClear({
                    op: "filter",
                    column: col,
                    cmp: filterCmp,
                    ...(filterCmp === "notNull" ? {} : { value: filterValue }),
                  });
                  setFilterValue("");
                }}
              >
                Aplicar
              </button>
            </>
          ) : null}
          {transformAction === "replace" ? (
            <>
              <NativeTextControl
                id="td-pq-replace-find"
                className="td-data-pq__ribbon-input"
                placeholder="Localizar"
                value={replaceFind}
                onChange={setReplaceFind}
              />
              <NativeTextControl
                id="td-pq-replace-with"
                className="td-data-pq__ribbon-input"
                placeholder="Substituir por"
                value={replaceWith}
                onChange={setReplaceWith}
              />
              <button
                type="button"
                className="td-btn td-btn--sm"
                disabled={!col}
                onClick={() => {
                  applyAndClear({
                    op: "replace",
                    column: col,
                    find: replaceFind,
                    replaceWith,
                  });
                  setReplaceFind("");
                  setReplaceWith("");
                }}
              >
                Aplicar
              </button>
            </>
          ) : null}
          {transformAction === "sort" ? (
            <>
              <FormSelectControl
                id="td-pq-sort-dir"
                ariaLabel="Direção"
                value={sortDir}
                onChange={(value) => setSortDir(value === "desc" ? "desc" : "asc")}
                options={[
                  { value: "asc", label: "A→Z" },
                  { value: "desc", label: "Z→A" },
                ]}
              />
              <button
                type="button"
                className="td-btn td-btn--sm"
                disabled={!col}
                onClick={() => applyAndClear({ op: "sort", column: col, direction: sortDir })}
              >
                Aplicar
              </button>
            </>
          ) : null}
          {transformAction === "keepRows" || transformAction === "removeRows" ? (
            <>
              <NativeTextControl
                id="td-pq-row-count"
                className="td-data-pq__ribbon-input"
                placeholder="N linhas"
                value={rowCount}
                onChange={setRowCount}
              />
              <FormSelectControl
                id="td-pq-row-from"
                ariaLabel="Topo ou base"
                value={rowFrom}
                onChange={(value) => setRowFrom(value === "bottom" ? "bottom" : "top")}
                options={[
                  { value: "top", label: "Do topo" },
                  { value: "bottom", label: "Da base" },
                ]}
              />
              <button
                type="button"
                className="td-btn td-btn--sm"
                onClick={() => {
                  const count = Math.max(0, Math.floor(Number(rowCount) || 0));
                  if (!count) return;
                  applyAndClear({
                    op: transformAction,
                    count,
                    from: rowFrom,
                  });
                }}
              >
                Aplicar
              </button>
            </>
          ) : null}
          {transformAction === "changeType" ? (
            <>
              <FormSelectControl
                id="td-pq-type-to"
                ariaLabel="Tipo destino"
                value={typeTo}
                onChange={(value) => setTypeTo(value === "string" ? "string" : "number")}
                options={[
                  { value: "number", label: "Número" },
                  { value: "string", label: "Texto" },
                ]}
              />
              <button
                type="button"
                className="td-btn td-btn--sm"
                disabled={!col}
                onClick={() =>
                  applyAndClear({ op: "changeType", column: col, to: typeTo })
                }
              >
                Aplicar
              </button>
            </>
          ) : null}
          {transformAction === "fillDown" ? (
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={!col}
              onClick={() => applyAndClear({ op: "fillDown", column: col })}
            >
              Aplicar
            </button>
          ) : null}
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => setTransformAction(null)}
          >
            Cancelar
          </button>
        </div>
      ) : null}

      {tab === "addColumn" && addAction === "custom" ? (
        <div className="td-data-pq__ribbon-form">
          <p className="td-data-pq__ribbon-form-title">Coluna personalizada</p>
          <NativeTextControl
            id="td-pq-add-name"
            className="td-data-pq__ribbon-input"
            placeholder="Nome"
            value={addName}
            onChange={setAddName}
          />
          <NativeTextControl
            id="td-pq-add-expr"
            className="td-data-pq__ribbon-input td-data-pq__ribbon-input--wide"
            placeholder="ex.: if(oee >= meta, 1, 0)"
            value={addExpr}
            onChange={setAddExpr}
          />
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={!addName.trim() || !addExpr.trim()}
            onClick={() => {
              applyAndClear({
                op: "addColumn",
                name: addName.trim(),
                expr: addExpr.trim(),
              });
              setAddName("");
              setAddExpr("");
            }}
          >
            Aplicar
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => setAddAction(null)}
          >
            Cancelar
          </button>
        </div>
      ) : null}

      {tab === "addColumn" && addAction === "groupBy" ? (
        <div className="td-data-pq__ribbon-form">
          <p className="td-data-pq__ribbon-form-title">Agrupar por</p>
          <NativeTextControl
            id="td-pq-group-keys"
            className="td-data-pq__ribbon-input"
            placeholder="chaves (a, b)"
            value={groupKeys}
            onChange={setGroupKeys}
          />
          <FormSelectControl
            id="td-pq-group-agg-col"
            ariaLabel="Coluna agregação"
            value={groupAggCol}
            onChange={setGroupAggCol}
            options={[{ value: "", label: "Agregar…" }, ...columnOptions]}
          />
          <FormSelectControl
            id="td-pq-group-agg-fn"
            ariaLabel="Função"
            value={groupAggFn}
            onChange={(value) => setGroupAggFn(value as DataTransformAgg)}
            options={AGG_OPTIONS}
          />
          <NativeTextControl
            id="td-pq-group-agg-as"
            className="td-data-pq__ribbon-input"
            placeholder="Nome resultado"
            value={groupAggAs}
            onChange={setGroupAggAs}
          />
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={!groupKeys.trim() || !groupAggCol.trim()}
            onClick={() => {
              const keys = groupKeys
                .split(",")
                .map((item) => item.trim())
                .filter(Boolean);
              if (!keys.length || !groupAggCol.trim()) return;
              const asName = groupAggAs.trim() || `${groupAggCol}_${groupAggFn}`;
              applyAndClear({
                op: "groupBy",
                keys,
                aggregations: [{ column: groupAggCol.trim(), fn: groupAggFn, as: asName }],
              });
              setGroupKeys("");
              setGroupAggAs("");
            }}
          >
            Aplicar
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => setAddAction(null)}
          >
            Cancelar
          </button>
        </div>
      ) : null}

      {tab === "addColumn" && addAction === "pivot" ? (
        <div className="td-data-pq__ribbon-form">
          <p className="td-data-pq__ribbon-form-title">Pivot</p>
          <FormSelectControl
            id="td-pq-pivot-col"
            ariaLabel="Coluna pivot"
            value={pivotCol}
            onChange={setPivotCol}
            options={[{ value: "", label: "Pivot…" }, ...columnOptions]}
          />
          <FormSelectControl
            id="td-pq-pivot-value"
            ariaLabel="Valores"
            value={pivotValue}
            onChange={setPivotValue}
            options={[{ value: "", label: "Valores…" }, ...columnOptions]}
          />
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={!pivotCol.trim() || !pivotValue.trim()}
            onClick={() => {
              applyAndClear({
                op: "pivot",
                column: pivotCol.trim(),
                valueColumn: pivotValue.trim(),
                aggregation: "sum",
              });
              setPivotCol("");
              setPivotValue("");
            }}
          >
            Aplicar
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => setAddAction(null)}
          >
            Cancelar
          </button>
        </div>
      ) : null}

      {tab === "addColumn" && addAction === "unpivot" ? (
        <div className="td-data-pq__ribbon-form">
          <p className="td-data-pq__ribbon-form-title">Unpivot</p>
          <NativeTextControl
            id="td-pq-unpivot"
            className="td-data-pq__ribbon-input td-data-pq__ribbon-input--wide"
            placeholder="colunas (a, b)"
            value={unpivotCols}
            onChange={setUnpivotCols}
          />
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={!unpivotCols.trim()}
            onClick={() => {
              const columns = unpivotCols
                .split(",")
                .map((item) => item.trim())
                .filter(Boolean);
              if (!columns.length) return;
              applyAndClear({ op: "unpivot", columns });
              setUnpivotCols("");
            }}
          >
            Aplicar
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => setAddAction(null)}
          >
            Cancelar
          </button>
        </div>
      ) : null}

      {tab === "combine" && combineAction === "merge" ? (
        <div className="td-data-pq__ribbon-form">
          <p className="td-data-pq__ribbon-form-title">Mesclar consultas</p>
          {!siblingOptions.length ? (
            <span className="td-deck-inspector__meta">Inclua outra fonte no slide.</span>
          ) : (
            <>
              <FormSelectControl
                id="td-pq-merge-source"
                ariaLabel="Consulta"
                value={mergeSource}
                onChange={setMergeSource}
                options={[{ value: "", label: "Consulta…" }, ...siblingOptions]}
              />
              <FormSelectControl
                id="td-pq-merge-left"
                ariaLabel="Chave esquerda"
                value={mergeLeft}
                onChange={setMergeLeft}
                options={[{ value: "", label: "Chave esq…" }, ...columnOptions]}
              />
              <NativeTextControl
                id="td-pq-merge-right"
                className="td-data-pq__ribbon-input"
                placeholder="Chave direita"
                value={mergeRight}
                onChange={setMergeRight}
              />
              <button
                type="button"
                className="td-btn td-btn--sm"
                disabled={!mergeSource.trim() || !mergeLeft.trim() || !mergeRight.trim()}
                onClick={() => {
                  applyAndClear({
                    op: "merge",
                    sourceId: mergeSource.trim(),
                    leftKey: mergeLeft.trim(),
                    rightKey: mergeRight.trim(),
                    join: "left",
                  });
                  setMergeSource("");
                  setMergeRight("");
                }}
              >
                Aplicar
              </button>
            </>
          )}
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => setCombineAction(null)}
          >
            Cancelar
          </button>
        </div>
      ) : null}

      {tab === "transform" && !transformAction ? (
        <p className="td-data-pq__ribbon-hint">
          Escolha uma ação acima. Clique numa coluna do grid para usá-la como contexto.
        </p>
      ) : null}
      {tab === "addColumn" && !addAction ? (
        <p className="td-data-pq__ribbon-hint">
          Escolha uma ação. «Inserir etapa (fx)» foca a barra de fórmulas (como o botão fx do Power
          Query).
        </p>
      ) : null}
    </div>
  );
}
