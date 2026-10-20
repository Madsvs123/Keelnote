import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { api } from "../api/client";
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
