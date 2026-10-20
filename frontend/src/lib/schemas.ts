import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().trim().min(1, "Enter your username."),
  password: z.string().min(1, "Enter your password."),
});

export const registerSchema = z
  .object({
    username: z.string().trim().min(3, "Use at least 3 characters.").max(150),
    password: z.string().min(8, "Use at least 8 characters.").max(128),
    confirm: z.string(),
  })
  .refine((values) => values.password === values.confirm, {
    path: ["confirm"],
    message: "Those passwords do not match.",
  });

export const productSchema = z.object({
  name: z.string().trim().min(2, "Use at least 2 characters.").max(120),
  summary: z.string().trim().max(280),
  repository_url: z
    .string()
    .trim()
    .max(300)
    .refine((value) => value === "" || /^https?:\/\/\S+$/i.test(value), "Use an http or https URL."),
});

export const entrySchema = z.object({
  kind: z.enum(["added", "changed", "fixed", "removed"]),
  text: z.string().trim().min(1, "Write a note before saving.").max(2000),
});

export type LoginValues = z.infer<typeof loginSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;
export type ProductValues = z.infer<typeof productSchema>;
export type EntryValues = z.infer<typeof entrySchema>;
