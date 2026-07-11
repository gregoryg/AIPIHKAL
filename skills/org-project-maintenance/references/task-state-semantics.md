# Task State Semantics

Match the repo's established vocabulary first. Use this reference when the repo needs a default interpretation.

## Core states

### TODO
Planned work not yet underway.

### STARTED
Active work in progress.

### IN-TEST
Implemented enough to test, but still awaiting confirmation or device/browser validation.

### DONE
Completed and validated to the repo's standard.

### BLOCKED
Cannot proceed without external input, dependency, asset, or API change.

## Special states often worth preserving

### DEFERRED
A good idea intentionally postponed. Use when the postponement is itself meaningful and future sessions should not reopen the question accidentally.

### EXPERIMENTAL
Implemented for evaluation but not accepted as settled UX/product behavior.

## Usage guidance
- Do not invent many near-duplicate states.
- If prose notes can express the nuance, prefer prose over another status keyword.
- When marking something deferred, explain the reason briefly.
- When marking something experimental, note what is being evaluated.
- When moving something to done, consider whether it should also leave the active section.
