import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  ArrowDown,
  ArrowDownAZ,
  ArrowUp,
  Braces,
  ChevronsLeft,
  Columns3,
  Copy,
  Eraser,
  Expand,
  Filter,
  FlipVertical2,
  GitBranch,
  GitMerge,
  Group,
  Hash,
  Heading,
  LayoutGrid,
  ListEnd,
  ListStart,
  ListX,
  Replace,
  Rows3,
  ShieldX,
  SplitSquareHorizontal,
  TableProperties,
  TextCursorInput,
  Trash2,
  Type,
  Wand2,
} from "lucide-react";
import { useState } from "react";

import type {
  DataQueryInsertOperation,
  DataQueryPreview,
} from "../domain/dataQueryTypes";

type Insert = (
  stepName: string,
  operation: DataQueryInsertOperation,
  arguments_: Record<string, unknown>,
) => void;

type PanelProps = {
  selectedColumnKey: string | null;
  preview: DataQueryPreview | null;
  insert: Insert;
};

type ColumnType =
  | "any"
  | "text"
  | "number"
  | "logical"
  | "date"
  | "datetime"
  | "duration";

const COLUMN_TYPE_OPTIONS = [
  { value: "text", label: "Texto" },
  { value: "number", label: "Número" },
  { value: "logical", label: "Lógico" },
  { value: "date", label: "Data" },
  { value: "datetime", label: "Data e hora" },
  { value: "duration", label: "Duração" },
  { value: "any", label: "Qualquer" },
];

const COLUMN_FUNCTION_OPTIONS = [
  { value: "trim", label: "Texto: remover espaços" },
  { value: "clean", label: "Texto: limpar controles" },
  { value: "upper", label: "Texto: maiúsculas" },
  { value: "lower", label: "Texto: minúsculas" },
  { value: "proper", label: "Texto: iniciais maiúsculas" },
  { value: "length", label: "Texto: tamanho" },
  { value: "contains", label: "Texto: contém" },
  { value: "before_delimiter", label: "Texto: antes do delimitador" },
  { value: "after_delimiter", label: "Texto: depois do delimitador" },
  { value: "between_delimiters", label: "Texto: entre delimitadores" },
  { value: "abs", label: "Número: absoluto" },
  { value: "round", label: "Número: arredondar" },
  { value: "round_up", label: "Número: arredondar acima" },
  { value: "round_down", label: "Número: arredondar abaixo" },
  { value: "mod", label: "Número: resto" },
  { value: "date_year", label: "Data: ano" },
  { value: "date_month", label: "Data: mês" },
  { value: "date_day", label: "Data: dia" },
  { value: "date_start_of_month", label: "Data: início do mês" },
  { value: "date_end_of_month", label: "Data: fim do mês" },
  { value: "date_add_days", label: "Data: adicionar dias" },
  { value: "date_add_months", label: "Data: adicionar meses" },
  { value: "duration_days", label: "Duração: dias" },
];

function secondaryColumn(preview: DataQueryPreview | null, selected: string): string {
  return preview?.columns.find((item) => item.key !== selected)?.key ?? selected;
}

function functionArguments(
  functionName: string,
  value: string,
  delimiter: string,
  replacement: string,
): unknown[] {
  if (["round", "round_up", "round_down"].includes(functionName)) return [2];
  if (["mod", "date_add_days", "date_add_months"].includes(functionName)) {
    return [Number(value) || 1];
  }
  if (["contains", "before_delimiter", "after_delimiter"].includes(functionName)) {
    return [delimiter];
  }
  return functionName === "between_delimiters" ? [delimiter, replacement] : [];
}

