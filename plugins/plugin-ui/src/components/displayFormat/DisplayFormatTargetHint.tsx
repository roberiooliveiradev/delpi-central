import type { DisplayFormatTarget } from "../../displayFormat";
import { resolveDisplayFormatTargetLabel } from "../../displayFormat";
import { DEFAULT_DISPLAY_FORMAT_CN } from "./displayFormatClasses";

export type DisplayFormatTargetHintProps = {
  target: DisplayFormatTarget;
  className?: string;
};

export function DisplayFormatTargetHint({ target, className }: DisplayFormatTargetHintProps) {
  const cn = DEFAULT_DISPLAY_FORMAT_CN;
  return (
    <p className={[cn.hint, className].filter(Boolean).join(" ")}>
      Formatando: {resolveDisplayFormatTargetLabel(target)}
    </p>
  );
}
