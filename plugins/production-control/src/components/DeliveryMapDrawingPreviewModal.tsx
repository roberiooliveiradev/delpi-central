import { FilePreviewModal } from "@delpi/plugin-ui/index";

import { fetchDeliveryMapDrawingPdf } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { PpcBranch } from "../types";

type DeliveryMapDrawingPreviewModalProps = {
  open: boolean;
  branch: PpcBranch;
  productCode: string | null;
  onClose: () => void;
};

export function DeliveryMapDrawingPreviewModal({
  open,
  branch,
  productCode,
  onClose,
}: DeliveryMapDrawingPreviewModalProps) {
  const dm = copy.deliveryMap;
  const code = productCode?.trim() || null;

  return (
    <FilePreviewModal
      open={open && Boolean(code)}
      title={code ? dm.drawingModalTitle(code) : dm.drawingModalTitleFallback}
      onClose={onClose}
      source={code ? () => fetchDeliveryMapDrawingPdf({ branch, productCode: code }) : null}
      mimeType="application/pdf"
      fileName={code ? `${code}.pdf` : undefined}
      portalScopeClassName="dashboard-production-control"
      labels={{
        loading: dm.drawingLoading,
        loadFailed: dm.drawingLoadError,
      }}
    />
  );
}