export function DataPrepareRibbonHomePanel({
  selectedColumnKey,
  preview,
  availableQueries,
  insert,
}: PanelProps & { availableQueries: string[] }) {
  const [rowCount, setRowCount] = useState("10");
  const [rowOffset, setRowOffset] = useState("0");
  const column = selectedColumnKey ?? "";
  const secondary = secondaryColumn(preview, column);
  const selectedQuery = availableQueries[0] ?? "";
  return (
    <>
      <section className="td-data-pq__ribbon-group" aria-label="Operações de coluna">
        <h3>Colunas</h3>
        <div className="td-data-pq__ribbon-group-body">
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            aria-label="Promover cabeçalhos"
            onClick={() => insert("Cabeçalhos promovidos", "firstRowAsHeader", {})}
          >
            <Heading size={15} aria-hidden />
            <span>Cabeçalhos</span>
          </button>
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            disabled={!column}
            onClick={() => insert("Colunas selecionadas", "select", { columns: [column] })}
          >
            <Columns3 size={15} aria-hidden />
            <span>Escolher coluna</span>
          </button>
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            disabled={!column}
            onClick={() =>
              insert("Colunas reordenadas", "reorder_columns", { columns: [column] })
            }
          >
            <ChevronsLeft size={15} aria-hidden />
            <span>Mover ao início</span>
          </button>
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            disabled={!column}
            onClick={() =>
              insert("Colunas removidas", "remove_columns", { columns: [column] })
            }
          >
            <Trash2 size={15} aria-hidden />
            <span>Remover coluna</span>
          </button>
        </div>
      </section>
      <section className="td-data-pq__ribbon-group" aria-label="Operações de linha">
        <h3>Linhas</h3>
        <div className="td-data-pq__ribbon-group-body">
          <label className="td-data-pq__ribbon-field">
            <span>Quantidade</span>
            <NativeTextControl
              id="td-m-row-count"
              aria-label="Quantidade de linhas"
              value={rowCount}
              onChange={setRowCount}
            />
          </label>
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            aria-label="Manter primeiras linhas"
            onClick={() =>
              insert("Primeiras linhas", "keepRows", {
                count: Math.max(0, Number(rowCount) || 0),
                fromEnd: false,
              })
            }
          >
            <ListStart size={15} aria-hidden />
            <span>Manter</span>
          </button>
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            aria-label="Remover primeiras linhas"
            onClick={() =>
              insert("Linhas removidas", "removeRows", {
                count: Math.max(0, Number(rowCount) || 0),
                fromEnd: false,
              })
            }
          >
            <ListX size={15} aria-hidden />
            <span>Remover</span>
          </button>
          <label className="td-data-pq__ribbon-field">
            <span>Início</span>
            <NativeTextControl
              id="td-m-row-offset"
              aria-label="Deslocamento inicial"
              value={rowOffset}
              onChange={setRowOffset}
            />
          </label>
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            onClick={() =>
              insert("Intervalo de linhas", "range_rows", {
                offset: Math.max(0, Number(rowOffset) || 0),
                count: Math.max(0, Number(rowCount) || 0),
              })
            }
          >
            <Rows3 size={15} aria-hidden />
            <span>Manter intervalo</span>
          </button>
        </div>
      </section>
      <section className="td-data-pq__ribbon-group" aria-label="Combinar consultas">
        <h3>Combinar</h3>
        <div className="td-data-pq__ribbon-group-body">
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            disabled={!selectedQuery}
            aria-label="Acrescentar consulta"
            onClick={() =>
              insert("Consultas acrescentadas", "append_queries", {
                queries: [selectedQuery],
              })
            }
          >
            <ListEnd size={15} aria-hidden />
            <span>Acrescentar</span>
          </button>
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            disabled={!column || !selectedQuery}
            aria-label="Mesclar consulta"
            onClick={() =>
              insert("Consultas mescladas", "nested_join", {
                query: selectedQuery,
                leftKeys: [column],
                rightKeys: [column],
                newColumn: selectedQuery,
              })
            }
          >
            <GitMerge size={15} aria-hidden />
            <span>Mesclar</span>
          </button>
          <button
            type="button"
            className="td-data-pq__ribbon-action"
            disabled={!column || !secondary}
            aria-label="Expandir coluna"
            onClick={() =>
              insert("Tabela expandida", "expand_table_column", {
                column,
                columns: [secondary],
                newColumnNames: [secondary],
              })
            }
          >
            <Expand size={15} aria-hidden />
            <span>Expandir</span>
          </button>
        </div>
      </section>
    </>
  );
}

