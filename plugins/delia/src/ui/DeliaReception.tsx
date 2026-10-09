import { DelpiLogoMark } from "@delpi/plugin-ui/index";

/**
 * S2-A — reception surface for a session with no turns yet.
 *
 * Honest by contract: no capability cards, no promised features, no
 * fake suggestions — the copy states only that answers depend on the
 * sources and permissions actually available.
 */
export function DeliaReception() {
  return (
    <section className="delia-reception" aria-label="Boas-vindas da DÉLIA">
      <DelpiLogoMark
        className="delia-reception__mark"
        title="DÉLIA — inteligência operacional da DELPI"
      />
      <h2 className="delia-reception__title">Como posso ajudar você hoje?</h2>
      <p className="delia-reception__subtitle">
        Converse com a inteligência operacional da DELPI. As respostas
        dependem das informações e permissões disponíveis no momento.
      </p>
      <p className="delia-reception__note">
        A conversa é mantida apenas nesta tela e não é salva.
      </p>
    </section>
  );
}
