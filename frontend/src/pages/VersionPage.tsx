import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, invalidateRelease } from "../api/client";
import { ChecklistCard } from "../components/ChecklistCard";
import { EntryForm } from "../components/EntryForm";
import { MarkdownPanel } from "../components/MarkdownPanel";
import { NoteList } from "../components/NoteList";
import { formatDay } from "../lib/dates";
import { errorText } from "../lib/errors";

export function VersionPage() {
  const { productId = "", versionId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [reason, setReason] = useState("");
  const versionQuery = useQuery({
    queryKey: ["version", versionId],
    queryFn: () => api.versions.get(versionId),
  });
  const entriesQuery = useQuery({
    queryKey: ["entries", productId, "version", versionId],
    queryFn: () => api.entries.list({ product: productId, version: versionId }),
  });
  const changelogQuery = useQuery({
    queryKey: ["changelog", productId],
    queryFn: () => api.products.changelog(productId),
  });
  const remove = useMutation({
    mutationFn: () => api.versions.remove(versionId),
    onSuccess: async () => {
      await invalidateRelease(queryClient, productId);
      navigate(`/products/${productId}`);
    },
  });
  const yank = useMutation({
    mutationFn: () => api.versions.yank(versionId, reason),
    onSuccess: async () => {
      setReason("");
      await invalidateRelease(queryClient, productId, versionId);
    },
  });

  useEffect(() => {
    document.title = versionQuery.data ? `${versionQuery.data.label} · Keelnote` : "Keelnote";
  }, [versionQuery.data]);

  if (versionQuery.isLoading) return <p className="page muted">Loading the version…</p>;
  if (versionQuery.isError || !versionQuery.data) {
    return (
      <div className="page stack">
        <h1 className="page-title">This version is not in the log.</h1>
        <Link to={`/products/${productId}`} className="btn btn-ghost">
          Back to the product
        </Link>
      </div>
    );
  }

  const version = versionQuery.data;
  const refresh = () => invalidateRelease(queryClient, productId, versionId);

  return (
    <div className="page stack">
      <header className="split">
        <div>
          <p className="kicker">
            <Link to={`/products/${productId}`}>Product</Link>
          </p>
          <h1 className="page-title">{version.label}</h1>
          <p className="lede">
            {version.yanked_on
              ? `Yanked ${formatDay(version.yanked_on)}. The notes stay on this version.`
              : version.released_on
                ? `Published ${formatDay(version.released_on)}`
                : "Draft, still open for notes."}
          </p>
        </div>
        {version.yanked_on && <span className="badge badge-yanked">Yanked</span>}
        {!version.released_on && (
          <button
            className="btn btn-danger"
            type="button"
            onClick={() => {
              if (window.confirm("Delete this draft and return its notes to unreleased?")) remove.mutate();
            }}
          >
            Delete draft
          </button>
        )}
      </header>
      {remove.isError && <p className="error">{errorText(remove.error, "The draft could not be deleted.")}</p>}

      {version.released_on && !version.yanked_on && (
        <form
          className="card stack"
          onSubmit={(event) => {
            event.preventDefault();
            yank.mutate();
          }}
        >
          <h2>Yank this release</h2>
          <p className="muted">The version and its notes stay in the log. Say why it should not be used.</p>
          <label className="field">
            <span>Reason</span>
            <input value={reason} onChange={(event) => setReason(event.target.value)} maxLength={280} />
          </label>
          {yank.isError && <p className="error">{errorText(yank.error, "This version could not be yanked.")}</p>}
          <div className="row">
            <button className="btn btn-danger" type="submit" disabled={yank.isPending || reason.trim().length < 3}>
              Yank {version.label}
            </button>
          </div>
        </form>
      )}
      {version.yanked_on && version.yank_reason && (
        <p className="card muted">
          <strong>Yank reason. </strong>
          {version.yank_reason}
        </p>
      )}

      <div className="grid-main">
        <div className="stack">
          <ChecklistCard version={version} productId={productId} />
          <section className="card stack">
            <h2>Notes in {version.label}</h2>
            <EntryForm productId={version.product} versionId={version.id} onSaved={refresh} />
            {entriesQuery.isLoading && <p className="muted">Loading notes…</p>}
            {entriesQuery.data && <NoteList entries={entriesQuery.data} onChanged={refresh} />}
          </section>
        </div>
        <MarkdownPanel markdown={changelogQuery.data} pending={changelogQuery.isLoading} />
      </div>
    </div>
  );
}
