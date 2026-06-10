import { useContext, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Compass, RotateCcw } from "lucide-react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";
import { useConfirmDialog } from "../components/ConfirmDialogProvider";
import { startPortalTour } from "./PortalTour";
import { restartPortalTourRemote } from "./portalTourPersistence";
import { resumePortalTour } from "./portalTourSession";

export function PortalTourProfileControls() {
  const { user, getAccessToken, refreshToken } = useContext(AuthContext);
  const navigate = useNavigate();
  const confirm = useConfirmDialog();

  const coreApi = useMemo(
    () =>
      new CoreApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  const handleContinueTour = () => {
    resumePortalTour();
    navigate("/");
  };

  const handleResetTour = async () => {
    if (!user?.id) return;

    const confirmed = await confirm({
      title: "Zerar progresso do tour?",
      message:
        "Isso apaga conquistas, XP e ranking desta versão do tour. A ação não pode ser desfeita.",
      confirmText: "Zerar e recomeçar",
      cancelText: "Cancelar",
      danger: true,
    });

    if (!confirmed) return;

    await restartPortalTourRemote(coreApi, user.id);
    startPortalTour();
    navigate("/");
  };

  return (
    <div className="portal-tour-achievements-controls">
      <button
        type="button"
        className="home-panel-action portal-tour-achievements-resume"
        data-tour="profile-tour-resume"
        onClick={handleContinueTour}
      >
        <Compass size={14} aria-hidden="true" />
        Continuar explorando
      </button>
      <button
        type="button"
        className="portal-tour-achievements-reset"
        data-tour="profile-tour-reset"
        onClick={() => void handleResetTour()}
      >
        <RotateCcw size={14} aria-hidden="true" />
        Zerar progresso e recomeçar
      </button>
    </div>
  );
}
