# Chat to Org Translation Patterns

Use this reference when conversation detail should become durable project memory.

## Rule of thumb

Chat is for coordination. Org is for memory.

Move information from chat into Org when it will matter after the session ends.

## Translation examples

### Chat
"Auto-advance feels controversial, so let's put it behind a temporary toggle before we invest in full preferences."

### Better durable note in PLANNING.org
```org
** 2026-04-23 — Experimental Auto-Advance
Implement auto-advance behind a lightweight toolbar toggle rather than a full preferences system. This supports real-world evaluation while acknowledging that the final behavior may change.
```

---

### Chat
"We should maybe add Shift+arrow later, but not yet because it will complicate evaluation."

### Better durable note in TASKS.org
```org
- [ ] Keyboard navigation, Phase 2.5: consider Shift+Left/Shift+Right for previous/next unmapped letter
  - Status: DEFERRED
  - Rationale: promising power-user shortcut, but postponed so it does not muddy evaluation of base auto-advance semantics
```

---

### Chat
"The workaround technically functions but feels wrong for the UI."

### Better durable note when it matters
```org
** 2026-04-23 — Source Help via Native Select Tooltips Rejected
Do not rely on native select/option tooltips for source explanations; browser behavior is inconsistent and the resulting UX does not fit the interface.
```

## Compression guidance
- Distill the lasting lesson.
- Remove conversational scaffolding.
- Preserve the decision and the reason.
- Do not transcribe the full debate.
