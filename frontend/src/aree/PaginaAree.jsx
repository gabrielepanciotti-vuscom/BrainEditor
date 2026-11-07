import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { CircleHelp, FileText, FolderTree } from "lucide-react";
import {
  Alert,
  Badge,
  DataTable,
  Field,
  PageHeader,
  Section,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Spinner,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@suite/design-system";
import { PERCORSI } from "../app/percorsi";
import { useT } from "../i18n/useT";
import { useArea, useAree } from "./useArea";

const STATO_NOTA = { active: "success", review: "info", draft: "warning" };

// The register writes markdown emphasis; the page shows plain text.
const testo = (s) => s.replace(/\*\*|`/g, "");

const apriInEditor = (navigate, nota) =>
  navigate(`${PERCORSI.editor}?nota=${encodeURIComponent(nota)}`);

const LINK = "text-xs text-accent underline-offset-2 hover:underline";

function Domande({ domande, navigate }) {
  const t = useT();
  if (!domande.length) return <p className="text-sm text-muted">{t("areas.noQuestions")}</p>;
  return (
    <ul className="space-y-4">
      {domande.map((d) => (
        <li key={d.id} className="rounded-card border border-border p-4">
          <div className="flex items-start gap-3">
            <Badge state="warning">{d.id}</Badge>
            <div className="space-y-2">
              <p className="text-sm font-medium">{testo(d.domanda)}</p>
              {d.perche && <p className="text-xs text-muted">{testo(d.perche)}</p>}
              {d.note.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {d.note.map((n) =>
                    d.percorsi[n] ? (
                      <button
                        key={n}
                        type="button"
                        className={LINK}
                        onClick={() => apriInEditor(navigate, d.percorsi[n])}
                      >
                        {n}
                      </button>
                    ) : (
                      <span key={n} className="text-xs text-muted">
                        {n}
                      </span>
                    ),
                  )}
                </div>
              )}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

function Note({ note, caricamento, navigate }) {
  const t = useT();
  const colonne = [
    {
      key: "titolo",
      header: t("areas.colNote"),
      sortable: true,
      accessor: (r) => r.titolo,
      render: (r) => (
        <button type="button" className="text-sm text-accent hover:underline" onClick={() => apriInEditor(navigate, r.nota)}>
          {r.titolo}
        </button>
      ),
    },
    {
      key: "stato",
      header: t("areas.colState"),
      sortable: true,
      accessor: (r) => r.stato || "",
      render: (r) => <Badge state={STATO_NOTA[r.stato]}>{r.stato || "—"}</Badge>,
    },
    { key: "aggiornata", header: t("areas.colUpdated"), sortable: true, accessor: (r) => r.aggiornata || "" },
  ];
  if (caricamento) return <Spinner />;
  if (!note.length) return <p className="text-sm text-muted">{t("areas.noNotes")}</p>;
  return <DataTable columns={colonne} data={note} rowKey={(r) => r.nota} />;
}

export default function PaginaAree() {
  const t = useT();
  const navigate = useNavigate();
  const { aree, errore: erroreAree } = useAree();
  const [scelta, setScelta] = useState(null);
  const areaId = scelta || aree[0]?.id;
  const area = aree.find((a) => a.id === areaId);
  const { note, domande, caricamento, errore } = useArea(areaId);

  return (
    <div className="space-y-6">
      <PageHeader icon={<FolderTree size={20} />} title={t("areas.title")} subtitle={t("areas.description")} />
      <Field label={t("areas.area")} className="max-w-md">
        <Select value={areaId ?? ""} onValueChange={setScelta}>
          <SelectTrigger aria-label={t("areas.area")}>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {aree.map((a) => (
              <SelectItem key={a.id} value={a.id}>
                {a.nome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Field>

      {(erroreAree || errore) && (
        <Alert variant="danger" title={t("areas.readFailed")}>
          {erroreAree || errore}
        </Alert>
      )}

      {area && (
        <Section
          id={`area-${area.id}`}
          collapsible={false}
          title={area.nome}
        >
          <p className="text-sm text-muted">
            {`${area.descrizione} ${t("areas.folders")}: ${area.cartelle_brain.join(", ")}.`}
          </p>
          <Tabs defaultValue="domande">
            <TabsList>
              <TabsTrigger value="domande">
                <CircleHelp size={14} className="mr-1.5" aria-hidden />
                {t("areas.questionsTab", { n: domande.length })}
              </TabsTrigger>
              <TabsTrigger value="note">
                <FileText size={14} className="mr-1.5" aria-hidden />
                {t("areas.notesTab", { n: note.length })}
              </TabsTrigger>
            </TabsList>
            <TabsContent value="domande">
              <Domande domande={domande} navigate={navigate} />
            </TabsContent>
            <TabsContent value="note">
              <Note note={note} caricamento={caricamento} navigate={navigate} />
            </TabsContent>
          </Tabs>
        </Section>
      )}
    </div>
  );
}
