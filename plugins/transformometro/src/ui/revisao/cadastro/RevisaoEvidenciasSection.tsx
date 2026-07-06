import type { AppProps } from "../../../App";
import { RevisaoEvidencePanel } from "../../../components/evidence/RevisaoEvidencePanel";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  onError: (message: string | null) => void;
  onReload?: () => void;
};

export function RevisaoEvidenciasSection({
  revisaoId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  onError,
  onReload,
}: Props) {
  return (
    <RevisaoEvidencePanel
      revisaoId={revisaoId}
      getAccessToken={getAccessToken}
      readOnly={readOnly}
      hideHeader={embeddedInCard}
      onError={onError}
      onChanged={onReload}
    />
  );
}
