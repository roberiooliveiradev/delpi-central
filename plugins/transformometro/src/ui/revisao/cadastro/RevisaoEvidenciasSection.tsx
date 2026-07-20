import type { AppProps } from "../../../App";
import { RevisaoEvidencePanel } from "../../../components/evidence/RevisaoEvidencePanel";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  onError: (message: string | null) => void;
  onReload?: () => void;
  resyncVersion?: number;
};

export function RevisaoEvidenciasSection({
  revisaoId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  onError,
  onReload,
  resyncVersion = 0,
}: Props) {
  return (
    <RevisaoEvidencePanel
      revisaoId={revisaoId}
      getAccessToken={getAccessToken}
      readOnly={readOnly}
      hideHeader={embeddedInCard}
      onError={onError}
      onChanged={onReload}
      resyncVersion={resyncVersion}
    />
  );
}
