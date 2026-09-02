import { useState } from "react";

import { PpActionButton, PpSectionCard, PpStateBox } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";

type DeviceFirmwareTabProps = {
  firmwareSource: string | null | undefined;
};

export function DeviceFirmwareTab({ firmwareSource }: DeviceFirmwareTabProps) {
  const source = (firmwareSource ?? "").trim() ? firmwareSource ?? "" : "";
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");

  const handleCopy = async () => {
    if (!source) return;
    try {
      await navigator.clipboard.writeText(source);
      setCopyState("copied");
      window.setTimeout(() => setCopyState("idle"), 2000);
    } catch {
      setCopyState("failed");
    }
  };

  if (!source) {
    return (
      <PpSectionCard title="Firmware (.ino)">
        <PpStateBox
          variant="empty"
          title="Sem sketch cadastrado"
          message={PP_HELP.detail.firmwareEmpty}
        />
      </PpSectionCard>
    );
  }

  const copyLabel =
    copyState === "copied"
      ? PP_HELP.detail.firmwareCopied
      : copyState === "failed"
        ? PP_HELP.detail.firmwareCopyFailed
        : PP_HELP.detail.firmwareCopy;

  return (
    <PpSectionCard
      title="Firmware (.ino)"
      actions={
        <PpActionButton variant="ghost" onClick={() => void handleCopy()}>
          {copyLabel}
        </PpActionButton>
      }
    >
      <pre className="pp-firmware-source" tabIndex={0}>
        {source}
      </pre>
    </PpSectionCard>
  );
}
