---
name: image-asset-design
description: Plan, generate, inspect, and refine visual assets with a deterministic-first workflow and Pi's confirmed image_generate tool. Use for image concepts, illustrations, textures, visual direction, UI artwork, or deciding whether an asset should be generated versus built as SVG/CSS/canvas. Enforces one confirmed billable attempt at a time, honest visual review, provenance, and mechanical validation before production acceptance.
---

# Image Asset Design

Treat image generation as a concept and artwork tool, not a substitute for
geometry you can specify exactly.

## Choose the construction method first

Prefer deterministic SVG, CSS, canvas, or ordinary drawing tools when the asset
requires any of these:

- exact paths, alignment, symmetry, dimensions, or safe margins;
- reliable transparency and alpha bounds;
- tiny UI legibility or icon variants at fixed sizes;
- exact text, logos, diagrams, schematics, or reusable vector geometry; or
- reproducible light/dark variants and mechanical rasterization.

Use `image_generate` when probabilistic synthesis materially helps: visual
concepts, illustrations, scenes, textures, mood, composition exploration, or a
reference from which to construct a precise final asset.

A hybrid is often best: generate a concept, then rebuild the accepted geometry
deterministically. Do not ask a diffusion-shaped slot machine to be your CAD
program.

## Prepare one complete visual brief

Before calling the tool, state the intended use and encode the useful decisions
in one prompt:

1. subject and action;
2. composition and focal hierarchy;
3. medium, rendering style, palette, lighting, and mood;
4. background and edge treatment;
5. aspect-ratio-specific placement or negative space;
6. details that must be present;
7. artifacts to avoid; and
8. whether the result is exploratory or a production candidate.

Do not add a negative-prompt syntax the selected model does not support. Express
important exclusions in ordinary prose. Avoid requests to copy living artists,
protected logos, or recognizable franchise assets when an original visual
language will do.

## Generate conservatively

Call `image_generate` with:

- one complete `prompt`;
- `resolution: "1K"` for normal concept work unless the user has a concrete
  reason for more;
- an `aspect_ratio` chosen for the actual placement; and
- no `output_directory` by default, leaving drafts in Pi's private directory.

Use `output_directory` only when the user wants the draft written into the
trusted current project. It must be relative to that project. Use `filename`
only for a meaningful safe basename; the tool never overwrites existing files.

The tool displays the model, options, destination, prompt, and charge warning.
The human must confirm every billable request. Cancellation is final for that
attempt.

Never automatically retry a failed, timed-out, uncertain, or
persistence-failed result. If another attempt is useful, explain why and let a
new tool call receive its own confirmation.

## Inspect the actual result

After generation, inspect the returned image rather than inferring quality from
the prompt or success status. Compare it against the brief and report concrete
findings:

- composition and focal clarity;
- malformed anatomy, perspective, lighting, edges, or repeated structures;
- text accuracy when text was unavoidable;
- unwanted marks, pseudo-signatures, or copied-looking identifiers;
- suitability at the intended crop and display size; and
- whether deterministic reconstruction is now the better next step.

Distinguish provider success, artifact persistence success, and visual
acceptance. They are three different claims.

## Promote deliberately

Keep generated drafts and their JSON provenance sidecars together. Before
promoting a candidate into production:

1. obtain explicit human acceptance of the visual direction;
2. perform deterministic post-processing or reconstruction where precision
   matters;
3. verify format, dimensions, alpha behavior, safe margins, and small-size
   legibility with ordinary inspection tools;
4. document any reproducible conversion or rasterization steps; and
5. preserve the original draft or its provenance when it constrains later work.

## Current tool boundary

The initial `image_generate` capability is intentionally narrow:

- OpenRouter's dedicated Image API;
- fixed `google/gemini-3.1-flash-image` model;
- text-to-image only;
- exactly one PNG;
- interactive Pi TUI confirmation only;
- bounded response and decoded-image sizes;
- no provider fallback or automatic retry; and
- safe private drafts or explicitly selected trusted project-relative output.

Reference-image editing, model menus, multiple outputs, streaming previews, and
provider failover are not current capabilities. Do not imply otherwise.
