import { FileText } from "lucide-react";

import { copy } from "../content/copy";

type DeliveryMapProductCellProps = {
  productCode: string;
  onOpenDrawing: (productCode: string) => void;
};

export function DeliveryMapProductCell({ productCode, onOpenDrawing }: DeliveryMapProductCellProps) {
  const dm = copy.deliveryMap;
  const code = productCode.trim();

  return (
    <span className="ppc-delivery-map__product-line">
      <span className="ppc-delivery-map__product-code">{code}</span>
      {code ? (
        <button
          type="button"
          className="ppc-delivery-map__drawing-btn"
          title={dm.drawingOpenLabel}
          aria-label={dm.drawingOpenAria(code)}
          onClick={() => onOpenDrawing(code)}
        >
          <FileText size={16} aria-hidden />
        </button>
      ) : null}
    </span>
  );
}
