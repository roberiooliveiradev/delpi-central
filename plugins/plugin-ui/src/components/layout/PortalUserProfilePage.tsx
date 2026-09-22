/**
 * Página canônica de perfil de usuário de um portal.
 * OWNS: hierarquia visual (path → hero → identidade|atalhos → seções) e rótulos genéricos.
 * DOES NOT OWN: HTTP, AuthZ, `isSelf`, rotas do portal, preferências ou copy de produto.
 *
 * Identidade é somente leitura: editar foto/cargo/contatos é `/profile` da Minha DELPI,
 * acionado pelo host via `hero.actions` ou `identity.actions`.
 */

import type { ReactNode } from "react";
import {
  BriefcaseBusiness,
  Mail,
  MessageCircle,
  Phone,
  Smartphone,
  User,
} from "lucide-react";

import { ActionButton } from "../actions/ActionButton";
import {
  InitialsAvatar,
  initialsAvatarBemClasses,
  type InitialsAvatarClassNames,
} from "./InitialsAvatar";
import {
  PageHero,
  pageHeroBemClasses,
  type PageHeroClassNames,
  type PageHeroDensity,
} from "./PageHero";
import {
  PagePath,
  pagePathBemClasses,
  type PagePathClassNames,
  type PagePathItem,
  type PagePathLink,
} from "./PagePath";
import {
  SectionCard,
  sectionCardPacBemClasses,
  type SectionCardClassNames,
  type SectionCardLabels,
} from "./SectionCard";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type PortalUserProfileIdentityField = {
  id: string;
  label: ReactNode;
  value: ReactNode;
  icon?: ReactNode;
};

export type PortalUserProfileIdentity = {
  name: string;
  email?: string | null;
  jobTitle?: string | null;
  phone?: string | null;
  mobile?: string | null;
  whatsapp?: string | null;
  /** URL já resolvida pelo host (blob, CDN). O kit não baixa foto. */
  photoUrl?: string | null;
  /** Chave estável de cor das iniciais (ex.: `user_id`). Default: `name`. */
  colorKey?: string;
  previewTitle?: string;
  previewAriaLabel?: string;
  portalScopeClassName?: string;
  /** Mostra `—` nos contatos sem valor em vez de omitir a linha. */
  showEmptyFields?: boolean;
  /** Linhas adicionais do portal (ex.: unidades). */
  extraFields?: PortalUserProfileIdentityField[];
  /** Nota de apresentação (ex.: onde editar a identidade). */
  note?: ReactNode;
  /** Ações do card de identidade (ex.: abrir `/profile`). */
  actions?: ReactNode;
};

export type PortalUserProfileShortcut = {
  id: string;
  label: ReactNode;
  icon?: ReactNode;
  /** Tooltip nativo do atalho. */
  title?: string;
  onSelect: () => void;
};

export type PortalUserProfileHero = {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  badge?: ReactNode;
  actions?: ReactNode;
  density?: PageHeroDensity;
};

export type PortalUserProfilePagePath = {
  back: PagePathLink;
  items?: PagePathItem[];
  current: string;
};

export type PortalUserProfilePageClassNames = {
  root: string;
  grid: string;
  identity: string;
  identityAvatar: string;
  identityFields: string;
  field: string;
  fieldLabel: string;
  fieldValue: string;
  note: string;
  identityActions: string;
  shortcuts: string;
  sections: string;
  status: string;
  error: string;
  loading: string;
  pagePath: PagePathClassNames;
  hero: PageHeroClassNames;
  section: SectionCardClassNames;
  avatar: InitialsAvatarClassNames;
};

export type PortalUserProfilePageLabels = {
  pageAriaLabel: string;
  identityTitle: string;
  identitySubtitle?: string;
  shortcutsTitle: string;
  shortcutsSubtitle?: string;
  shortcutsAriaLabel: string;
  nameLabel: string;
  emailLabel: string;
  jobTitleLabel: string;
  phoneLabel: string;
  mobileLabel: string;
  whatsappLabel: string;
  emptyValue: string;
  section: SectionCardLabels;
};

export type PortalUserProfilePageProps = {
  classNames: PortalUserProfilePageClassNames;
  /** Rótulos genéricos da página. Copy de produto continua no `content/` do portal. */
  labels?: PortalUserProfilePageLabels;
  className?: string;
  pagePath?: PortalUserProfilePagePath;
  hero?: PortalUserProfileHero;
  identity?: PortalUserProfileIdentity | null;
  /** `hint` do card de identidade (HelpTooltip do portal). */
  identityHint?: string;
  shortcuts?: PortalUserProfileShortcut[];
  shortcutsHint?: string;
  /** Seções de domínio do portal (preferências, acessos, carteiras, grupos). */
  sections?: ReactNode;
  /** Substitui o corpo enquanto o host carrega. `pagePath` permanece navegável. */
  loading?: boolean;
  loadingNode?: ReactNode;
  /** Avisos não fatais (ex.: sem permissão, preferências salvas). */
  status?: ReactNode;
  /** Erro fatal do perfil (host decide banner e retry). */
  error?: ReactNode;
  /** Escopo de tema do portal para overlays (overflow do path, lightbox da foto). */
  portalScopeClassName?: string;
};

