import { DisplaySection } from "./DisplaySection";
import type { SelectionSectionLayout } from "./types";

/**
 * @deprecated Absorvido por `DisplaySection` (Exibição). Mantido para hosts que
 * ainda pedem `only={["frame"]}` — delega ao mesmo UI.
 */
export function FrameSizeSection({ layout }: { layout: SelectionSectionLayout }) {
  return <DisplaySection layout={layout} />;
}
