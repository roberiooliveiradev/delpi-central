import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import { ArrowDownAZ, Filter, Type } from "lucide-react";
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
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        onClick={() => insert("Cabeçalhos promovidos", "firstRowAsHeader", {})}
      >
        Cabeçalhos promovidos
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() => insert("Colunas selecionadas", "select", { columns: [column] })}
      >
        Escolher coluna
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() =>
          insert("Colunas reordenadas", "reorder_columns", { columns: [column] })
        }
      >
        Mover coluna para início
      </button>
      <NativeTextControl
        id="td-m-row-count"
        aria-label="Quantidade de linhas"
        value={rowCount}
        onChange={setRowCount}
      />
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        onClick={() =>
          insert("Primeiras linhas", "keepRows", {
            count: Math.max(0, Number(rowCount) || 0),
            fromEnd: false,
          })
        }
      >
        Manter linhas
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        onClick={() =>
          insert("Linhas removidas", "removeRows", {
            count: Math.max(0, Number(rowCount) || 0),
            fromEnd: false,
          })
        }
      >
        Remover linhas
      </button>
      <NativeTextControl
        id="td-m-row-offset"
        aria-label="Deslocamento inicial"
        value={rowOffset}
        onChange={setRowOffset}
      />
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
        Manter intervalo
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() =>
          insert("Colunas removidas", "remove_columns", { columns: [column] })
        }
      >
        Remover coluna
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!selectedQuery}
        onClick={() =>
          insert("Consultas acrescentadas", "append_queries", {
            queries: [selectedQuery],
          })
        }
      >
        Acrescentar consulta
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !selectedQuery}
        onClick={() =>
          insert("Consultas mescladas", "nested_join", {
            query: selectedQuery,
            leftKeys: [column],
            rightKeys: [column],
            newColumn: selectedQuery,
          })
        }
      >
        Mesclar consulta
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !secondary}
        onClick={() =>
          insert("Tabela expandida", "expand_table_column", {
            column,
            columns: [secondary],
            newColumnNames: [secondary],
          })
        }
      >
        Expandir coluna
      </button>
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
          insert("Linhas filtradas", "filter", { column, cmp: "eq", value })
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
        onClick={() =>
          insert("Valor substituído", "replace", {
            column,
            find: value,
            replaceWith: replacement,
          })
        }
      >
        Substituir valor
      </button>
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
        <Type size={16} aria-hidden /> Alterar tipo
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() =>
          insert("Duplicatas removidas", "distinct_rows", { columns: [column] })
        }
      >
        Remover duplicatas
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() => insert("Preenchido abaixo", "fillDown", { column })}
      >
        Preencher abaixo
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() => insert("Preenchido acima", "fill_up", { column })}
      >
        Preencher acima
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        onClick={() => insert("Linhas invertidas", "reverse_rows", {})}
      >
        Inverter linhas
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        onClick={() => insert("Tabela transposta", "transpose", {})}
      >
        Transpor
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() =>
          insert("Erros removidos", "remove_errors", { columns: [column] })
        }
      >
        Remover erros
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
        Substituir erros
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !secondary}
        onClick={() =>
          insert("Linhas agrupadas", "group_rows", {
            keys: [column],
            valueColumn: secondary,
            aggregate: "sum",
            output: `Total ${secondary}`,
          })
        }
      >
        Agrupar linhas
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !secondary}
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
        Coluna dinâmica
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column}
        onClick={() =>
          insert("Colunas anuladas", "unpivot", {
            columns: [column],
            attributeName: "Atributo",
            valueName: "Valor",
          })
        }
      >
        Anular dinamização
      </button>
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
        onClick={() =>
          insert("Coluna personalizada", "add_custom_column", {
            newName: newName.trim(),
            expression: expression.trim(),
            type: columnType,
          })
        }
      >
        Coluna personalizada
      </button>
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
        Coluna condicional
      </button>
      <button
        type="button"
        className="td-data-pq__ribbon-action"
        disabled={!column || !newName.trim()}
        onClick={() =>
          insert("Coluna duplicada", "duplicate_column", {
            column,
            newName: newName.trim(),
          })
        }
      >
        Duplicar coluna
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
        Índice
      </button>
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
        onClick={() =>
          insert("Coluna dividida", "split_column", {
            column,
            delimiter,
            newColumns: [`${newName.trim()} 1`, `${newName.trim()} 2`],
          })
        }
      >
        Dividir coluna
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
        Aplicar função
      </button>
    </>
  );
}
