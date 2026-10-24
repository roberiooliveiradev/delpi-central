import { SuppliesPersonIdentity } from "../../app/SuppliesDirectoryIdentity";
import {
  SuppliesDataCardsGrid,
  SuppliesEntityLink,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { PURCHASE_REQUESTS_CONTENT as C } from "./content";
import {
  formatDatePtBr,
  formatProductLabel,
  formatRequestNumber,
  labelOverallStage,
  stageBadgeVariant,
} from "./query";
import type { PurchaseRequestListItem } from "./types";

type PurchaseRequestsCardsProps = {
  items: PurchaseRequestListItem[];
  detailHref: (item: PurchaseRequestListItem) => string;
  onSelectRow: (item: PurchaseRequestListItem) => void;
  basePath: string;
};

export function PurchaseRequestsCards({
  items,
  detailHref,
  onSelectRow,
  basePath,
}: PurchaseRequestsCardsProps) {
  return (
    <SuppliesDataCardsGrid
      className="sp-purchase-requests__cards"
      ariaLabel={C.cardsAriaLabel}
    >
      {items.map((row) => {
        const label = formatRequestNumber(row.request_number);
        return (
          <article
            key={`${row.branch}-${row.request_number}-${row.request_item ?? ""}`}
            className="sp-purchase-requests__card"
          >
            <header className="sp-purchase-requests__card-header">
              <SuppliesEntityLink
                href={detailHref(row)}
                title={C.openScLinkTitle(label)}
                className="sp-entity-link"
                onNavigate={() => onSelectRow(row)}
              >
                {label}
              </SuppliesEntityLink>
              <span>{row.request_item || "—"}</span>
            </header>
            <p className="sp-purchase-requests__card-product">
              {formatProductLabel(row.product_code, row.product_description)}
            </p>
            <dl className="sp-purchase-requests__card-meta">
              <div>
                <dt>{C.cardRequester}</dt>
                <dd>
                  <SuppliesPersonIdentity
                    person={row.requester}
                    photoPeriod={{
                      dateFrom: row.request_issue_date,
                      dateTo: row.request_issue_date,
                    }}
                    basePath={basePath}
                  />
                </dd>
              </div>
              <div>
                <dt>{C.cardCc}</dt>
                <dd>{row.cost_center?.code || row.cost_center_code || "—"}</dd>
              </div>
              <div>
                <dt>{C.cardOpened}</dt>
                <dd>{formatDatePtBr(row.request_issue_date)}</dd>
              </div>
              <div>
                <dt>{C.cardStage}</dt>
                <dd>
                  <SuppliesStatusBadge
                    label={labelOverallStage(row.derived?.overall_stage)}
                    variant={stageBadgeVariant(row.derived?.overall_stage)}
                  />
                </dd>
              </div>
            </dl>
          </article>
        );
      })}
    </SuppliesDataCardsGrid>
  );
}
