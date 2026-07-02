import { useEffect, useState } from "react";
import { photoUrl, type PublicParticipant } from "./api";
import "./thanks.css";

export function ThanksView({ participant }: { participant: PublicParticipant }) {
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setRevealed(true), 120);
    return () => window.clearTimeout(timer);
  }, []);

  const p = participant;
  const firstName = p.fullName.trim().split(/\s+/)[0];
  const message = (p.thankYouMessage?.trim() || defaultMessage(p.companyName)).split("\n\n");

  return (
    <div className={`cxp-hero${revealed ? " is-revealed" : ""}`}>
      <span className="cxp-eyebrow">Programa Experiência do Cliente · DELPI</span>

      <div className="cxp-photo-frame">
        <img className="cxp-photo" src={photoUrl(p)} alt={p.fullName} />
        <span className="cxp-badge">Feito por você na DELPI</span>
      </div>

      <h1 className="cxp-headline">Que orgulho, {firstName}!</h1>
      <p className="cxp-name">{p.fullName}</p>
      <p className="cxp-company">
        {p.companyName}
        {p.participantInfo ? ` · ${p.participantInfo}` : ""}
      </p>

      <div className="cxp-message">
        {message.map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>

      <div className="cxp-signature">
        <span className="cxp-signature__line" />
        Equipe DELPI
      </div>
      <p className="cxp-date">Sua visita · {formatDate(p.visitDate)}</p>
    </div>
  );
}

function defaultMessage(company: string): string {
  const partner = company?.trim() ? company.trim() : "sua empresa";
  return [
    "Hoje você não apenas conheceu a DELPI — você colocou a mão na massa e montou o seu próprio chicote, a mesma engenharia que conecta máquinas, veículos e indústrias por todo o Brasil.",
    `Cada contato, cada terminal e cada detalhe passou pelas suas mãos. Obrigado por viver essa experiência com a gente e por construir, junto conosco, a conexão entre a DELPI e a ${partner}.`,
    "Que essa parceria seja tão firme e resistente quanto o chicote que saiu das suas mãos. Foi uma honra ter você aqui — volte sempre!",
  ].join("\n\n");
}

function formatDate(iso: string): string {
  const parts = iso.split("-");
  if (parts.length !== 3) return iso;
  const [year, month, day] = parts;
  return `${day}/${month}/${year}`;
}
