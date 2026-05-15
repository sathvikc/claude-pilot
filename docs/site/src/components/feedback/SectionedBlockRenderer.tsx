import { useState, useEffect, useMemo } from "react";
import {
  AlertTriangle,
  BookOpen,
  Bookmark,
  Brain,
  CheckSquare,
  ChevronDown,
  ClipboardCheck,
  ClipboardList,
  Compass,
  Cpu,
  Crosshair,
  FileText,
  HelpCircle,
  Lightbulb,
  ListTree,
  MonitorCheck,
  MousePointerClick,
  Route,
  Scale,
  SquareX,
  Target,
  Terminal,
  Text as TextIcon,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { BlockRenderer } from "./BlockRenderer";
import { extractObjectiveBlocks, stripLabelPrefix } from "./sectioned-block-helpers";
import type { Annotation, Block } from "@/lib/annotation/types";

/**
 * Section-aware wrapper around BlockRenderer for pilot-shell.com / shared
 * spec viewing.
 *
 * Grouping levels:
 *  - H2 (`##`) → top-level collapsible section.
 *  - Inside `## Implementation Tasks` / `## Tasks`, `### Task N:` H3 → per-task collapsible.
 *  - Inside each task, paragraphs whose content is `**Label:**` → per-field collapsible.
 *
 * Heading blocks are NOT re-rendered inside their own card — the card title
 * already shows the heading. Annotation auto-expand still works by checking
 * the heading block id alongside the body blocks.
 */

interface SectionedBlockRendererProps {
  blocks: Block[];
  annotations: Annotation[];
  selectedAnnotationId: string | null;
  onSelectAnnotation?: (id: string) => void;
  onQuickAnnotate?: (
    blockId: string,
    originalText: string,
    annotationText: string,
  ) => void;
}

interface H2Group {
  heading: string;
  headingBlock: Block;
  blocks: Block[];
}

interface TaskGroup {
  number: number;
  title: string;
  /** null when this group holds prelude blocks that appeared before the first `### Task N:` heading. */
  headingBlock: Block | null;
  blocks: Block[];
}

interface FieldGroup {
  label: string;
  blocks: Block[];
}

// Map section headings to lucide icons (ported from console SpecSection.tsx).
const SECTION_ICONS: Record<string, LucideIcon> = {
  // Spec sections
  Summary: TextIcon,
  Approach: Compass,
  "Fix Approach": Wrench,
  "Feature Inventory": ClipboardList,
  Scope: Target,
  "Out of Scope": SquareX,
  "Autonomous Decisions": Brain,
  "Context for Implementer": BookOpen,
  "Runtime Environment": Terminal,
  Assumptions: Lightbulb,
  "Risks and Mitigations": AlertTriangle,
  "Goal Verification": CheckSquare,
  "E2E Test Scenarios": MonitorCheck,
  "E2E Results": ClipboardCheck,
  "Verification Scenario": MousePointerClick,
  "Open Questions": HelpCircle,
  "Deferred Ideas": Bookmark,
  "Implementation Details": ListTree,
  "Implementation Tasks": ListTree,
  Tasks: ListTree,
  Investigation: HelpCircle,
  "Behavior Contract": Scale,
  // PRD sections
  "Problem Statement": Crosshair,
  "Core User Flows": Route,
  "Technical Context": Cpu,
  "Key Decisions": Scale,
};

// Plan-header metadata paragraph: `Created: …\nAuthor: …\nStatus: …\n…`.
// Hidden from the shared view — reviewers don't review progress.
const PLAN_METADATA_RE = /^(Created|Author|Status|Approved|Iterations|Worktree|Type):/m;

function isPlanMetadataBlock(block: Block): boolean {
  return block.type === "paragraph" && PLAN_METADATA_RE.test(block.content);
}

// Top-of-tasks-section progress checklist: `- [x] Task N: …`. Hidden from
// the shared view because each task already renders as its own collapsible.
function isTaskProgressChecklistItem(block: Block): boolean {
  return (
    block.type === "list-item" &&
    typeof block.checked === "boolean" &&
    /^Task\s+\d+:/.test(block.content)
  );
}

function groupByH2(blocks: Block[]): H2Group[] {
  const groups: H2Group[] = [];
  let current: H2Group | null = null;
  for (const block of blocks) {
    if (block.type === "heading" && block.level === 2) {
      if (current) groups.push(current);
      // Heading block is NOT in .blocks — the CollapsibleCard title shows it.
      current = { heading: block.content, headingBlock: block, blocks: [] };
    } else if (current) {
      current.blocks.push(block);
    } else {
      current = { heading: "", headingBlock: block, blocks: [block] };
    }
  }
  if (current) groups.push(current);
  return groups.filter((g) => g.heading || g.blocks.length > 0);
}

function groupByTaskH3(blocks: Block[]): TaskGroup[] {
  const groups: TaskGroup[] = [];
  let current: TaskGroup | null = null;
  const prelude: Block[] = [];
  for (const block of blocks) {
    if (block.type === "heading" && block.level === 3) {
      const m = block.content.match(/^Task\s+(\d+):\s*(.+)$/);
      if (m) {
        if (current) groups.push(current);
        else if (prelude.length > 0) {
          groups.push({ number: 0, title: "", headingBlock: null, blocks: prelude.splice(0) });
        }
        current = {
          number: parseInt(m[1], 10),
          title: m[2].trim(),
          headingBlock: block,
          // Heading block is NOT in .blocks — the CollapsibleCard title shows it.
          blocks: [],
        };
        continue;
      }
    }
    if (current) current.blocks.push(block);
    else prelude.push(block);
  }
  if (current) groups.push(current);
  else if (prelude.length > 0) {
    groups.push({ number: 0, title: "", headingBlock: null, blocks: prelude });
  }
  return groups;
}

function matchLabelMarker(block: Block): string | null {
  if (block.type !== "paragraph") return null;
  const m = block.content.match(/^\*\*([A-Za-z][A-Za-z0-9 /]+):\*\*\s*(.*)$/s);
  if (!m) return null;
  return m[1].trim();
}

function groupByLabel(blocks: Block[]): FieldGroup[] {
  const groups: FieldGroup[] = [];
  let current: FieldGroup | null = null;
  for (const block of blocks) {
    const label = matchLabelMarker(block);
    if (label) {
      if (current) groups.push(current);
      const stripped = stripLabelPrefix(block, label);
      current = { label, blocks: stripped ? [stripped] : [] };
      continue;
    }
    if (current) current.blocks.push(block);
    // No leading-`**Label:**` block → blocks go into the parent task body
    // directly (no synthetic "Notes" group that just mirrors the title).
  }
  if (current) groups.push(current);
  return groups;
}

interface CollapsibleCardProps {
  title: React.ReactNode;
  icon?: LucideIcon;
  defaultOpen: boolean;
  expanded?: boolean;
  rightSlot?: React.ReactNode;
  children: React.ReactNode;
}

function CollapsibleCard({
  title,
  icon: SectionIcon,
  defaultOpen,
  expanded,
  rightSlot,
  children,
}: CollapsibleCardProps) {
  const [open, setOpen] = useState(defaultOpen);
  const isOpen = expanded ?? open;
  const setIsOpen = (next: boolean) => setOpen(next);
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2.5 px-4 py-3 text-left cursor-pointer hover:bg-muted/50 transition-colors"
      >
        {SectionIcon && (
          <SectionIcon size={14} className="text-primary flex-shrink-0" />
        )}
        <div className="flex-1 text-sm font-semibold">{title}</div>
        {rightSlot}
        <ChevronDown
          size={14}
          className={cn(
            "text-muted-foreground/60 transition-transform duration-200",
            isOpen ? "rotate-180" : "",
          )}
        />
      </button>
      {isOpen && (
        <div className="px-4 pb-4 pt-0 border-t border-border/50">
          <div className="pt-3">{children}</div>
        </div>
      )}
    </div>
  );
}

