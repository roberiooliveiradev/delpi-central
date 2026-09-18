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
} from "./query";
import type { PurchaseRequestListItem } from "./types";

type PurchaseRequestsCardsProps = {
  items: PurchaseRequestListItem[];
  detailHref: (item: PurchaseRequestListItem) => string;
  onSelectRow: (item: PurchaseRequestListItem) => void;
};

function stageBadgeVariant(
  stage: string | null | undefined,
): "neutral" | "info" | "success" | "warning" {
  switch (stage) {
    case "awaiting_order":
    case "awaiting_receipt":
      return "warning";
    case "partially_ordered":
    case "ordered":
    case "partially_received":
      return "info";
    case "completed":
      return "success";
    default:
      return "neutral";
  }
}

export function PurchaseRequestsCards({
  items,
  detailHref,
  onSelectRow,
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
                  <SuppliesPersonIdentity person={row.requester} />
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
