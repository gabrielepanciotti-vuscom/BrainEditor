import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { FilePenLine } from "lucide-react";
import { Alert, Badge, Button, Field, Input, PageHeader, Section, Textarea } from "@suite/design-system";
import { useT } from "../i18n/useT";
import { useEditorNota } from "./useEditorNota";

const REGOLE = [
  { id: "frontmatter", labelKey: "editor.ruleFrontmatter" },
  { id: "wikilink", labelKey: "editor.ruleWikilink" },
  { id: "lunghezza", labelKey: "editor.ruleLength" },
  { id: "classification", labelKey: "editor.ruleClassification" },
];

function Verifiche({ esito }) {
  const t = useT();
  if (!esito) return <p className="text-sm text-muted">{t("editor.checking")}</p>;
  return (
    <ul className="space-y-3">
      {REGOLE.map((r) => {
        const problemi = esito.problemi.filter((p) => p.regola === r.id);
        return (
          <li key={r.id}>
            <div className="flex items-center gap-2 text-sm">
              <Badge state={problemi.length ? "danger" : "success"} dot>
                {problemi.length ? t("editor.toFix") : t("editor.ok")}
              </Badge>
              <span>{t(r.labelKey)}</span>
            </div>
            {problemi.map((p) => (
              <p key={p.messaggio} className="ml-2 mt-1 text-xs text-muted">
                {p.messaggio}
              </p>
            ))}
          </li>
        );
      })}
      <li className="text-xs text-muted">
        {t("editor.stats", {
          links: esito.wikilink_validi,
          lines: esito.righe_corpo,
          classification: esito.classification || t("editor.notIndicated"),
        })}
      </li>
    </ul>
  );
}

export default function EditorNota() {
  const t = useT();
  const ed = useEditorNota();
  const [parametri] = useSearchParams();
  const daAprire = parametri.get("nota") || "";
  const [percorso, setPercorso] = useState(daAprire);
  const [messaggio, setMessaggio] = useState("");
  const { apri: apriNota } = ed;

  // Arriving from the area page (?nota=...): open that note straight away.
  useEffect(() => {
    if (daAprire) {
      setPercorso(daAprire);
      apriNota(daAprire);
    }
  }, [daAprire, apriNota]);

  const apri = (e) => {
    e.preventDefault();
    if (percorso.trim()) ed.apri(percorso.trim());
  };

  const stato = ed.info?.stato || t("editor.unspecified");

  return (
    <div className="space-y-6">
      <PageHeader icon={<FilePenLine size={20} />} title={t("editor.title")} subtitle={t("editor.description")} />
      <form onSubmit={apri} className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <Field label={t("editor.note")} hint={t("editor.noteHint")} className="flex-1">
          <Input value={percorso} onChange={(e) => setPercorso(e.target.value)} />
        </Field>
        <Button type="submit" loading={ed.caricamento}>
          {t("editor.open")}
        </Button>
      </form>

      {ed.errore && (
        <Alert variant="danger" title={t("editor.failed")}>
          {ed.errore}
        </Alert>
      )}
      {ed.commit && (
        <Alert variant="success" title={t("editor.saved")}>
          {t("editor.savedDetail", {
            sha: ed.commit.sha.slice(0, 7),
            branch: ed.commit.branch,
            state: ed.commit.stato,
          })}
        </Alert>
      )}

      {ed.nota && (
        <div className="grid gap-6 lg:grid-cols-3">
          <Section
            id="nota"
            collapsible={false}
            title={ed.nota}
            className="lg:col-span-2"
          >
            <p className="text-sm text-muted">
              {ed.info?.branch
                ? t("editor.review", { branch: ed.info.branch, state: stato })
                : t("editor.published", { state: stato })}
            </p>
            <Field label={t("editor.markdown")}>
              <Textarea
                rows={24}
                className="font-mono text-sm"
                value={ed.contenuto}
                onChange={(e) => ed.setContenuto(e.target.value)}
              />
            </Field>
          </Section>
          <Section id="regole" collapsible={false} title={t("editor.rules")}>
            <Verifiche esito={ed.esito} />
            <div className="mt-6 space-y-3">
              <Field label={t("editor.message")} hint={t("editor.messageHint")}>
                <Input value={messaggio} onChange={(e) => setMessaggio(e.target.value)} />
              </Field>
              <Button
                className="w-full"
                loading={ed.salvataggio}
                disabled={!ed.esito?.valida}
                onClick={() => ed.salva(messaggio)}
              >
                {t("editor.save")}
              </Button>
            </div>
          </Section>
        </div>
      )}
    </div>
  );
}
