import { useMutation, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { Check, FileText, Tag } from "lucide-react";
import { api, invalidateRelease } from "../api/client";
import type { ReleaseVersion } from "../api/types";
import { formatDay } from "../lib/dates";
import { errorText } from "../lib/errors";

const ITEMS = [
  { key: "tests", label: "Tests passed", hint: "The suite you trust is green.", icon: Check },
  { key: "notes", label: "Notes reviewed", hint: "The changelog says what shipped.", icon: FileText },
  { key: "tag", label: "Tag created", hint: "The tag matches this version.", icon: Tag },
] as const;

export function ChecklistCard({ version, productId }: { version: ReleaseVersion; productId: string }) {
  const queryClient = useQueryClient();
  const published = Boolean(version.released_on);
  const toggle = useMutation({
    mutationFn: (body: Partial<Pick<ReleaseVersion["checklist"], "tests" | "notes" | "tag">>) =>
      api.versions.updateChecklist(String(version.id), body),
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
          return (
            <button
              key={item.key}
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
