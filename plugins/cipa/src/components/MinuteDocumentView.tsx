import { useCallback } from "react";
import { CipaMeetingMinuteDocumentView as SharedCipaMeetingMinuteDocumentView } from "@delpi/cipa-meeting-minutes-presentation";

import { getSignatureImage, type MinuteDetail } from "../api/cipaApi";

export type MinuteDocumentViewProps = {
  detail: MinuteDetail;
  className?: string;
};

/** Wrapper autenticado — delega visualização à lib compartilhada. */
export function MinuteDocumentView({ detail, className }: MinuteDocumentViewProps) {
  const minuteId = String(detail.minute.id || "");
  const getSignatureImageForMinute = useCallback(
    (signatureId: string) => getSignatureImage(minuteId, signatureId),
    [minuteId],
  );

  return (
    <SharedCipaMeetingMinuteDocumentView
      minute={detail.minute}
      version={detail.version}
      participants={detail.participants}
      signers={detail.signers}
      signatures={detail.signatures}
      getSignatureImage={getSignatureImageForMinute}
      className={className}
    />
  );
}
