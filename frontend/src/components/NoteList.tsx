import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { api } from "../api/client";
import type { Entry } from "../api/types";
import { formatAgo } from "../lib/dates";
import { errorText } from "../lib/errors";
import { KIND_META, KIND_ORDER } from "../lib/kinds";
import { entrySchema, type EntryValues } from "../lib/schemas";

export function NoteList({
  entries,
  onChanged,
}: {
  entries: Entry[];
  onChanged: () => Promise<unknown> | void;
}) {
  const [editing, setEditing] = useState<number | null>(null);
  const remove = useMutation({
    mutationFn: (id: number) => api.entries.remove(id),
    onSuccess: () => onChanged(),
  });

  if (entries.length === 0) {
    return <p className="empty">No notes in this bucket yet.</p>;
  }

  const groups = KIND_ORDER.map((kind) => ({
    kind,
    notes: entries.filter((entry) => entry.kind === kind),
  })).filter((group) => group.notes.length > 0);

  return (
    <div className="stack">
      {groups.map((group) => {
        const meta = KIND_META[group.kind];
        const Icon = meta.icon;
        return (
          <section key={group.kind} className="stack">
            <h3 className={`pill pill-${group.kind}`}>
              <Icon size={14} />
              {meta.label}
            </h3>
            {group.notes.map((entry) =>
              editing === entry.id ? (
                <EditNote
                  key={entry.id}
                  entry={entry}
                  onDone={() => setEditing(null)}
                  onSaved={onChanged}
                />
              ) : (
                <article key={entry.id} className={`note note-${entry.kind}${entry.breaking ? " note-breaking" : ""}`}>
                  <div className="note-top">
                    <div className="stack">
                      {entry.breaking && <span className="badge badge-breaking">Breaking</span>}
                      <p>{entry.text}</p>
                    </div>
                    <div className="note-actions">
                      <button type="button" className="text-button" onClick={() => setEditing(entry.id)}>
                        <Pencil size={14} />
                        Edit
                      </button>
                      <button
                        type="button"
                        className="text-button"
                        onClick={() => {
                          if (window.confirm("Remove this note?")) remove.mutate(entry.id);
                        }}
                      >
                        <Trash2 size={14} />
                        Remove
                      </button>
                    </div>
                  </div>
                  <p className="muted">{formatAgo(entry.created_at)}</p>
                </article>
              ),
            )}
          </section>
        );
      })}
      {remove.isError && <p className="error">{errorText(remove.error, "The note could not be removed.")}</p>}
    </div>
  );
}

function EditNote({
  entry,
  onDone,
  onSaved,
}: {
  entry: Entry;
  onDone: () => void;
  onSaved: () => Promise<unknown> | void;
}) {
  const form = useForm<EntryValues>({
    resolver: zodResolver(entrySchema),
    defaultValues: { kind: entry.kind, text: entry.text, breaking: entry.breaking },
  });
  const mutation = useMutation({
    mutationFn: (values: EntryValues) => api.entries.update(entry.id, values),
    onSuccess: async () => {
      await onSaved();
      onDone();
    },
  });

  return (
    <form className="note stack" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <label className="field">
        <span>Kind</span>
        <select {...form.register("kind")}>
          {KIND_ORDER.map((kind) => (
            <option key={kind} value={kind}>
              {KIND_META[kind].label}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Note</span>
        <textarea rows={3} {...form.register("text")} />
      </label>
      <label className="check-line">
        <input type="checkbox" {...form.register("breaking")} />
        <span>Breaking change</span>
      </label>
      {form.formState.errors.text && <p className="error">{form.formState.errors.text.message}</p>}
      {mutation.isError && <p className="error">{errorText(mutation.error, "The note could not be updated.")}</p>}
      <div className="row">
        <button className="btn btn-primary btn-tiny" type="submit" disabled={mutation.isPending}>
          Save note
        </button>
        <button className="btn btn-ghost btn-tiny" type="button" onClick={onDone}>
          Cancel
        </button>
      </div>
    </form>
  );
}