export const PORTAL_USER_PROFILE_LABELS_PT: PortalUserProfilePageLabels = {
  pageAriaLabel: "Perfil do usuário",
  identityTitle: "Identidade",
  identitySubtitle: "Dados do cadastro corporativo.",
  shortcutsTitle: "Atalhos",
  shortcutsSubtitle: "Áreas liberadas para este usuário.",
  shortcutsAriaLabel: "Atalhos do portal",
  nameLabel: "Nome",
  emailLabel: "E-mail",
  jobTitleLabel: "Cargo",
  phoneLabel: "Telefone",
  mobileLabel: "Celular",
  whatsappLabel: "WhatsApp",
  emptyValue: "Não informado",
  section: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
};

export function portalUserProfilePageBemClasses(
  prefix: string,
  overrides?: Partial<
    Pick<PortalUserProfilePageClassNames, "pagePath" | "hero" | "section" | "avatar">
  >,
): PortalUserProfilePageClassNames {
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  const base = `${prefix}-portal-user-profile`;
  const ui = "delpi-ui-portal-user-profile";
  return {
    root: pair(base, ui),
    grid: pair(`${base}__grid`, `${ui}__grid`),
    identity: pair(`${base}__identity`, `${ui}__identity`),
    identityAvatar: pair(`${base}__identity-avatar`, `${ui}__identity-avatar`),
    identityFields: pair(`${base}__identity-fields`, `${ui}__identity-fields`),
    field: pair(`${base}__field`, `${ui}__field`),
    fieldLabel: pair(`${base}__field-label`, `${ui}__field-label`),
    fieldValue: pair(`${base}__field-value`, `${ui}__field-value`),
    note: pair(`${base}__note`, `${ui}__note`),
    identityActions: pair(`${base}__identity-actions`, `${ui}__identity-actions`),
    shortcuts: pair(`${base}__shortcuts`, `${ui}__shortcuts`),
    sections: pair(`${base}__sections`, `${ui}__sections`),
    status: pair(`${base}__status`, `${ui}__status`),
    error: pair(`${base}__error`, `${ui}__error`),
    loading: pair(`${base}__loading`, `${ui}__loading`),
    pagePath: overrides?.pagePath ?? pagePathBemClasses(prefix),
    hero: overrides?.hero ?? pageHeroBemClasses(prefix),
    section: overrides?.section ?? sectionCardPacBemClasses(prefix),
    avatar: overrides?.avatar ?? initialsAvatarBemClasses(prefix),
  };
}

function trimOrNull(value: string | null | undefined): string | null {
  const text = (value ?? "").trim();
  return text || null;
}

type ResolvedField = {
  id: string;
  label: ReactNode;
  value: ReactNode;
  icon?: ReactNode;
};

