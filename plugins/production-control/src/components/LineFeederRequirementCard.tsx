import {
  createDashboardInteractiveDataCard,
  createDashboardStatusBadge,
} from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";
import type { LineFeederRequirement, LineFeederStatusMeta } from "../types";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import {
  formatScheduleTime,
  requirementBadgeVariant,
} from "../utils/lineFeederStatus";

const InteractiveDataCard = createDashboardInteractiveDataCard({ prefix: "ppc" });
const StatusBadge = createDashboardStatusBadge({ prefix: "ppc" });

type LineFeederRequirementCardProps = {
  row: LineFeederRequirement;
  statuses: Record<string, LineFeederStatusMeta>;
  onOpen: (row: LineFeederRequirement) => void;
};

function optionalQty(value: number | null | undefined): string {
  if (value == null) return "—";
  return formatOpQuantity(value);
}

export function LineFeederRequirementCard({
  row,
  statuses,
  onOpen,
}: LineFeederRequirementCardProps) {
  const texts = copy.lineFeeder;
  const blocked = Boolean(row.inventory_blocked);
  const productTitle = row.description?.trim()
    ? `${row.product_code} · ${row.description.trim()}`
    : row.product_code;

  return (
    <InteractiveDataCard
      ariaLabel={productTitle}
      openHint={texts.detail.openHint}
      onActivate={() => onOpen(row)}
      fields={[
        {
          id: "inventory_blocked",
          label: texts.columns.inventoryBlock,
          value: (
            <span className="ppc-feeder__card-inv">
              <span
                className={
                  blocked
                    ? "ppc-feeder__inv-dot ppc-feeder__inv-dot--blocked"
                    : "ppc-feeder__inv-dot ppc-feeder__inv-dot--ok"
                }
                aria-hidden
              />
              <span>{blocked ? texts.inventoryBlockedShort : texts.inventoryFreeShort}</span>
            </span>
          ),
          valueTone: "meta",
        },
        {
          id: "product_code",
          label: texts.columns.product,
          value: productTitle,
          valueTone: "title",
        },
        {
          id: "work_center",
          label: texts.columns.workCenter,
          value: row.work_center,
        },
        {
          id: "to_deliver_qty",
          label: texts.columns.toDeliver,
          value: optionalQty(row.to_deliver_qty),
          valueTone: "value",
        },
        {
          id: "status",
          label: texts.columns.status,
          value: (
            <StatusBadge
              label={statuses[row.status]?.label ?? row.status}
              variant={requirementBadgeVariant(row.status)}
            />
          ),
        },
        {
          id: "pickup_location",
          label: texts.columns.pickupLocation,
          value: row.pickup_location?.trim()
            ? row.pickup_location
            : copy.lineFeeder.pickPlan.pickupLocationEmpty,
          valueTone: "meta",
        },
        {
          id: "first_scheduled_at",
          label: texts.columns.firstScheduled,
          value: formatScheduleTime(row.first_scheduled_at),
          valueTone: "meta",
        },
        {
          id: "first_production_order",
          label: texts.columns.order,
          value: `${row.first_production_order}/${row.first_operation_code}`,
          valueTone: "meta",
        },
      ]}
    />
  );
}
