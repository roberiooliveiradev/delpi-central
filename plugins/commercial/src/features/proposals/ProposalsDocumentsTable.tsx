import type { CSSProperties } from "react";
import { HelpTooltip, type DataTableColumn } from "@delpi/plugin-ui/index";

import {
  CommercialDataCardsGrid,
  CommercialDataListToolbar,
  CommercialDataTable,
  CommercialInteractiveDataCard,
  CommercialSegmentToggle,
  CommercialTableFontSizeControls,
  usePersistedViewLayout,
  useTableFontSize,
} from "../../app/commercialUi";
import { currentLocationAsReturnTo } from "../../app/commercialNavigationReturn";
import { navigateProposalDetail } from "../../app/pluginNavigation";
import { CM_HELP } from "../../content/helpTooltips";
import { PROPOSALS_CONTENT } from "../../content/analyticsContent";
import type { ProposalDocumentListItem } from "../../types/proposalsDocument";
import {
  PROPOSALS_DOCUMENTS_COLUMN_HELP,
  withColumnHelp,
} from "../../utils/customersColumnHelp";
import { formatDisplayDate } from "../../utils/dates";

const LAYOUT_STORAGE_KEY = "commercial.proposals.documents.layout";
const FONT_SIZE_STORAGE_KEY = "commercial.proposals.documents.tableFontSize";

type ProposalsDocumentsTableProps = {
  rows: ProposalDocumentListItem[];
  basePath: string;
  loading?: boolean;
};

function buildColumns(
  openDetail: (row: ProposalDocumentListItem) => void,
): DataTableColumn<ProposalDocumentListItem>[] {
  return [
    {
      key: "ov",
      header: "Nº OV",
      render: (row) => (
        <button
          type="button"
          className="cm-link-button"
          onClick={(event) => {
            event.stopPropagation();
            openDetail(row);
          }}
        >
          {row.numero_ov || row.proposta_interna}
        </button>
      ),
    },
    { key: "interna", header: "Proposta", render: (row) => row.proposta_interna },
    { key: "cliente", header: "Cliente", render: (row) => row.cliente || "—" },
    {
      key: "oportunidade",
      header: "Oportunidade",
      render: (row) => row.oportunidade || "—",
    },
    { key: "versao", header: "Versão", render: (row) => row.versao || "—" },
    {
      key: "data",
      header: "Data",
      render: (row) => formatDisplayDate(row.data),
    },
    {
      key: "itens",
      header: "Itens",
      align: "right",
      render: (row) => row.quantidade_itens.toLocaleString("pt-BR"),
    },
  ];
}

export function ProposalsDocumentsTable({
  rows,
  basePath,
  loading = false,
}: ProposalsDocumentsTableProps) {
  const { layout, setLayout } = usePersistedViewLayout({
    storageKey: LAYOUT_STORAGE_KEY,
  });
  const {
    fontSize,
    increase,
    decrease,
    reset: resetFontSize,
    canIncrease,
    canDecrease,
    isDefault,
  } = useTableFontSize({
    storageKey: FONT_SIZE_STORAGE_KEY,
  });

  const tableStyle = {
    "--delpi-ui-table-font-size": `${fontSize}px`,
  } as CSSProperties;

  const openDetail = (row: ProposalDocumentListItem) =>
    navigateProposalDetail(row.proposta_interna, {
      basePath,
      returnNav: {
        returnTo: currentLocationAsReturnTo(),
        returnLabel: PROPOSALS_CONTENT.list.title,
      },
    });
  const baseColumns = buildColumns(openDetail);
  const columns = withColumnHelp(baseColumns, PROPOSALS_DOCUMENTS_COLUMN_HELP);

  return (
    <>
      <CommercialDataListToolbar
        style={tableStyle}
        leading={
          <HelpTooltip
            content={CM_HELP.proposals.layoutToggle}
            ariaLabel="Ajuda: modo Tabela ou Cards"
            wrap
            placement="bottom"
          >
            <CommercialSegmentToggle
              size="sm"
              ariaLabel="Modo de visualização"
              idPrefix="proposals-documents-layout"
              value={layout}
              onChange={setLayout}
              options={[
                { value: "table", label: "Tabela" },
                { value: "cards", label: "Cards" },
              ]}
            />
          </HelpTooltip>
        }
        hint={
          <HelpTooltip
            content={CM_HELP.proposals.tableRowOpensDetail}
            ariaLabel="Ajuda: tabela de propostas"
            wrap
            placement="bottom"
          >
            <span className="delpi-ui-section-hint-label">
              {columns.length} coluna(s) · {rows.length.toLocaleString("pt-BR")} linha(s)
            </span>
          </HelpTooltip>
        }
        actions={
          <CommercialTableFontSizeControls
            fontSize={fontSize}
            onIncrease={increase}
            onDecrease={decrease}
            onReset={resetFontSize}
            canIncrease={canIncrease}
            canDecrease={canDecrease}
            isDefault={isDefault}
          />
        }
      />

      {layout === "table" ? (
        <div style={tableStyle}>
          <CommercialDataTable
            rows={rows}
            columns={columns}
            rowKey={(row) => row.proposta_interna}
            layout="section"
            loading={loading}
            onRowClick={openDetail}
            rowClickRole="button"
          />
        </div>
      ) : (
        <CommercialDataCardsGrid
          style={tableStyle}
          ariaLabel="Propostas-documento"
        >
          {rows.map((row) => {
            const label = row.numero_ov || row.proposta_interna;
            return (
              <CommercialInteractiveDataCard
                key={row.proposta_interna}
                ariaLabel={`Abrir proposta ${label}`}
                onActivate={() => openDetail(row)}
                openHint={CM_HELP.proposals.tableRowOpensDetail}
                fields={[
                  {
                    id: "ov",
                    label: "Nº OV",
                    valueTone: "title",
                    value: label,
                  },
                  {
                    id: "interna",
                    label: "Proposta",
                    valueTone: "meta",
                    value: row.proposta_interna,
                  },
                  {
                    id: "cliente",
                    label: "Cliente",
                    valueTone: "value",
                    value: row.cliente || "—",
                  },
                  {
                    id: "oportunidade",
                    label: "Oportunidade",
                    valueTone: "meta",
                    value: row.oportunidade || "—",
                  },
                  {
                    id: "versao",
                    label: "Versão",
                    valueTone: "meta",
                    value: row.versao || "—",
                  },
                  {
                    id: "data",
                    label: "Data",
                    valueTone: "meta",
                    value: formatDisplayDate(row.data),
                  },
                  {
                    id: "itens",
                    label: "Itens",
                    valueTone: "meta",
                    value: row.quantidade_itens.toLocaleString("pt-BR"),
                  },
                ]}
              />
            );
          })}
        </CommercialDataCardsGrid>
      )}
    </>
  );
}
