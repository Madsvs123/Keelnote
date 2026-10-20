export type Level = "major" | "minor" | "patch";

export type Channel = "alpha" | "beta" | "rc";

export type Kind = "added" | "changed" | "fixed" | "removed";

export type Product = {
  id: number;
  name: string;
  slug: string;
  summary: string;
  repository_url: string;
  latest: string | null;
  next_versions: Record<Level, string>;
  next_channels: Record<Channel, string | null>;
  unreleased_count: number;
  created_at: string;
  updated_at: string;
};

export type ProductInput = {
  name: string;
  summary?: string;
  repository_url?: string;
};

export type Checklist = {
  tests: boolean;
  notes: boolean;
  tag: boolean;
  tests_note: string;
  notes_note: string;
  tag_note: string;
  complete: boolean;
  updated_at: string;
};

export type ReleaseVersion = {
  id: number;
  product: number;
  label: string;
  major: number;
  minor: number;
  patch: number;
  prerelease: string;
  released_on: string | null;
  yanked_on: string | null;
  yank_reason: string;
  checklist: Checklist;
  note_count: number;
  created_at: string;
};

export type Entry = {
  id: number;
  product: number;
  version: number | null;
  version_label: string | null;
  kind: Kind;
  text: string;
  breaking: boolean;
  created_at: string;
};

export type Suggestion = {
  level: Level;
  label: string;
  reason: string;
  note_count: number;
  breaking: boolean;
};

export type LintIssue = {
  code: "missing_kind" | "empty_summary";
  message: string;
  index: number;
  entry?: number;
};

export type NoteTemplate = {
  id: number | null;
  slug: string;
  name: string;
  kind: Kind;
  body: string;
  builtin: boolean;
  created_at?: string;
};

export type SessionPayload = {
  id?: number;
  username: string;
  access: string;
  refresh: string;
};
