import { useLanguage } from "@suite/i18n";

/** `t(key, vars)`: the provider's lookup plus `{name}` placeholders. */
export function useT() {
  const { t } = useLanguage();
  return (key, vars = {}) =>
    t(key).replace(/\{(\w+)\}/g, (m, name) => (name in vars ? String(vars[name]) : m));
}
