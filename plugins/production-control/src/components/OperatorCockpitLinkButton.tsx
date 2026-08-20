import { useEffect, useState } from "react";
import { copy } from "../content/copy";
import { buildOperatorCockpitUrl, copyText } from "../utils/operatorCockpitLink";

type Props = {
  branch: string;
};

/** Compartilha com o chão de fábrica o link somente-leitura da fila desta filial. */
export function OperatorCockpitLinkButton({ branch }: Props) {
  const [feedback, setFeedback] = useState<"idle" | "copied" | "error">("idle");

  useEffect(() => {
    if (feedback === "idle") return;
    const timer = window.setTimeout(() => setFeedback("idle"), 2400);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  const onClick = async () => {
    const ok = await copyText(buildOperatorCockpitUrl(branch));
    setFeedback(ok ? "copied" : "error");
  };

  return (
    <button
      type="button"
      className="ppc-period__operator-link"
      onClick={onClick}
      title={copy.machineLoad.operatorLinkHint}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path
          d="M10 14a4 4 0 0 0 5.66 0l3-3A4 4 0 0 0 13 5.34l-1.2 1.2M14 10a4 4 0 0 0-5.66 0l-3 3A4 4 0 0 0 11 18.66l1.2-1.2"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
        />
      </svg>
      {feedback === "copied"
        ? copy.machineLoad.operatorLinkCopied
        : feedback === "error"
          ? copy.machineLoad.operatorLinkError
          : copy.machineLoad.operatorLink}
    </button>
  );
}
