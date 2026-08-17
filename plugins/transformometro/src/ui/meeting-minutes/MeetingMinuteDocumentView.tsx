import { useCallback } from "react";
import { MeetingMinuteDocumentView as SharedMeetingMinuteDocumentView } from "@delpi/transformometro-meeting-minutes-presentation";

import {
  fetchAtaSignatureImageBlob,
  type AtaDetail,
} from "../../data/api/transformometroMeetingMinutesApi";

type Props = {
  detail: AtaDetail;
  getAccessToken?: () => string | undefined;
  onError?: (message: string | null) => void;
};

export function MeetingMinuteDocumentView({ detail, getAccessToken }: Props) {
  const minuteId = String(detail.minute.id ?? "");
  const getSignatureImage = useCallback(
    (signatureId: string) =>
      fetchAtaSignatureImageBlob(minuteId, signatureId, getAccessToken),
    [getAccessToken, minuteId],
  );

  return (
    <SharedMeetingMinuteDocumentView
      minute={detail.minute}
      version={detail.version}
      participants={detail.participants}
      signers={detail.signers}
      signatures={detail.signatures}
      getSignatureImage={getSignatureImage}
    />
  );
}
