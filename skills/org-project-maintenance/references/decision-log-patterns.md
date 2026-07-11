# Decision Log Patterns

Use dated entries for choices that shape future implementation.

## Minimal pattern

```org
** 2026-04-23 — Feature Navigation Model
Short paragraph explaining what was decided and why.
```

## Pattern with structured follow-up

```org
** 2026-04-23 — Keyboard Navigation Phasing
Adopt a phased UX plan so the team can validate the least controversial movement first and defer more controversial shortcuts until after real-world use.

- Phase 1: Left/right among visible tile occurrences
- Phase 2: Optional auto-advance behind a toggle
- Phase 2.5: Shift+arrow power-user shortcut deferred
- Phase 3: Up/down by rendered geometry
```

## Pattern for experimental behavior

```org
** 2026-04-23 — Experimental Auto-Advance
Implement auto-advance behind a lightweight toggle rather than a full preferences system. This allows direct comparison during real puzzle-solving while acknowledging that the behavior may change after testing.
```

## Pattern for rejected approach

```org
** 2026-04-23 — Source Help via Native Select Tooltips Rejected
Native select and option tooltips proved unreliable across target browsers, so the frontend should not depend on them for source explanations.
```

## Heuristics
- One short paragraph first.
- Bullets only for phases, guardrails, or explicit consequences.
- Use the heading to name the decision, not the discussion topic.
- If it is provisional, say so in the first paragraph.
- Record the why, not the whole conversation.
