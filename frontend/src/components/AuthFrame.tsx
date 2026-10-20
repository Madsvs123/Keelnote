import type { ReactNode } from "react";

export function AuthFrame({ children }: { children: ReactNode }) {
  return (
    <section className="auth">
      <div className="auth-copy">
        <p className="kicker">Keelnote</p>
        <h1>The release log for software you maintain.</h1>
        <p className="lede">
          Notes sit in an unreleased bucket until you cut the next semantic version. One maintainer, your own
          products, and a changelog you can ship.
        </p>
      </div>
      <div className="auth-card">{children}</div>
    </section>
  );
}
