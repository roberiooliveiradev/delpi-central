import type { AppProps } from "../../../App";
import { RevisaoEvidencePanel } from "../../../components/evidence/RevisaoEvidencePanel";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  readOnly?: boolean;
  onError: (message: string | null) => void;
  onReload?: () => void;
};

export function RevisaoEvidenciasSection({
  revisaoId,
  getAccessToken,
  readOnly = false,
  onError,
  onReload,
}: Props) {
  return (
    <RevisaoEvidencePanel
      revisaoId={revisaoId}
      getAccessToken={getAccessToken}
      readOnly={readOnly}
      onError={onError}
      onChanged={onReload}
    />
  );
}
