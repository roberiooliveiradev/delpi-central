/**
 * Página canônica de perfil de usuário de um portal.
 * OWNS: Hero (density comfortable), badge «Você», CTA «Editar no Meu Perfil»,
 * identidade (empty/helper), grid Identidade|Atalhos, responsive e a11y.
 * DOES NOT OWN: HTTP, AuthZ, cálculo de `isSelf`, rotas do portal, preferências
 * ou badges/seções/atalhos de domínio.
 *
 * `isSelf` e `onEditSelf` são estado já decidido pelo host — o kit só apresenta.
 */

import type { ReactNode } from "react";
import {
  BriefcaseBusiness,
  Mail,
  MessageCircle,
  Pencil,
  Phone,
  Smartphone,
  User,
} from "lucide-react";

import { ActionButton } from "../actions/ActionButton";
import {
  StatusBadge,
  statusBadgeBemClasses,
  type StatusBadgeClassNames,
} from "../feedback/StatusBadge";
import {
  InitialsAvatar,
  initialsAvatarBemClasses,
  type InitialsAvatarClassNames,
} from "./InitialsAvatar";
import {
  PageHero,
  pageHeroBemClasses,
  type PageHeroClassNames,
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
  /**
   * Contatos: chave ausente → omite a linha; chave presente com vazio/null →
   * «Não informado». O host só passa chaves que o contrato dele conhece.
   */
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
  /** Linhas adicionais do portal (ex.: unidades). */
  extraFields?: PortalUserProfileIdentityField[];
  /**
   * @deprecated Preferir `labels.identityHostNote` canônico. Override só se o
   * portal precisar de nota adicional (não para CTA de edição).
   */
  note?: ReactNode;
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
  /**
   * Badges extras além do self badge / `contextBadges`. Preferir `contextBadges`
   * na página; mantido para compatibilidade de composição.
   */
  badge?: ReactNode;
  /** Ações extras além do CTA self (o kit injeta «Editar no Meu Perfil»). */
  actions?: ReactNode;
};

export type PortalUserProfilePagePath = {
  back: PagePathLink;
  items?: PagePathItem[];
  current: string;
};

export type PortalUserProfileAccessClassNames = {
  access: string;
  accessGroup: string;
  accessHeading: string;
  accessBadges: string;
  accessList: string;
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
  shortcuts: string;
  sections: string;
  status: string;
  error: string;
  loading: string;
  pagePath: PagePathClassNames;
  hero: PageHeroClassNames;
  section: SectionCardClassNames;
  avatar: InitialsAvatarClassNames;
  selfBadge: StatusBadgeClassNames;
} & PortalUserProfileAccessClassNames;

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
  selfBadgeLabel: string;
  editSelfLabel: string;
  identityHostNote: string;
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
  /**
   * Já decidido pelo host (comparação de IDs). `null`/`undefined` = ainda
   * desconhecido — o kit omite chrome self.
   */
  isSelf?: boolean | null;
  /** Badges de domínio (carteiras, filiais). O kit prepende «Você» quando self. */
  contextBadges?: ReactNode;
  /** Abre Meu Perfil Minha DELPI. Só renderiza CTA quando `isSelf === true`. */
  onEditSelf?: () => void;
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
  selfBadgeLabel: "Você",
  editSelfLabel: "Editar no Meu Perfil",
  identityHostNote:
    "Foto, cargo e contatos são gerenciados no Meu Perfil da Minha DELPI.",
  section: {
    titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
  },
};

/**
 * Classes BEM do bloco «Acesso na plataforma» (chrome transversal).
 * Hosts usam nas seções de domínio; o CSS canônico é `.delpi-ui-portal-user-profile__*`.
 */
export function portalUserProfileAccessBemClasses(
  prefix: string,
): PortalUserProfileAccessClassNames {
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  const base = `${prefix}-portal-user-profile`;
  const ui = "delpi-ui-portal-user-profile";
  return {
    access: pair(`${base}__access`, `${ui}__access`),
    accessGroup: pair(`${base}__access-group`, `${ui}__access-group`),
    accessHeading: pair(`${base}__access-heading`, `${ui}__access-heading`),
    accessBadges: pair(`${base}__access-badges`, `${ui}__access-badges`),
    accessList: pair(`${base}__access-list`, `${ui}__access-list`),
  };
}