function resolveIdentityFields(
  identity: PortalUserProfileIdentity,
  labels: PortalUserProfilePageLabels,
): ResolvedField[] {
  const iconSize = 15;
  const showEmpty = identity.showEmptyFields === true;
  const fields: ResolvedField[] = [
    {
      id: "name",
      label: labels.nameLabel,
      value: trimOrNull(identity.name) ?? labels.emptyValue,
      icon: <User size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
    {
      id: "email",
      label: labels.emailLabel,
      value: trimOrNull(identity.email) ?? labels.emptyValue,
      icon: <Mail size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
  ];

  const contacts: Array<{ id: string; label: ReactNode; raw: string | null; icon: ReactNode }> = [
    {
      id: "jobTitle",
      label: labels.jobTitleLabel,
      raw: trimOrNull(identity.jobTitle),
      icon: <BriefcaseBusiness size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
    {
      id: "phone",
      label: labels.phoneLabel,
      raw: trimOrNull(identity.phone),
      icon: <Phone size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
    {
      id: "mobile",
      label: labels.mobileLabel,
      raw: trimOrNull(identity.mobile),
      icon: <Smartphone size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
    {
      id: "whatsapp",
      label: labels.whatsappLabel,
      raw: trimOrNull(identity.whatsapp),
      icon: <MessageCircle size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
  ];

  for (const contact of contacts) {
    if (!contact.raw && !showEmpty) continue;
    fields.push({
      id: contact.id,
      label: contact.label,
      value: contact.raw ?? labels.emptyValue,
      icon: contact.icon,
    });
  }

  for (const extra of identity.extraFields ?? []) {
    fields.push(extra);
  }

  return fields;
}

export function PortalUserProfilePage({
  classNames,
  labels = PORTAL_USER_PROFILE_LABELS_PT,
  className,
  pagePath,
  hero,
  identity,
  identityHint,
  shortcuts,
  shortcutsHint,
  sections,
  loading = false,
  loadingNode,
  status,
  error,
  portalScopeClassName,
}: PortalUserProfilePageProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const hasShortcuts = Boolean(shortcuts?.length);
  const hasBody =
    !loading && Boolean(hero || identity || hasShortcuts || sections);

  return (
    <section className={rootClass} aria-label={labels.pageAriaLabel}>
      {pagePath ? (
        <PagePath
          classNames={classNames.pagePath}
          back={pagePath.back}
          items={pagePath.items ?? []}
          current={pagePath.current}
          portalScopeClassName={portalScopeClassName}
        />
      ) : null}

      {status ? (
        <div className={classNames.status} role="status">
          {status}
        </div>
      ) : null}

      {error ? (
        <div className={classNames.error} role="alert">
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className={classNames.loading} aria-busy="true">
          {loadingNode}
        </div>
      ) : null}

      {hasBody ? (
        <>
          {hero ? (
            <PageHero
              classNames={classNames.hero}
              eyebrow={hero.eyebrow}
              title={hero.title}
              description={hero.description}
              badge={hero.badge}
              actions={hero.actions}
              density={hero.density}
            />
          ) : null}

          {identity || hasShortcuts ? (
            <div className={classNames.grid}>
              {identity ? (
                <SectionCard
                  classNames={classNames.section}
                  labels={labels.section}
                  title={labels.identityTitle}
                  subtitle={labels.identitySubtitle}
                  hint={identityHint}
                >
                  <div className={classNames.identity}>
                    <InitialsAvatar
                      classNames={classNames.avatar}
                      className={classNames.identityAvatar}
                      name={identity.name}
                      colorKey={identity.colorKey}
                      src={identity.photoUrl ?? null}
                      size="lg"
                      previewTitle={identity.previewTitle}
                      previewAriaLabel={identity.previewAriaLabel}
                      portalScopeClassName={
                        identity.portalScopeClassName ?? portalScopeClassName
                      }
                    />
                    <dl className={classNames.identityFields}>
                      {resolveIdentityFields(identity, labels).map((field) => (
                        <div key={field.id} className={classNames.field}>
                          <dt className={classNames.fieldLabel}>
                            {field.icon}
                            <span>{field.label}</span>
                          </dt>
                          <dd className={classNames.fieldValue}>{field.value}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                  {identity.note ? <p className={classNames.note}>{identity.note}</p> : null}
                  {identity.actions ? (
                    <div className={classNames.identityActions}>{identity.actions}</div>
                  ) : null}
                </SectionCard>
              ) : null}

              {hasShortcuts ? (
                <SectionCard
                  classNames={classNames.section}
                  labels={labels.section}
                  title={labels.shortcutsTitle}
                  subtitle={labels.shortcutsSubtitle}
                  hint={shortcutsHint}
                >
                  <div className={classNames.shortcuts} aria-label={labels.shortcutsAriaLabel}>
                    {shortcuts!.map((item) => (
                      <ActionButton
                        key={item.id}
                        type="button"
                        title={item.title}
                        onClick={item.onSelect}
                      >
                        {item.icon}
                        {item.label}
                      </ActionButton>
                    ))}
                  </div>
                </SectionCard>
              ) : null}
            </div>
          ) : null}

          {sections ? <div className={classNames.sections}>{sections}</div> : null}
        </>
      ) : null}
    </section>
  );
}

export type DashboardPortalUserProfilePageProps = Omit<
  PortalUserProfilePageProps,
  "classNames" | "labels"
>;

export function createDashboardPortalUserProfilePage(config: {
  prefix: string;
  classNames?: Partial<
    Pick<PortalUserProfilePageClassNames, "pagePath" | "hero" | "section" | "avatar">
  >;
  /** Sobrescreve rótulos genéricos (o restante herda o bundle PT do kit). */
  labels?: Partial<PortalUserProfilePageLabels>;
  portalScopeClassName?: string;
}) {
  const classNames = portalUserProfilePageBemClasses(config.prefix, config.classNames);
  const labels: PortalUserProfilePageLabels = {
    ...PORTAL_USER_PROFILE_LABELS_PT,
    ...config.labels,
    section: config.labels?.section ?? PORTAL_USER_PROFILE_LABELS_PT.section,
  };
  return function DashboardPortalUserProfilePage(
    props: DashboardPortalUserProfilePageProps,
  ) {
    return (
      <PortalUserProfilePage
        classNames={classNames}
        labels={labels}
        portalScopeClassName={config.portalScopeClassName}
        {...props}
      />
    );
  };
}
