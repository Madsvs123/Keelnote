import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { errorText } from "../lib/errors";
import { productSchema, type ProductValues } from "../lib/schemas";

export function ProductsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const products = useQuery({ queryKey: ["products"], queryFn: api.products.list });
  const form = useForm<ProductValues>({
    resolver: zodResolver(productSchema),
    defaultValues: { name: "", summary: "", repository_url: "" },
  });
  const createProduct = useMutation({
    mutationFn: api.products.create,
    onSuccess: async (product) => {
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      navigate(`/products/${product.id}`);
    },
  });

  useEffect(() => {
    document.title = "Products · Keelnote";
  }, []);

  return (
    <div className="page stack">
      <header>
        <p className="kicker">Products</p>
        <h1 className="page-title">What you maintain</h1>
        <p className="lede">Each product has its own unreleased bucket, version line, and generated changelog.</p>
      </header>

      <section className="card stack">
        <h2>New product</h2>
        <form className="stack" onSubmit={form.handleSubmit((values) => createProduct.mutate(values))}>
          <div className="form-grid">
            <label className="field">
              <span>Name</span>
              <input placeholder="Harbor" {...form.register("name")} />
            </label>
            <label className="field">
              <span>Summary</span>
              <input placeholder="What this software is" {...form.register("summary")} />
            </label>
            <label className="field">
              <span>Repository URL</span>
              <input placeholder="https://example.com/harbor" {...form.register("repository_url")} />
            </label>
          </div>
          {form.formState.errors.name && <p className="error">{form.formState.errors.name.message}</p>}
          {form.formState.errors.summary && <p className="error">{form.formState.errors.summary.message}</p>}
          {form.formState.errors.repository_url && (
            <p className="error">{form.formState.errors.repository_url.message}</p>
          )}
          {createProduct.isError && (
            <p className="error">{errorText(createProduct.error, "The product could not be created.")}</p>
          )}
          <div className="row">
            <button className="btn btn-primary" type="submit" disabled={createProduct.isPending}>
              Create product
            </button>
          </div>
        </form>
      </section>

      {products.isLoading && <p className="muted">Loading the log…</p>}
      {products.isError && <p className="error">{errorText(products.error, "Products could not be loaded.")}</p>}
      {products.data && products.data.length === 0 && (
        <p className="empty">No products yet. Create one, then drop notes into its unreleased bucket.</p>
      )}
      {products.data && products.data.length > 0 && (
        <div className="product-grid">
          {products.data.map((product) => (
            <Link key={product.id} to={`/products/${product.id}`} className="product-card">
              <p className="kicker">{product.latest ?? "No release yet"}</p>
              <h2>{product.name}</h2>
              <p>{product.summary || "No summary yet."}</p>
              <p className="muted">
                {product.unreleased_count} unreleased {product.unreleased_count === 1 ? "note" : "notes"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
