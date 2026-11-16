import "./DeploymentReviewPreview.css";

/**
 * ATLAS P2.2h.2c: isolated, read-only presentation candidate.
 * Deliberately NOT imported by App, routes, navigation or API clients.
 * Prop data is presentation-only, never approval/authorization evidence.
 */
export type DeploymentReviewSummary = Readonly<{
  proposalId: string;
  requesterLabel: string;
  environment: "prod" | "hml";
  serviceId: "public-hub";
  status: "pending_approval";
  targetCommitSha: string;
  manifestDigest: string;
  previousImageId: string;
  targetImageId: string;
  bindingSha256: string;
  expiresAt: string;
}>;

const SHA = /^[0-9a-f]{40}$/;
const DIGEST = /^sha256:[0-9a-f]{64}$/;
const HASH = /^[0-9a-f]{64}$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

function validPreview(value: DeploymentReviewSummary | null): value is DeploymentReviewSummary {
  return Boolean(
    value &&
    UUID.test(value.proposalId) &&
    value.serviceId === "public-hub" &&
    (value.environment === "hml" || value.environment === "prod") &&
    value.status === "pending_approval" &&
    SHA.test(value.targetCommitSha) &&
    DIGEST.test(value.manifestDigest) &&
    DIGEST.test(value.previousImageId) &&
    DIGEST.test(value.targetImageId) &&
    value.previousImageId !== value.targetImageId &&
    HASH.test(value.bindingSha256) &&
    typeof value.expiresAt === "string" &&
    !Number.isNaN(Date.parse(value.expiresAt)),
  );
}

export function DeploymentReviewPreview({
  proposal,
}: {
  proposal: DeploymentReviewSummary | null;
}) {
  const valid = validPreview(proposal);

  return (
    <section className="itp-deploy-review" aria-label="Prévia da revisão de implantação">
      <header className="itp-deploy-review__head">
        <div>
          <span className="itp-deploy-review__eyebrow">ATLAS · Governança de implantação</span>
          <h2>Revisão de implantação</h2>
          <p>Conferência da versão solicitada antes de uma futura aprovação.</p>
        </div>
        <span className="itp-deploy-review__tag">Prévia não ativada</span>
      </header>
      <div className="itp-deploy-review__notice" role="status">
        Esta tela ainda não está conectada ao Core ou ao journal. Nenhuma aprovação pode ser registrada aqui.
        Os deploys manuais pelo terminal continuam independentes.
      </div>
      {valid && proposal ? (
        <>
          <div className="itp-deploy-review__intro">
            <div>
              <span className="itp-deploy-review__label">Serviço</span>
              <strong>Public Hub</strong>
            </div>
            <div>
              <span className="itp-deploy-review__label">Ambiente</span>
              <strong>{proposal.environment === "prod" ? "Produção" : "Homologação"}</strong>
            </div>
            <div>
              <span className="itp-deploy-review__label">Situação</span>
              <strong>Aguardando análise</strong>
            </div>
          </div>
          <dl className="itp-deploy-review__details">
            <div><dt>Solicitante</dt><dd>{proposal.requesterLabel || "Não informado"}</dd></div>
            <div><dt>Identificador da proposta</dt><dd>{proposal.proposalId}</dd></div>
            <div><dt>Commit solicitado</dt><dd>{proposal.targetCommitSha}</dd></div>
            <div><dt>Manifesto OCI assinado</dt><dd>{proposal.manifestDigest}</dd></div>
            <div><dt>Imagem atual</dt><dd>{proposal.previousImageId}</dd></div>
            <div><dt>Imagem solicitada</dt><dd>{proposal.targetImageId}</dd></div>
            <div><dt>Identidade vinculada</dt><dd>{proposal.bindingSha256}</dd></div>
            <div><dt>Validade da proposta</dt><dd>{proposal.expiresAt}</dd></div>
          </dl>
        </>
      ) : (
        <div className="itp-deploy-review__empty">
          <strong>Nenhuma solicitação pronta para visualização.</strong>
          <p>Os dados serão carregados somente após a integração autenticada ao Portal do TI.</p>
        </div>
      )}
      <footer className="itp-deploy-review__footer">
        <span>Revisão visual apenas. Sem ações de escrita.</span>
        <div className="itp-deploy-review__buttons">
          <button type="button" disabled title="Aprovação ainda não disponível">Rejeitar</button>
          <button type="button" disabled title="Aprovação ainda não disponível">Aprovar atualização</button>
        </div>
      </footer>
    </section>
  );
}
