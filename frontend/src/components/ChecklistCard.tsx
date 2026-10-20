import { useMutation, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { Check, FileText, Tag } from "lucide-react";
import { api, invalidateRelease } from "../api/client";
import type { ReleaseVersion } from "../api/types";
import { formatDay } from "../lib/dates";
import { errorText } from "../lib/errors";

const ITEMS = [
  { key: "tests", note: "tests_note", label: "Tests passed", hint: "The suite you trust is green.", icon: Check },
  { key: "notes", note: "notes_note", label: "Notes reviewed", hint: "The changelog says what shipped.", icon: FileText },
  { key: "tag", note: "tag_note", label: "Tag created", hint: "The tag matches this version.", icon: Tag },
] as const;

export function ChecklistCard({ version, productId }: { version: ReleaseVersion; productId: string }) {
  const queryClient = useQueryClient();
  const published = Boolean(version.released_on);
  const toggle = useMutation({
    mutationFn: (
      body: Partial<
        Pick<ReleaseVersion["checklist"], "tests" | "notes" | "tag" | "tests_note" | "notes_note" | "tag_note">
      >,
    ) => api.versions.updateChecklist(String(version.id), body),
    onSuccess: () => invalidateRelease(queryClient, productId, String(version.id)),
  });
  const publish = useMutation({
    mutationFn: () => api.versions.publish(String(version.id)),
    onSuccess: () => invalidateRelease(queryClient, productId, String(version.id)),
  });

  return (
    <section className="card stack">
      <div className="card-head">
        <h2>Release checklist</h2>
        {published && version.released_on ? (
          <span className="badge badge-live">Published {formatDay(version.released_on)}</span>
        ) : (
          <span className="badge badge-draft">{version.checklist.complete ? "Ready to publish" : "Draft"}</span>
        )}
      </div>
      <div className="checks">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          const checked = version.checklist[item.key];
          const note = version.checklist[item.note];
          return (
            <div key={item.key} className="check-block">
              <button
                type="button"
                className={clsx("check", checked && "is-on")}
                disabled={published || toggle.isPending}
                onClick={() => toggle.mutate({ [item.key]: !checked })}
              >
                <Icon size={16} />
                <span>
                  <strong>{item.label}</strong>
                  <small>{item.hint}</small>
                </span>
              </button>
              <label className="field">
                <span>Note</span>
                <input
                  key={`${item.note}-${version.checklist.updated_at}`}
                  defaultValue={note}
                  maxLength={400}
                  placeholder="What you checked, in a sentence"
                  disabled={published || toggle.isPending}
                  onBlur={(event) => {
                    const next = event.target.value.trim();
                    if (next !== note) toggle.mutate({ [item.note]: next });
                  }}
                />
              </label>
            </div>
          );
        })}
      </div>
      {toggle.isError && <p className="error">{errorText(toggle.error, "The checklist could not be updated.")}</p>}
      {publish.isError && <p className="error">{errorText(publish.error, "This version could not be published.")}</p>}
      {!published && (
        <button
          className="btn btn-primary"
          type="button"
          disabled={!version.checklist.complete || publish.isPending}
          onClick={() => publish.mutate()}
        >
          Publish release
        </button>
      )}
    </section>
  );
}
