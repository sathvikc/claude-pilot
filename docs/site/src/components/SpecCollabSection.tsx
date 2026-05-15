import { ArrowRight, Link as LinkIcon, Users, MessageSquareText, Bell } from "lucide-react";
import { useInView } from "@/hooks/use-in-view";

const SpecCollabSection = () => {
  const [headerRef, headerInView] = useInView<HTMLDivElement>();
  const [cardsRef, cardsInView] = useInView<HTMLDivElement>();
  const [ctaRef, ctaInView] = useInView<HTMLDivElement>();

  return (
    <section
      id="spec-collaboration"
      className="py-16 lg:py-24 px-4 sm:px-6 relative bg-gradient-to-b from-transparent via-primary/[0.025] to-transparent"
    >
      <div className="max-w-6xl mx-auto">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

        {/* Header */}
        <div
          ref={headerRef}
          className={`text-center mb-12 ${headerInView ? "animate-fade-in-up" : "opacity-0"}`}
        >
          <span className="inline-block text-xs font-semibold tracking-widest uppercase text-primary/80 mb-3">
            Shift Left
          </span>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground mb-4">
            Catch flaws in the spec, not the PR.
          </h2>
          <p className="text-muted-foreground text-lg sm:text-xl max-w-3xl mx-auto">
            Review and annotate requirements with your team{" "}
            <span className="text-foreground font-medium">before a single line of code is written</span>.
            Wrong approach, missed edge case, unclear scope, weak architecture — spot it while it costs a sentence to change, not a refactor.
          </p>
        </div>

        {/* Three feature cards */}
        <div
          ref={cardsRef}
          className={`grid md:grid-cols-3 gap-6 mb-12 ${cardsInView ? "animate-fade-in-up animation-delay-100" : "opacity-0"}`}
        >
          {/* One link */}
          <div className="rounded-lg p-6 border border-border/50 bg-card">
            <div className="w-11 h-11 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
              <LinkIcon className="h-5 w-5 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              One link, many reviewers
            </h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Click <span className="font-mono text-foreground/80">Share with Teammates</span> once. The button is permanently replaced by a copyable link. Forward it to as many people as you like — no Pilot install required on their side.
            </p>
          </div>

          {/* Auto-grouped */}
          <div className="rounded-lg p-6 border border-primary/50 bg-card">
            <div className="w-11 h-11 bg-primary/20 rounded-xl flex items-center justify-center mb-4">
              <Users className="h-5 w-5 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              Feedback grouped by author
            </h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Teammate annotations stream back into your Console in 60 seconds — author-grouped, collapsible, deletable. Stored next to the spec so the agent reads them at the next review checkpoint.
            </p>
          </div>

          {/* Zero handoff */}
          <div className="rounded-lg p-6 border border-border/50 bg-card">
            <div className="w-11 h-11 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
              <Bell className="h-5 w-5 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              Zero handoff overhead
            </h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Reviewers click <span className="font-mono text-foreground/80">Submit</span> — no copy-URL-back step. Each submit produces a single notification in your Console: <span className="italic">"Bob left 3 annotations on auth-flow"</span>.
            </p>
          </div>
        </div>

        {/* Inline mini-flow */}
        <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-muted-foreground mb-10">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-card border border-border/50">
            <LinkIcon className="h-3.5 w-3.5 text-primary" />
            Share
          </span>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/50" />
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-card border border-border/50">
            <MessageSquareText className="h-3.5 w-3.5 text-primary" />
            Review in browser
          </span>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/50" />
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-card border border-border/50">
            <Bell className="h-3.5 w-3.5 text-primary" />
            Notification arrives
          </span>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/50" />
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-card border border-border/50">
            <Users className="h-3.5 w-3.5 text-primary" />
            Author-grouped in Console
          </span>
        </div>

        {/* CTA */}
        <div
          ref={ctaRef}
          className={`text-center ${ctaInView ? "animate-fade-in-up animation-delay-200" : "opacity-0"}`}
        >
          <a
            href="/docs/features/spec-collaboration"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors"
          >
            See how it works
            <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      </div>
    </section>
  );
};

export default SpecCollabSection;
