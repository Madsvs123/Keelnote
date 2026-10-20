import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, invalidateRelease } from "../api/client";
import type { Channel, Level } from "../api/types";
import { EntryForm } from "../components/EntryForm";
import { MarkdownPanel } from "../components/MarkdownPanel";
import { NoteList } from "../components/NoteList";
import { formatDay } from "../lib/dates";
import { errorText } from "../lib/errors";
import { productSchema, type ProductValues } from "../lib/schemas";

const LEVELS: Level[] = ["patch", "minor", "major"];
const CHANNELS: Channel[] = ["alpha", "beta", "rc"];

export function ProductPage() {
  const { productId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pre, setPre] = useState("");
  const [editing, setEditing] = useState(false);
  const [leftId, setLeftId] = useState("");
  const [rightId, setRightId] = useState("");
  const productQuery = useQuery({
    queryKey: ["product", productId],
    queryFn: () => api.products.get(productId),
  });
  const entriesQuery = useQuery({
    queryKey: ["entries", productId, "unreleased"],
    queryFn: () => api.entries.list({ product: productId, bucket: "unreleased" }),
  });
  const versionsQuery = useQuery({
    queryKey: ["versions", productId],
    queryFn: () => api.versions.list(productId),
  });
  const changelogQuery = useQuery({
    queryKey: ["changelog", productId],
    queryFn: () => api.products.changelog(productId),
  });
  const compareQuery = useQuery({
    queryKey: ["compare", productId, leftId, rightId],
    queryFn: () => api.products.compare(productId, leftId, rightId),
    enabled: Boolean(leftId && rightId && leftId !== rightId),
  });
  const form = useForm<ProductValues>({
    resolver: zodResolver(productSchema),
    defaultValues: { name: "", summary: "", repository_url: "" },
  });

  useEffect(() => {
    document.title = productQuery.data ? `${productQuery.data.name} · Keelnote` : "Keelnote";
  }, [productQuery.data]);

  const refresh = () => invalidateRelease(queryClient, productId);
  const bump = useMutation({
    mutationFn: (level: Level | Channel) =>
      api.products.bump(
        productId,
        level === "alpha" || level === "beta" || level === "rc"
          ? { level }
          : { level, prerelease: pre.trim().replace(/^-/, "") },
      ),
    onSuccess: async (version) => {
      setPre("");
      await refresh();
      navigate(`/products/${productId}/versions/${version.id}`);
    },
  });
  const saveProduct = useMutation({
    mutationFn: (values: ProductValues) => api.products.update(productId, values),
    onSuccess: async () => {
      setEditing(false);
      await refresh();
    },
  });
  const removeProduct = useMutation({
    mutationFn: () => api.products.remove(productId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      navigate("/");
    },
  });

  if (productQuery.isLoading) return <p className="page muted">Loading the log…</p>;
  if (productQuery.isError || !productQuery.data) {
    return (
      <div className="page stack">
        <h1 className="page-title">This product is not in your log.</h1>
        <Link to="/" className="btn btn-ghost">
          Back to products
        </Link>
      </div>
    );
  }

  const product = productQuery.data;
  const suffix = pre.trim().replace(/^-/, "");

  return (
    <div className="page stack">
      <header className="split">
        <div>
          <p className="kicker">{product.slug}</p>
          <h1 className="page-title">{product.name}</h1>
          <p className="lede">{product.summary || "No summary yet."}</p>
          {product.repository_url && (
            <a className="link-quiet" href={product.repository_url} target="_blank" rel="noreferrer">
              {product.repository_url}
            </a>
          )}
        </div>
        <div className="row">
          <button
            className="btn btn-ghost"
            type="button"
            onClick={() => {
              form.reset({
                name: product.name,
                summary: product.summary,
                repository_url: product.repository_url,
              });
              setEditing((open) => !open);
            }}
          >
            {editing ? "Close editor" : "Edit product"}
          </button>
        </div>
      </header>

      {editing && (
        <form className="card stack" onSubmit={form.handleSubmit((values) => saveProduct.mutate(values))}>
          <label className="field">
            <span>Name</span>
            <input {...form.register("name")} />
          </label>
          <label className="field">
            <span>Summary</span>
            <input {...form.register("summary")} />
          </label>
          <label className="field">
            <span>Repository URL</span>
            <input {...form.register("repository_url")} />
          </label>
          {form.formState.errors.name && <p className="error">{form.formState.errors.name.message}</p>}
          {form.formState.errors.repository_url && (
            <p className="error">{form.formState.errors.repository_url.message}</p>
          )}
          {saveProduct.isError && <p className="error">{errorText(saveProduct.error, "The product could not be saved.")}</p>}
          <div className="row">
            <button className="btn btn-primary" type="submit" disabled={saveProduct.isPending}>
              Save product
            </button>
          </div>
        </form>
      )}

      <section className="card bump">
        <div>
          <h2>Cut a version</h2>
          <p className="muted">
            {product.unreleased_count} unreleased {product.unreleased_count === 1 ? "note" : "notes"} will move into
            the new version. Leave the pre-release label blank for a stable cut, or step alpha, then beta, then rc.
          </p>
        </div>
        <label className="field pre-field">
          <span>Pre-release label</span>
          <input value={pre} onChange={(event) => setPre(event.target.value)} placeholder="rc.1" />
        </label>
        <div className="row wrap">
          {LEVELS.map((level) => (
            <button
              key={level}
              className="btn btn-brass"
              type="button"
              disabled={bump.isPending}
              onClick={() => bump.mutate(level)}
            >
              Cut {product.next_versions[level]}
              {suffix ? `-${suffix}` : ""}
            </button>
          ))}
        </div>
        <div className="row wrap">
          {CHANNELS.map((channel) => {
            const label = product.next_channels[channel];
            return (
              <button
                key={channel}
                className="btn btn-ghost"
                type="button"
                disabled={bump.isPending || !label}
                onClick={() => bump.mutate(channel)}
              >
                Cut {label ?? channel}
              </button>
            );
          })}
        </div>
        {bump.isError && <p className="error">{errorText(bump.error, "The version could not be cut.")}</p>}
      </section>

      <div className="grid-main">
        <section className="card stack">
          <div className="card-head">
            <h2>Unreleased</h2>
            <span className="badge badge-draft">{entriesQuery.data?.length ?? 0}</span>
          </div>
          <EntryForm productId={product.id} onSaved={refresh} />
          {entriesQuery.isLoading && <p className="muted">Loading notes…</p>}
          {entriesQuery.data && <NoteList entries={entriesQuery.data} onChanged={refresh} />}
        </section>
        <MarkdownPanel markdown={changelogQuery.data} pending={changelogQuery.isLoading} />
      </div>

      <section className="card stack">
        <h2>Compare two versions</h2>
        <p className="muted">A markdown diff of the notes. Matching notes share a kind, a summary, and the breaking flag.</p>
        {(versionsQuery.data?.length ?? 0) < 2 && <p className="empty">Cut two versions before comparing them.</p>}
        {(versionsQuery.data?.length ?? 0) >= 2 && (
          <div className="compare-grid">
            <label className="field">
              <span>Left</span>
              <select value={leftId} onChange={(event) => setLeftId(event.target.value)}>
                <option value="">Choose a version</option>
                {versionsQuery.data?.map((version) => (
                  <option key={version.id} value={String(version.id)}>
                    {version.label}
                    {version.yanked_on ? " (yanked)" : ""}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Right</span>
              <select value={rightId} onChange={(event) => setRightId(event.target.value)}>
                <option value="">Choose a version</option>
                {versionsQuery.data?.map((version) => (
                  <option key={version.id} value={String(version.id)}>
                    {version.label}
                    {version.yanked_on ? " (yanked)" : ""}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        {leftId && leftId === rightId && <p className="error">Choose two different versions.</p>}
        {compareQuery.isError && <p className="error">{errorText(compareQuery.error, "Those versions could not be compared.")}</p>}
        {(compareQuery.data || compareQuery.isFetching) && (
          <MarkdownPanel
            markdown={compareQuery.data?.markdown}
            pending={compareQuery.isFetching}
            title={compareQuery.data ? `Compare ${compareQuery.data.left} and ${compareQuery.data.right}` : "Compare"}
            filename="compare.md"
          />
        )}
      </section>

      <section className="stack">
        <h2>Versions</h2>
        {versionsQuery.data && versionsQuery.data.length === 0 && <p className="empty">No versions cut yet.</p>}
        <div className="version-list">
          {versionsQuery.data?.map((version) => {
            const done = [version.checklist.tests, version.checklist.notes, version.checklist.tag].filter(Boolean)
              .length;
            return (
              <Link key={version.id} className="version-row" to={`/products/${productId}/versions/${version.id}`}>
                <strong>{version.label}</strong>
                <span>{version.released_on ? formatDay(version.released_on) : "Draft"}</span>
                <span>
                  {version.note_count} {version.note_count === 1 ? "note" : "notes"}
                </span>
                <span>
                  {done}/3 checklist
                </span>
                <span>{version.yanked_on ? "Yanked" : ""}</span>
              </Link>
            );
          })}
        </div>
      </section>

      <div>
        <button
          className="btn btn-danger"
          type="button"
          onClick={() => {
            if (window.confirm(`Delete ${product.name} and its release log?`)) removeProduct.mutate();
          }}
        >
          Delete product
        </button>
        {removeProduct.isError && (
          <p className="error">{errorText(removeProduct.error, "The product could not be deleted.")}</p>
        )}
      </div>
    </div>
  );
}
