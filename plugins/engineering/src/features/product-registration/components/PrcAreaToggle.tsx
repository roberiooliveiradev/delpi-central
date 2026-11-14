/** U1 — seletor «Solicitações | Produtos acompanhados» da ferramenta
 * Controle e Cadastro de Produtos. Estado navegável em `?area=`. */

import { EngineeringSegmentToggle } from "../../../ui/engineeringUi";
import { PRC_PRODUCTS_COPY } from "../prcCopy";

export type PrcArea = "requests" | "products";

export function PrcAreaToggle({
  value,
  onChange,
}: {
  value: PrcArea;
  onChange: (area: PrcArea) => void;
}) {
  return (
    <EngineeringSegmentToggle
      ariaLabel={PRC_PRODUCTS_COPY.areaLabel}
      idPrefix="prc-area"
      size="sm"
      widthMode="content"
      value={value}
      onChange={(v) => onChange(v as PrcArea)}
      options={[
        {
          value: "requests",
          label: PRC_PRODUCTS_COPY.areaRequests,
        },
        {
          value: "products",
          label: PRC_PRODUCTS_COPY.areaProducts,
        },
      ]}
    />
  );
}