export function SectionedBlockRenderer({
  blocks,
  annotations,
  selectedAnnotationId,
  onSelectAnnotation,
  onQuickAnnotate,
}: SectionedBlockRendererProps) {
  const sections = useMemo(() => groupByH2(blocks), [blocks]);

  const [forceOpenBlockId, setForceOpenBlockId] = useState<string | null>(null);
  useEffect(() => {
    if (!selectedAnnotationId) {
      setForceOpenBlockId(null);
      return;
    }
    const ann = annotations.find((a) => a.id === selectedAnnotationId);
    setForceOpenBlockId(ann?.blockId ?? null);
  }, [selectedAnnotationId, annotations]);

  const renderLeaf = (groupBlocks: Block[]) => (
    <BlockRenderer
      blocks={groupBlocks}
      annotations={annotations}
      selectedAnnotationId={selectedAnnotationId}
      onSelectAnnotation={onSelectAnnotation}
      onQuickAnnotate={onQuickAnnotate}
    />
  );

  const containsBlockOrHeading = (
    groupBlocks: Block[],
    headingBlock: Block | null,
    targetId: string | null,
  ): boolean => {
    if (!targetId) return false;
    if (headingBlock && headingBlock.id === targetId) return true;
    return groupBlocks.some((b) => b.id === targetId);
  };

  return (
    <div className="space-y-2">
      {sections.map((section) => {
        const isTaskSection =
          section.heading === "Implementation Tasks" ||
          section.heading === "Tasks";
        const sectionForceOpen = containsBlockOrHeading(
          section.blocks,
          section.headingBlock,
          forceOpenBlockId,
        );
        if (!section.heading) {
          // Preamble before the first H2: drop the plan-metadata paragraph
          // so reviewers don't see Status/Iterations/Approved/etc.
          const preambleBlocks = section.blocks.filter(
            (b) => !isPlanMetadataBlock(b),
          );
          if (preambleBlocks.length === 0) return null;
          return (
            <div key={`preamble-${section.headingBlock.id}`}>
              {renderLeaf(preambleBlocks)}
            </div>
          );
        }
        const SectionIcon = SECTION_ICONS[section.heading] ?? FileText;
        return (
          <CollapsibleCard
            key={section.headingBlock.id}
            title={section.heading}
            icon={SectionIcon}
            defaultOpen={true}
            expanded={sectionForceOpen || undefined}
          >
            {isTaskSection ? (
              <div className="space-y-2">
                {groupByTaskH3(section.blocks).map((task) => {
                  const taskForceOpen = containsBlockOrHeading(
                    task.blocks,
                    task.headingBlock,
                    forceOpenBlockId,
                  );
                  // Prelude blocks (before the first `### Task N:`): drop
                  // the progress checklist (`- [x] Task N: …`) — the
                  // per-task cards below already show each task.
                  if (task.headingBlock === null) {
                    const preludeBlocks = task.blocks.filter(
                      (b) => !isTaskProgressChecklistItem(b),
                    );
                    if (preludeBlocks.length === 0) return null;
                    return (
                      <div key={`prelude-${task.blocks[0]?.id ?? "empty"}`}>
                        {renderLeaf(preludeBlocks)}
                      </div>
                    );
                  }
                  const taskHeadingId = task.headingBlock.id;
                  const { objective, rest } = extractObjectiveBlocks(task.blocks);
                  return (
                    <CollapsibleCard
                      key={taskHeadingId}
                      title={
                        <div className="flex items-baseline gap-2">
                          <span className="text-xs font-mono text-muted-foreground/70">
                            Task {task.number}
                          </span>
                          <span>{task.title}</span>
                        </div>
                      }
                      defaultOpen={taskForceOpen}
                      expanded={taskForceOpen || undefined}
                    >
                      {/* The per-task Objective renders inline as the
                          "what this task does" line — matching the Console
                          SpecTaskCard layout. No second click required. */}
                      {objective && objective.length > 0 && (
                        <div className="mb-3 text-sm text-muted-foreground">
                          {renderLeaf(objective)}
                        </div>
                      )}
                      <div className="space-y-2">
                        {groupByLabel(rest).map((field) => {
                          const fieldForceOpen = containsBlockOrHeading(
                            field.blocks,
                            null,
                            forceOpenBlockId,
                          );
                          return (
                            <CollapsibleCard
                              key={`${taskHeadingId}-${field.label}`}
                              title={
                                <span className="text-xs font-medium text-muted-foreground">
                                  {field.label}
                                </span>
                              }
                              defaultOpen={fieldForceOpen}
                              expanded={fieldForceOpen || undefined}
                            >
                              {renderLeaf(field.blocks)}
                            </CollapsibleCard>
                          );
                        })}
                      </div>
                    </CollapsibleCard>
                  );
                })}
              </div>
            ) : (
              renderLeaf(section.blocks)
            )}
          </CollapsibleCard>
        );
      })}
    </div>
  );
}
