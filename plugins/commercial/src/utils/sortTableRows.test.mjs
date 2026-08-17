import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  nextTableSortState,
  sortTableRows,
} from "./sortTableRows.ts";

describe("sortTableRows", () => {
  const columns = [
    {
      key: "name",
      header: "Nome",
      sortable: true,
      sortValue: (row) => row.name,
      render: (row) => row.name,
    },
    {
      key: "value",
      header: "Valor",
      sortable: true,
      sortValue: (row) => row.value,
      render: (row) => row.value,
    },
  ];

  const rows = [
    { name: "B", value: 2 },
    { name: "A", value: 10 },
    { name: "C", value: 1 },
  ];

  it("ordena por texto ascendente", () => {
    const sorted = sortTableRows(rows, columns, "name", "asc");
    assert.deepEqual(
      sorted.map((row) => row.name),
      ["A", "B", "C"],
    );
  });

  it("ordena por número descendente", () => {
    const sorted = sortTableRows(rows, columns, "value", "desc");
    assert.deepEqual(
      sorted.map((row) => row.value),
      [10, 2, 1],
    );
  });

  it("nextTableSortState inverte a mesma coluna", () => {
    assert.deepEqual(nextTableSortState("value", "desc", "value"), {
      sortKey: "value",
      sortDirection: "asc",
    });
  });

  it("nextTableSortState usa default em coluna nova", () => {
    assert.deepEqual(nextTableSortState("value", "asc", "name", "desc"), {
      sortKey: "name",
      sortDirection: "desc",
    });
  });
});
