# Further work for Keelnote

Keelnote stays a changelog and release manager for one maintainer's own software. Later work should deepen that job: clearer notes, safer cuts, and exports the maintainer can publish. It should not grow a customer list, billing, or any store of other people's personal data.

The license stays MIT.

## Notes worth keeping

- Add a security kind, and a deprecated kind, without collapsing them into changed. The lint rules should know both.
- Let a breaking note carry a short migration hint: what a caller must do, and which version removes the old path. The compare view should show that hint when the note is only on one side.
- Warn before saving a note whose summary matches one already in the unreleased bucket or in the version being edited.
- Let a product keep its own saved templates, separate from the maintainer-wide list, so two products can use different wording.
- Import an existing Keep a Changelog file into unreleased notes, and refuse the import when lint finds a missing kind or an empty summary.

## Cuts and channels

- Treat a yanked version as history, not as the latest version shown on the product, while the notes stay attached and the number stays taken.
- When a pre-release exists for the current core, ask for an rc before the stable cut of that same core. Keep the explicit override for a maintainer who wants to skip it.
- Compare a version with the unreleased bucket, using the same markdown diff as a version-to-version compare.
- Show which notes arrived on alpha, which changed again on beta or rc, and which survived into the stable cut.
- Block a new cut while another draft of the same product is still unpublished, with a clear way to discard that draft first.
- Suggest a channel step (alpha, beta, rc) when the unreleased notes are still being tried, and reserve the stable suggestion for notes the checklist has already accepted.

## Publishing what shipped

- Render one version on its own, as well as the file that already contains every version.
- Build a short "what to announce" page from breaking notes and removals only.
- Offer a static page of published versions the maintainer can host next to the repository. Yanked versions stay listed and marked.
- Fill the tag checklist note with the exact tag name Keelnote expects, and leave a reminder to sign the tag. Keelnote does not create the git tag itself.
- Preview the release body that would be pasted into a repository release, using the same markdown as the changelog section for that version.

## Care of the log

- Record a product rename without breaking the slug used in exports and in `addnote`.
- Search across kind and the breaking flag, not only the summary text.
- Keep the unreleased preview, the full export, and the compare output in agreement when a note is edited, yanked, or moved.
- Add a command that lints a product from the shell and exits with a failure when a note is missing its kind or its summary.

## Out of scope

Keelnote does not manage customers, payments, support tickets, or accounts for anyone but the maintainer. It does not collect analytics on who read a changelog. Release work stays on the maintainer's own products, versions, notes, and checklist.
