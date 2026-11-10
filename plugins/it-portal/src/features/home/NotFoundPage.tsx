import { ItpActionButton, ItpEmptyState } from "../../app/itPortalUi";
import { spaNavigate } from "../../app/navigation";
import { usePortal } from "../../app/PortalContext";
import { buildPath } from "../../app/routes";

export function NotFoundPage() {
  const { basePath } = usePortal();
  const home = buildPath(basePath, "home");
  return (
    <ItpEmptyState title="Página não encontrada" message="Este endereço não existe no Portal de TI.">
      <ItpActionButton variant="primary" href={home} title="Voltar ao início do Portal de TI" onClick={spaNavigate(home)}>
        Ir para o início
      </ItpActionButton>
    </ItpEmptyState>
  );
}
