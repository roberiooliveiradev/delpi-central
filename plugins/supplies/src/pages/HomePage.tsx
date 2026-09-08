import { SuppliesStateBanner } from "../app/suppliesUi";
import { PlaceholderPage } from "./PlaceholderPage";

type HomePageProps = {
  basePath: string;
};

export function HomePage({ basePath }: HomePageProps) {
  return (
    <>
      <SuppliesStateBanner>
        Início: cards de atenção chegam na próxima entrega. Use a navegação e o Ctrl+K para as
        áreas liberadas.
      </SuppliesStateBanner>
      <PlaceholderPage
        basePath={basePath}
        title="Início"
        description="O hub de atenção será composto na E4. Enquanto isso, abra as jornadas pela barra superior."
      />
    </>
  );
}
