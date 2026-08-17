import { delpiUiClass } from "../../utils/delpiUiClass";

export type DisplayFormatClassNames = {
  hint: string;
  menu: string;
  menuItem: string;
  menuItemActive: string;
  menuDesc: string;
  menuMore: string;
  group: string;
  groupCompact: string;
  trigger: string;
  shortcuts: string;
  shortcut: string;
  launcher: string;
  dialogBody: string;
  dialogHint: string;
  dialogGrid: string;
  categoryList: string;
  categoryBtn: string;
  categoryBtnActive: string;
  sample: string;
  sampleLabel: string;
  sampleValue: string;
  typeList: string;
  typeBtn: string;
  typeBtnActive: string;
  typeMeta: string;
  customField: string;
  customHelp: string;
  locale: string;
  footer: string;
};

export function displayFormatBemClasses(prefix = "delpi-ui"): DisplayFormatClassNames {
  const base = `${prefix}-display-format`;
  const ui = "delpi-ui-display-format";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    hint: pair(`${base}__hint`, `${ui}__hint`),
    menu: pair(`${base}__menu`, `${ui}__menu`),
    menuItem: pair(`${base}__menu-item`, `${ui}__menu-item`),
    menuItemActive: pair(`${base}__menu-item--active`, `${ui}__menu-item--active`),
    menuDesc: pair(`${base}__menu-desc`, `${ui}__menu-desc`),
    menuMore: pair(`${base}__menu-more`, `${ui}__menu-more`),
    group: pair(`${base}__group`, `${ui}__group`),
    groupCompact: pair(`${base}__group--compact`, `${ui}__group--compact`),
    trigger: pair(`${base}__trigger`, `${ui}__trigger`),
    shortcuts: pair(`${base}__shortcuts`, `${ui}__shortcuts`),
    shortcut: pair(`${base}__shortcut`, `${ui}__shortcut`),
    launcher: pair(`${base}__launcher`, `${ui}__launcher`),
    dialogBody: pair(`${base}__dialog-body`, `${ui}__dialog-body`),
    dialogHint: pair(`${base}__dialog-hint`, `${ui}__dialog-hint`),
    dialogGrid: pair(`${base}__dialog-grid`, `${ui}__dialog-grid`),
    categoryList: pair(`${base}__cats`, `${ui}__cats`),
    categoryBtn: pair(`${base}__cat`, `${ui}__cat`),
    categoryBtnActive: pair(`${base}__cat--active`, `${ui}__cat--active`),
    sample: pair(`${base}__sample`, `${ui}__sample`),
    sampleLabel: pair(`${base}__sample-label`, `${ui}__sample-label`),
    sampleValue: pair(`${base}__sample-value`, `${ui}__sample-value`),
    typeList: pair(`${base}__types`, `${ui}__types`),
    typeBtn: pair(`${base}__type`, `${ui}__type`),
    typeBtnActive: pair(`${base}__type--active`, `${ui}__type--active`),
    typeMeta: pair(`${base}__type-meta`, `${ui}__type-meta`),
    customField: pair(`${base}__custom`, `${ui}__custom`),
    customHelp: pair(`${base}__custom-help`, `${ui}__custom-help`),
    locale: pair(`${base}__locale`, `${ui}__locale`),
    footer: pair(`${base}__footer`, `${ui}__footer`),
  };
}

export const DEFAULT_DISPLAY_FORMAT_CN = displayFormatBemClasses();