export function DataPrepareRibbonTransformPanel({
  selectedColumnKey,
  preview,
  insert,
}: PanelProps) {
  const [value, setValue] = useState("");
  const [renameTo, setRenameTo] = useState("");
  const [replacement, setReplacement] = useState("");
  const [direction, setDirection] = useState<"asc" | "desc">("asc");
  const [columnType, setColumnType] = useState<ColumnType>("number");
  const column = selectedColumnKey ?? "";
  const secondary = secondaryColumn(preview, column);
  return (
    <>
      <section className="td-data-pq__ribbon-group" aria-label="Seleção e ordenação">
        <h3>Seleção e ordem</h3>
        <div className="td-data-pq__ribbon-group-body">
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
        onClick={() => insert("Linhas ordenadas", "sort", { column, direction })}
      >
        <ArrowDownAZ size={15} aria-hidden />
        <span>Ordenar</span>
      </button>
        </div>
      </section>
      <section className="td-data-pq__ribbon-group" aria-label="Filtrar e substituir valores">
        <h3>Valores</h3>
        <div className="td-data-pq__ribbon-group-body">
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
          insert("Linhas filtradas", "filter", { column, cmp: "eq", value })
        }
      >
        <Filter size={15} aria-hidden />
        <span>Filtrar</span>
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
        <TextCursorInput size={15} aria-hidden />
        <span>Renomear</span>
      </button>
      <NativeTextControl
        id="td-m-replacement-value"
        aria-label="Novo valor"
        placeholder="Novo valor"
        value={replacement}
        onChange={setReplacement}
      />
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        aria-label="Substituir valor"
        onClick={() =>
          insert("Valor substituído", "replace", {
            column,
            find: value,
            replaceWith: replacement,
          })
        }
      >
        <Replace size={15} aria-hidden />
        <span>Substituir</span>
      </button>
        </div>
      </section>
      <section className="td-data-pq__ribbon-group" aria-label="Tipos e limpeza">
        <h3>Tipos e limpeza</h3>
        <div className="td-data-pq__ribbon-group-body">
      <FormSelectControl
        id="td-m-column-type"
        ariaLabel="Tipo de destino"
        value={columnType}
        onChange={(next) => setColumnType(next as ColumnType)}
        options={COLUMN_TYPE_OPTIONS}
      />
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() =>
          insert("Tipo alterado", "changeType", { column, to: columnType })
        }
      >
        <Type size={15} aria-hidden />
        <span>Alterar tipo</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        aria-label="Remover duplicatas"
        onClick={() =>
          insert("Duplicatas removidas", "distinct_rows", { columns: [column] })
        }
      >
        <Copy size={15} aria-hidden />
        <span>Sem duplicatas</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() => insert("Preenchido abaixo", "fillDown", { column })}
      >
        <ArrowDown size={15} aria-hidden />
        <span>Preencher abaixo</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() => insert("Preenchido acima", "fill_up", { column })}
      >
        <ArrowUp size={15} aria-hidden />
        <span>Preencher acima</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        onClick={() => insert("Linhas invertidas", "reverse_rows", {})}
      >
        <FlipVertical2 size={15} aria-hidden />
        <span>Inverter linhas</span>
      </button>
        </div>
      </section>
      <section className="td-data-pq__ribbon-group" aria-label="Formato da tabela e erros">
        <h3>Forma e erros</h3>
        <div className="td-data-pq__ribbon-group-body">
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        onClick={() => insert("Tabela transposta", "transpose", {})}
      >
        <TableProperties size={15} aria-hidden />
        <span>Transpor</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() =>
          insert("Erros removidos", "remove_errors", { columns: [column] })
        }
      >
        <Eraser size={15} aria-hidden />
        <span>Remover erros</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() =>
          insert("Erros substituídos", "replace_errors", {
            column,
            replacement,
          })
        }
      >
        <ShieldX size={15} aria-hidden />
        <span>Substituir erros</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !secondary}
        aria-label="Agrupar linhas"
        onClick={() =>
          insert("Linhas agrupadas", "group_rows", {
            keys: [column],
            valueColumn: secondary,
            aggregate: "sum",
            output: `Total ${secondary}`,
          })
        }
      >
        <Group size={15} aria-hidden />
        <span>Agrupar</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !secondary}
        aria-label="Coluna dinâmica"
        onClick={() =>
          insert("Coluna dinâmica", "pivot", {
            values: Array.from(
              new Set(
                (preview?.rows ?? [])
                  .map((row) => row[column])
                  .filter(
                    (item): item is string | number | boolean =>
                      typeof item === "string" ||
                      typeof item === "number" ||
                      typeof item === "boolean",
                  ),
              ),
            ),
            attributeColumn: column,
            valueColumn: secondary,
          })
        }
      >
        <LayoutGrid size={15} aria-hidden />
        <span>Dinâmica</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        aria-label="Anular dinamização"
        onClick={() =>
          insert("Colunas anuladas", "unpivot", {
            columns: [column],
            attributeName: "Atributo",
            valueName: "Valor",
          })
        }
      >
        <Rows3 size={15} aria-hidden />
        <span>Anular dinâmica</span>
      </button>
        </div>
      </section>
    </>
  );
}

