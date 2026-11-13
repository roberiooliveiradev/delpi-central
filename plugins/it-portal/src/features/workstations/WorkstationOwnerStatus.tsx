import { useQuery } from "@tanstack/react-query";
import { lookupDirectoryUser } from "../../api/coreDirectoryApi";

/** Nome historico continua visivel quando uma conta e inativada. */
export function WorkstationOwnerStatus({
  userId,
  snapshot,
}: {
  userId: string | null;
  snapshot: string | null;
}) {
  const lookup = useQuery({
    queryKey: ["it-portal", "directory-user", userId],
    queryFn: ({ signal }) => lookupDirectoryUser(userId!, signal),
    enabled: Boolean(userId),
    retry: 1,
    staleTime: 60_000,
  });
  if (!userId) {
    return <span>{snapshot ? `${snapshot} (cadastro anterior, sem vínculo)` : "Sem responsável"}</span>;
  }
  if (lookup.isPending) return <span>{snapshot || "Usuário vinculado"} (verificando vínculo…)</span>;
  if (lookup.isError) return <span>{snapshot || "Usuário vinculado"} (diretório indisponível)</span>;
  if (!lookup.data) return <span>{snapshot || "Usuário vinculado"} (conta inativa ou indisponível)</span>;
  return <span>{lookup.data.name} (usuário da plataforma)</span>;
}
