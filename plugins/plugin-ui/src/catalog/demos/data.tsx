import { useState } from "react";

import { PUC_PREFIX } from "../../app/bemPrefix";
import {
  ConfigurablePresentationTable,
  ConfigurableTableClassesProvider,
  Pagination,
  paginationBemClasses,
} from "../../components/data";
import type { CatalogEntry } from "../types";

const paginationKit = paginationBemClasses(PUC_PREFIX);

export const dataCatalogEntries: CatalogEntry[] = [
  {
    id: "data.Pagination",
    family: "data",
    exportName: "Pagination",
    title: "Pagination",
    description: "Rodapé de tabela com páginas e salto.",
    docAnchor: "pagination",
    propsSummary: ["page", "pageSize", "total", "onPageChange"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => <PaginationDemo />,
      },
    ],
  },
  {
    id: "data.ConfigurablePresentationTable",
    family: "data",
    exportName: "ConfigurablePresentationTable",
    title: "ConfigurablePresentationTable",
    description: "Tabela configurável (schema-driven) com dados mock.",
    docAnchor: "configurablepresentationtable",
    propsSummary: ["columns", "rows", "preset"],
    demos: [
      {
        id: "default",
        label: "Grid",
        render: () => (
          <ConfigurableTableClassesProvider prefix="delpi-ui-config-table">
            <ConfigurablePresentationTable
              preset="grid"
              options={{ title: "Itens de exemplo" }}
              columns={[
                { key: "codigo", label: "Código" },
                { key: "descricao", label: "Descrição" },
                { key: "qtd", label: "Qtd." },
              ]}
              rows={[
                { codigo: "A-100", descricao: "Componente Alfa", qtd: 12 },
                { codigo: "B-200", descricao: "Componente Beta", qtd: 4 },
                { codigo: "C-300", descricao: "Componente Gama", qtd: 27 },
              ]}
            />
          </ConfigurableTableClassesProvider>
        ),
      },
    ],
  },
];

function PaginationDemo() {
  const [page, setPage] = useState(1);

  return (
    <Pagination
      page={page}
      pageSize={10}
      total={47}
      onPageChange={setPage}
      classNames={paginationKit.pagination}
      labels={{
        navigationAriaLabel: "Paginação",
        pagesAriaLabel: "Páginas",
        previous: "Anterior",
        next: "Próxima",
        info: ({ rangeStart, rangeEnd, total }) => `${rangeStart}–${rangeEnd} de ${total}`,
        jumpLabel: "Ir para",
        jumpInputAriaLabel: "Número da página",
        jumpError: (reason, totalPages) =>
          reason === "above_max" || reason === "below_min"
            ? `Informe 1–${totalPages}`
            : "Página inválida",
      }}
    />
  );
}
