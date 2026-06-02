import type { ProcessoComparativoItem } from "../../data/api/transformometroApi";

declare module "../../data/api/transformometroApi" {
  export type RevisionCompareItem = ProcessoComparativoItem;
}
