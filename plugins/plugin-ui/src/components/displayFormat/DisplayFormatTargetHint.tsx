import type { DisplayFormatTarget } from "../../displayFormat";
import { resolveDisplayFormatTargetLabel } from "../../displayFormat";
import { DEFAULT_DISPLAY_FORMAT_CN } from "./displayFormatClasses";

export type DisplayFormatTargetHintProps = {
  target: DisplayFormatTarget;
  /** Texto fino do alvo; se omitido, usa o rótulo genérico do target. */
  label?: string;
  className?: string;
};

export function DisplayFormatTargetHint({ target, label, className }: DisplayFormatTargetHintProps) {
  const cn = DEFAULT_DISPLAY_FORMAT_CN;
  return (
    <p className={[cn.hint, className].filter(Boolean).join(" ")}>
      Formatando: {label?.trim() || resolveDisplayFormatTargetLabel(target)}
    </p>
  );
}
