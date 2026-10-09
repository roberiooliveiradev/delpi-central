import { Sparkles } from "lucide-react";

/**
 * S2-A + S3 — reception surface for a session with no turns yet.
 *
 * Chat-first identity: the DÉLIA glyph (Sparkles, same mark the
 * Portal dock uses for DÉLIA) — never the DELPI/Minha DELPI logo.
 * Honest by contract: no capability cards, no promised features —
 * the copy states only that answers depend on the sources and
 * permissions actually available.
 */
export function DeliaReception() {
  return (
    <section className="delia-reception" aria-label="Boas-vindas da DÉLIA">
      <span className="delia-reception__mark" aria-hidden="true">
        <Sparkles size={26} />
      </span>
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