export function portalUserProfilePageBemClasses(
  prefix: string,
  overrides?: Partial<
    Pick<
      PortalUserProfilePageClassNames,
      "pagePath" | "hero" | "section" | "avatar" | "selfBadge"
    >
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
    shortcuts: pair(`${base}__shortcuts`, `${ui}__shortcuts`),
    sections: pair(`${base}__sections`, `${ui}__sections`),
    status: pair(`${base}__status`, `${ui}__status`),
    error: pair(`${base}__error`, `${ui}__error`),
    loading: pair(`${base}__loading`, `${ui}__loading`),
    ...portalUserProfileAccessBemClasses(prefix),
    pagePath: overrides?.pagePath ?? pagePathBemClasses(prefix),
    hero: overrides?.hero ?? pageHeroBemClasses(prefix),
    section: overrides?.section ?? sectionCardPacBemClasses(prefix),
    avatar: overrides?.avatar ?? initialsAvatarBemClasses(prefix),
    selfBadge: overrides?.selfBadge ?? statusBadgeBemClasses(prefix),
  };
}

function trimOrNull(value: string | null | undefined): string | null {
  const text = (value ?? "").trim();
  return text || null;
}

function hasOwn(
  identity: PortalUserProfileIdentity,
  key: keyof PortalUserProfileIdentity,
): boolean {
  return Object.prototype.hasOwnProperty.call(identity, key);
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
  const fields: ResolvedField[] = [
    {
      id: "name",
      label: labels.nameLabel,
      value: trimOrNull(identity.name) ?? labels.emptyValue,
      icon: <User size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
  ];

  if (hasOwn(identity, "email")) {
    fields.push({
      id: "email",
      label: labels.emailLabel,
      value: trimOrNull(identity.email) ?? labels.emptyValue,
      icon: <Mail size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    });
  }

  const contacts: Array<{
    key: "jobTitle" | "phone" | "mobile" | "whatsapp";
    id: string;
    label: ReactNode;
    icon: ReactNode;
  }> = [
    {
      key: "jobTitle",
      id: "jobTitle",
      label: labels.jobTitleLabel,
      icon: <BriefcaseBusiness size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
    {
      key: "phone",
      id: "phone",
      label: labels.phoneLabel,
      icon: <Phone size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
    {
      key: "mobile",
      id: "mobile",
      label: labels.mobileLabel,
      icon: <Smartphone size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
    {
      key: "whatsapp",
      id: "whatsapp",
      label: labels.whatsappLabel,
      icon: <MessageCircle size={iconSize} strokeWidth={1.75} aria-hidden="true" />,
    },
  ];

  for (const contact of contacts) {
    if (!hasOwn(identity, contact.key)) continue;
    fields.push({
      id: contact.id,
      label: contact.label,
      value: trimOrNull(identity[contact.key] as string | null | undefined) ?? labels.emptyValue,
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
  isSelf = null,
  contextBadges,
  onEditSelf,
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

  const selfChrome = isSelf === true;
  const heroBadges =
    selfChrome || contextBadges || hero?.badge ? (
      <>
        {selfChrome ? (
          <StatusBadge
            classNames={classNames.selfBadge}
            label={labels.selfBadgeLabel}
            variant="success"
          />
        ) : null}
        {contextBadges}
        {hero?.badge}
      </>
    ) : undefined;

  const heroActions =
    (selfChrome && onEditSelf) || hero?.actions ? (
      <>
        {selfChrome && onEditSelf ? (
          <ActionButton variant="primary" type="button" onClick={onEditSelf}>
            <Pencil size={16} aria-hidden="true" />
            {labels.editSelfLabel}
          </ActionButton>
        ) : null}
        {hero?.actions}
      </>
    ) : undefined;

  const identityNote = identity?.note ?? labels.identityHostNote;

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
              badge={heroBadges}
              actions={heroActions}
              density="comfortable"
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
                  {identityNote ? <p className={classNames.note}>{identityNote}</p> : null}
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
    Pick<
      PortalUserProfilePageClassNames,
      "pagePath" | "hero" | "section" | "avatar" | "selfBadge"
    >
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
