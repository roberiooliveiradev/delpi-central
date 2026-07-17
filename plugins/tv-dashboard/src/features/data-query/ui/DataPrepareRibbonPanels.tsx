import { FormSelectControl, HelpTooltip, NativeTextControl } from "@delpi/plugin-ui/index";
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
import { useState, type ReactNode } from "react";

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
  selectedColumnKeys?: string[];
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

/** Seção da ribbon com título e balão de explicação (HelpTooltip do kit). */
function RibbonGroup({
  regionLabel,
  title,
  hint,
  children,
}: {
  regionLabel: string;
  title: string;
  hint: string;
  children: ReactNode;
}) {
  return (
    <section className="td-data-pq__ribbon-group" aria-label={regionLabel}>
      <div className="td-data-pq__ribbon-group-head">
        <h3>{title}</h3>
        <HelpTooltip content={hint} ariaLabel={`Ajuda: ${title}`} />
      </div>
      <div className="td-data-pq__ribbon-group-body">{children}</div>
    </section>
  );
}

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
  selectedColumnKeys,
  preview,
  availableQueries,
  insert,
}: PanelProps & { availableQueries: string[] }) {
  const [rowCount, setRowCount] = useState("10");
  const [rowOffset, setRowOffset] = useState("0");
  const column = selectedColumnKey ?? "";
  const columns =
    selectedColumnKeys && selectedColumnKeys.length > 0
      ? selectedColumnKeys
      : column
        ? [column]
        : [];
  const secondary = secondaryColumn(preview, column);
  const selectedQuery = availableQueries[0] ?? "";
  return (
    <>
      <RibbonGroup
        regionLabel="Operações de coluna"
        title="Colunas"
        hint="Promova a primeira linha como cabeçalho e selecione, mova ou remova a coluna ativa do grid."
      >
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
          disabled={columns.length === 0}
          onClick={() => insert("Colunas selecionadas", "select", { columns })}
        >
          <Columns3 size={15} aria-hidden />
          <span>Escolher coluna</span>
        </button>
        <button
          type="button"
          className="td-data-pq__ribbon-action"
          disabled={columns.length === 0}
          onClick={() =>
            insert("Colunas reordenadas", "reorder_columns", { columns })
          }
        >
          <ChevronsLeft size={15} aria-hidden />
          <span>Mover ao início</span>
        </button>
        <button
          type="button"
          className="td-data-pq__ribbon-action"
          disabled={columns.length === 0}
          onClick={() =>
            insert("Colunas removidas", "remove_columns", { columns })
          }
        >
          <Trash2 size={15} aria-hidden />
          <span>Remover coluna</span>
        </button>
      </RibbonGroup>
      <RibbonGroup
        regionLabel="Operações de linha"
        title="Linhas"
        hint="Mantenha ou remova as primeiras linhas, ou selecione um intervalo por posição inicial e quantidade."
      >
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
      </RibbonGroup>
      <RibbonGroup
        regionLabel="Combinar consultas"
        title="Combinar"
        hint="Acrescente linhas de outra consulta, mescle por chave ou expanda uma coluna aninhada."
      >
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
      </RibbonGroup>
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
      <RibbonGroup
        regionLabel="Seleção e ordenação"
        title="Seleção e ordem"
        hint="Escolha a coluna ativa e ordene as linhas de forma crescente ou decrescente."
      >
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
      </RibbonGroup>
      <RibbonGroup
        regionLabel="Filtrar e substituir valores"
        title="Valores"
        hint="Filtre linhas pela coluna ativa, renomeie a coluna ou substitua valores encontrados."
      >
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
      </RibbonGroup>
      <RibbonGroup
        regionLabel="Tipos e limpeza"
        title="Tipos e limpeza"
        hint="Altere o tipo da coluna, remova duplicatas, preencha valores vazios ou inverta a ordem das linhas."
      >
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
      </RibbonGroup>
      <RibbonGroup
        regionLabel="Formato da tabela e erros"
        title="Forma e erros"
        hint="Transponha a tabela, trate erros e agrupe, dinamize ou anule a dinamização das colunas."
      >
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
      </RibbonGroup>
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
      <RibbonGroup
        regionLabel="Coluna personalizada"
        title="Personalizada"
        hint="Crie uma coluna a partir de uma expressão M personalizada."
      >
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
      </RibbonGroup>
      <RibbonGroup
        regionLabel="Coluna condicional"
        title="Condicional"
        hint="Gere uma coluna com valores definidos por uma condição sobre a coluna ativa."
      >
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
      </RibbonGroup>
      <RibbonGroup
        regionLabel="Ações rápidas de coluna"
        title="Ações rápidas"
        hint="Duplique a coluna ativa ou adicione uma coluna de índice sequencial."
      >
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
      </RibbonGroup>
      <RibbonGroup
        regionLabel="Dividir e transformar coluna"
        title="Dividir e transformar"
        hint="Divida a coluna por um delimitador ou aplique funções de texto, número e data."
      >
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
      </RibbonGroup>
    </>
  );
}
