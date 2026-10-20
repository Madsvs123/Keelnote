import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { api } from "../api/client";
import type { Kind } from "../api/types";
import { errorText } from "../lib/errors";
import { KIND_ORDER, KIND_META } from "../lib/kinds";
import { entrySchema, type EntryValues } from "../lib/schemas";

export function EntryForm({
  productId,
  versionId = null,
  onSaved,
}: {
  productId: number;
  versionId?: number | null;
  onSaved: () => Promise<unknown> | void;
}) {
  const form = useForm<EntryValues>({
    resolver: zodResolver(entrySchema),
    defaultValues: { kind: "added", text: "", breaking: false },
  });
  const templates = useQuery({
    queryKey: ["templates"],
    queryFn: () => api.templates.list(),
  });
  const mutation = useMutation({
    mutationFn: (values: EntryValues) =>
      api.entries.create({
        product: productId,
        version: versionId,
        kind: values.kind,
        text: values.text,
        breaking: values.breaking,
      }),
    onSuccess: async () => {
      const kind = form.getValues("kind");
      form.reset({ kind, text: "", breaking: false });
      await onSaved();
    },
  });

  return (
    <form className="stack" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
      <label className="field">
        <span>Template</span>
        <select
          defaultValue=""
          onChange={(event) => {
            const key = event.target.value;
            const template = templates.data?.find((item) => (item.builtin ? item.slug : `saved-${item.id}`) === key);
            if (!template) return;
            form.setValue("kind", template.kind as Kind, { shouldValidate: true });
            form.setValue("text", template.body, { shouldValidate: true });
            event.target.value = "";
          }}
        >
          <option value="">Start from a template</option>
          {templates.data?.map((template) => (
            <option key={template.builtin ? template.slug : template.id} value={template.builtin ? template.slug : `saved-${template.id}`}>
              {template.name}
              {template.builtin ? "" : " (saved)"}
            </option>
          ))}
        </select>
      </label>
      <div className="form-grid">
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
          <textarea rows={3} placeholder="What changed, in the maintainer's own words" {...form.register("text")} />
        </label>
      </div>
      <label className="check-line">
        <input type="checkbox" {...form.register("breaking")} />
        <span>Breaking change</span>
      </label>
      {form.formState.errors.text && <p className="error">{form.formState.errors.text.message}</p>}
      {mutation.isError && <p className="error">{errorText(mutation.error, "The note could not be saved.")}</p>}
      <div className="row">
        <button className="btn btn-primary" type="submit" disabled={mutation.isPending}>
          {versionId ? "Add to this version" : "Add to unreleased"}
        </button>
      </div>
    </form>
  );
}
