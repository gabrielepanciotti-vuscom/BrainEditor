import { LanguageProvider } from "@suite/i18n";
import { translations } from "./translations";

export default function Lingue({ children }) {
  return (
    <LanguageProvider translations={translations} defaultLanguage="it">
      {children}
    </LanguageProvider>
  );
}
