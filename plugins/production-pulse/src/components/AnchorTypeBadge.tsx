import { anchorTypeLabel } from "../utils/deviceDisplay";

type AnchorTypeBadgeProps = {
  anchorType: string;
};

export function AnchorTypeBadge({ anchorType }: AnchorTypeBadgeProps) {
  return <span className="pp-anchor-type-badge">{anchorTypeLabel(anchorType)}</span>;
}
