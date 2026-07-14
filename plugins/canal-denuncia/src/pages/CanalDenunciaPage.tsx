import { useState, type FormEvent } from "react";
import {
  CheckCircle2,
  CircleAlert,
  FilePenLine,
  Mail,
  Scale,
  Send,
  Shield,
  ShieldCheck,
} from "lucide-react";
import logoMinhaDelpi from "../assets/logoMinhaDelpi.svg";
import { createAnonymousDenuncia } from "../api/canalDenunciaApi";
import {
  ERROR_MESSAGE,
  FLOW_STEPS,
  MAX_DESCRIPTION_LENGTH,
  MIN_DESCRIPTION_LENGTH,
  PRIVACY_NOTICE,
  RESPONSIBILITY_NOTICE,
  SUCCESS_MESSAGE,
} from "../constants/form";

const FLOW_ICONS = [FilePenLine, ShieldCheck, Mail, Scale] as const;


export function CanalDenunciaPage() {
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const trimmedLength = description.trim().length;
  const canSubmit =
    !submitting &&
    trimmedLength >= MIN_DESCRIPTION_LENGTH &&
    description.length <= MAX_DESCRIPTION_LENGTH;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit || submitting) return;

    setSubmitting(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      await createAnonymousDenuncia({ description: description.trim() });
      setDescription("");
      setSuccessMessage(SUCCESS_MESSAGE);
    } catch {
      setErrorMessage(ERROR_MESSAGE);
    } finally {
      setSubmitting(false);
    }
  }

  function handleDescriptionChange(value: string) {
    setDescription(value.slice(0, MAX_DESCRIPTION_LENGTH));
    if (successMessage) setSuccessMessage(null);
    if (errorMessage) setErrorMessage(null);
  }

  return (
    <div className="cd-page">
      <header className="cd-hero">
        <div className="cd-hero__brand">
          <img
            className="cd-hero__logo"
            src={logoMinhaDelpi}
            alt="Minha DELPI"
            data-testid="canal-denuncia-logo"
          />
          <span className="cd-hero__divider" aria-hidden="true" />
          <div className="cd-hero__titles">
            <p className="cd-hero__eyebrow">Ouvidoria · Sigilo</p>
            <h1 className="cd-hero__title">Canal de Denúncia</h1>
          </div>
        </div>
        <Shield className="cd-hero__watermark" aria-hidden="true" strokeWidth={1.25} />
      </header>

      <section className="cd-intro" aria-labelledby="canal-denuncia-intro-title">
        <h2 id="canal-denuncia-intro-title" className="cd-intro__title">
          Um espaço seguro para relatar o ocorrido
        </h2>
        <p className="cd-intro__lead">
          Este espaço é destinado ao envio de relatos à Ouvidoria da DELPI. Seu
          relato será recebido de forma sigilosa para análise responsável.
        </p>
      </section>

      <div className="cd-layout">
      <section className="cd-card cd-card--privacy" aria-label="Orientações de sigilo">
        <div className="cd-card__icon" aria-hidden="true">
          <Shield strokeWidth={1.75} />
        </div>
        <div className="cd-card__body">
          <p className="cd-card__text">{PRIVACY_NOTICE}</p>
          <hr className="cd-card__sep" />

          <ol className="cd-flow" aria-label="Como funciona o Canal de Denúncia">
            {FLOW_STEPS.map((step, index) => {
              const Icon = FLOW_ICONS[index] ?? Shield;
              return (
                <li key={step.title} className="cd-flow__item">
                  <span className="cd-flow__marker" aria-hidden="true">
                    <Icon strokeWidth={1.75} />
                    <span className="cd-flow__index">{index + 1}</span>
                  </span>
                  <div className="cd-flow__content">
                    <p className="cd-flow__title">{step.title}</p>
                    <p className="cd-flow__desc">{step.description}</p>
                  </div>
                </li>
              );
            })}
          </ol>

          <hr className="cd-card__sep" />
          <p className="cd-card__text">{RESPONSIBILITY_NOTICE}</p>
        </div>
      </section>


      <form className="cd-card cd-card--form" onSubmit={handleSubmit} noValidate>
        <div className="cd-form__heading">
          <FilePenLine className="cd-form__heading-icon" aria-hidden="true" />
          <label className="cd-form__label" htmlFor="canal-denuncia-description">
            Relato da denúncia
          </label>
        </div>

        <textarea
          id="canal-denuncia-description"
          className="cd-form__textarea"
          value={description}
          onChange={(event) => handleDescriptionChange(event.target.value)}
          disabled={submitting}
          maxLength={MAX_DESCRIPTION_LENGTH}
          rows={12}
          placeholder="Descreva o ocorrido com o máximo de clareza e objetividade."
        />

        <div className="cd-form__meta">
          <span className="cd-form__hint">
            Mínimo de {MIN_DESCRIPTION_LENGTH} caracteres.
          </span>
          <span className="cd-form__counter" data-testid="char-counter">
            {description.length} / {MAX_DESCRIPTION_LENGTH}
          </span>
        </div>

        <div className="cd-form__feedback" aria-live="polite">
          {successMessage ? (
            <p className="cd-alert cd-alert--success" role="status">
              <CheckCircle2 aria-hidden="true" />
              <span>{successMessage}</span>
            </p>
          ) : null}
          {errorMessage ? (
            <p className="cd-alert cd-alert--error" role="alert">
              <CircleAlert aria-hidden="true" />
              <span>{errorMessage}</span>
            </p>
          ) : null}
        </div>

        <button
          type="submit"
          className="cd-form__submit"
          disabled={!canSubmit}
          aria-busy={submitting || undefined}
        >
          {submitting ? (
            <>Enviando...</>
          ) : (
            <>
              <Send aria-hidden="true" size={18} />
              Enviar denúncia
            </>
          )}
        </button>
      </form>
      </div>
    </div>
  );
}