export function DataPrepareRibbonAddColumnPanel({
  selectedColumnKey,
  insert,
}: PanelProps) {
  const [newName, setNewName] = useState("");
  const [expression, setExpression] = useState("");
  const [delimiter, setDelimiter] = useState("-");
  const [replacement, setReplacement] = useState("");
  const [columnType] = useState<ColumnType>("number");
  const [columnFunction, setColumnFunction] = useState("trim");
  const column = selectedColumnKey ?? "";
  return (
    <>
      <section className="td-data-pq__ribbon-group" aria-label="Coluna personalizada">
        <h3>Personalizada</h3>
        <div className="td-data-pq__ribbon-group-body">
      <NativeTextControl
        id="td-m-new-column"
        aria-label="Nome da nova coluna"
        placeholder="Nova coluna"
        value={newName}
        onChange={setNewName}
      />
      <NativeTextControl
        id="td-m-custom-expression"
        aria-label="Expressão da coluna personalizada"
        placeholder="Expressão M da coluna"
        value={expression}
        onChange={setExpression}
      />
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!newName.trim() || !expression.trim()}
        aria-label="Coluna personalizada"
        onClick={() =>
          insert("Coluna personalizada", "add_custom_column", {
            newName: newName.trim(),
            expression: expression.trim(),
            type: columnType,
          })
        }
      >
        <Braces size={15} aria-hidden />
        <span>Personalizada</span>
      </button>
        </div>
      </section>
      <section className="td-data-pq__ribbon-group" aria-label="Coluna condicional">
        <h3>Condicional</h3>
        <div className="td-data-pq__ribbon-group-body">
      <NativeTextControl
        id="td-m-conditional-result"
        aria-label="Resultado da condição"
        placeholder="Resultado quando verdadeiro"
        value={replacement}
        onChange={setReplacement}
      />
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !newName.trim()}
        aria-label="Coluna condicional"
        onClick={() =>
          insert("Coluna condicional", "add_conditional_column", {
            column,
            newName: newName.trim(),
            operator: "eq",
            value: expression,
            thenValue: replacement,
            elseValue: null,
          })
        }
      >
        <GitBranch size={15} aria-hidden />
        <span>Condicional</span>
      </button>
        </div>
      </section>
      <section className="td-data-pq__ribbon-group" aria-label="Ações rápidas de coluna">
        <h3>Ações rápidas</h3>
        <div className="td-data-pq__ribbon-group-body">
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !newName.trim()}
        aria-label="Duplicar coluna"
        onClick={() =>
          insert("Coluna duplicada", "duplicate_column", {
            column,
            newName: newName.trim(),
          })
        }
      >
        <Copy size={15} aria-hidden />
        <span>Duplicar</span>
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        onClick={() =>
          insert("Índice adicionado", "add_index", {
            newName: newName.trim() || "Índice",
            initial: 1,
            increment: 1,
          })
        }
      >
        <Hash size={15} aria-hidden />
        <span>Índice</span>
      </button>
        </div>
      </section>
      <section className="td-data-pq__ribbon-group" aria-label="Dividir e transformar coluna">
        <h3>Dividir e transformar</h3>
        <div className="td-data-pq__ribbon-group-body">
      <NativeTextControl
        id="td-m-delimiter"
        aria-label="Delimitador"
        value={delimiter}
        onChange={setDelimiter}
      />
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !delimiter || !newName.trim()}
        aria-label="Dividir coluna"
        onClick={() =>
          insert("Coluna dividida", "split_column", {
            column,
            delimiter,
            newColumns: [`${newName.trim()} 1`, `${newName.trim()} 2`],
          })
        }
      >
        <SplitSquareHorizontal size={15} aria-hidden />
        <span>Dividir</span>
      </button>
      <FormSelectControl
        id="td-m-column-function"
        ariaLabel="Função da coluna"
        value={columnFunction}
        onChange={setColumnFunction}
        options={COLUMN_FUNCTION_OPTIONS}
      />
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() =>
          insert("Coluna transformada", "transform_column", {
            column,
            function: columnFunction,
            arguments: functionArguments(
              columnFunction,
              expression,
              delimiter,
              replacement,
            ),
          })
        }
      >
        <Wand2 size={15} aria-hidden />
        <span>Aplicar função</span>
      </button>
        </div>
      </section>
    </>
  );
}
