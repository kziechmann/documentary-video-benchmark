# Build "DocuBench": an open benchmark for AI documentary video editing

> **How to use this prompt.** Paste it into a capable coding/research agent (or hand it to a team). Placeholders look like `{{THIS}}` and have defaults in brackets. Where the prompt says "decide and justify," make the call, record the reasoning in the repo, and flag it in your summary instead of asking.

---

## 1. Role and goal

Act as a three-person team: a senior ML evaluation researcher who has shipped widely adopted public benchmarks; a documentary post-production supervisor fluent in broadcast delivery standards (EBU R128 / ITU-R BS.1770, Rec. 709); and an editorial fact-checker. Design and build **{{BENCHMARK_NAME}}** [default: DocuBench; check for name collisions with existing benchmarks and propose two alternatives], a public benchmark that measures how well AI systems **edit a short documentary-style video from a provided set of clips and audio**, scored on four pillars:

1. **Narrative consistency**
2. **Factual accuracy through grounding**
3. **Visual style and cohesion**
4. **Technical quality** (audio levels and clarity; video resolution, frame integrity, color accuracy)

**v0.1 scope.** The core task is editing: the system receives news clips, stock footage, stills, narration and music audio, and a grounded brief, and must deliver a finished cut. Systems that generate their own visuals compete in a **separate track** that is scored with the same rubrics but never ranked against the edit track. Script-only and detect-and-repair tasks are documented as future tiers, not built now.

The output is a complete v0.1 of a GitHub repository (specification, data schemas, evaluation harness, pilot tasks, docs, licenses, leaderboard) plus a Kaggle-ready dataset package. It must be rigorous enough that a research lab would cite it and practical enough that a solo developer can run the dev set in an afternoon.

## 2. Non-negotiable design principles

- **Truth is the source pack, not world knowledge.** Every task ships a sealed source pack. A claim is "supported" only if the pack supports it. Because news footage concerns real events, the pack — not the model's memory — defines what may be stated.
- **Edit track and generation track are separate categories.** Same brief format, same rubrics, same harness; separate leaderboards. Never present a single ranking across both.
- **Measure what can be measured; judge the rest; validate every judge against humans.** Technical metrics are computed deterministically (ffmpeg/ffprobe and friends) and, because source assets are known, mostly with full-reference methods. Narrative, grounding, and style use model judges with published rubrics, and every judge must report agreement with a human-rated calibration set.
- **Report pillars, not just a composite.** A composite exists for leaderboards, but pillar scores and hard-gate failures are the primary result.
- **Assume adversarial submissions.** Gates and minimum-content requirements must make degenerate outputs (a 10-second black video with one true sentence; a cut that uses one clip) score poorly.
- **Reproducible by default.** Containerized harness, pinned versions, fixed seeds, deterministic metrics, a validator for submissions.
- **Open and legal.** Code under Apache-2.0, task metadata and annotations under CC BY 4.0. Media is either redistributable (CC0 / CC BY / public domain) or referenced by URL + checksum with a fetch script; never redistribute footage whose license does not permit it. "Publicly viewable" is not "licensed."
- **Documentary ethics are part of the score.** Any synthetic, reenacted, or AI-generated footage must be disclosed on screen and in the manifest. No realistic synthetic likenesses of real people. News footage must not be re-cut to imply events that did not happen (sequence-implied causation is a grounding failure).

## 3. Task design

### 3.1 Tracks

| Track | Name | Input | Model output | Ranked against |
|---|---|---|---|---|
| **A** (core) | Edit from provided assets | Brief + source pack + asset bundle (news clips, stock footage, stills, narration stems, music stems, SFX) + delivery spec | Finished video + sidecars | Track A only |
| **B** (separate category) | Edit with generated visuals | Same brief, source pack, audio stems, and delivery spec; footage optional or absent; system may generate visuals | Finished video + sidecars, with every generated shot flagged | Track B only |

Track A has two **variants**, both built in v0.1:

- **A1 — Cut to narration.** Narration audio and its transcript are provided. The system selects, orders, trims, and grades footage, mixes music under narration, adds titles/lower-thirds and captions. Tests narrative structure, A/V alignment, visual cohesion, and technical quality; grounding is tested through visual attribution (is the clip shown actually of the thing the narration names?).
- **A2 — Write and cut.** No narration provided. The system writes the narration from the source pack, renders it with the provided TTS voice (or a permitted TTS of its choice, declared in the manifest), then edits as in A1. Adds the full grounding pillar: claim precision, key-fact recall, trap resistance.

Future tiers to document in `docs/roadmap.md` but not build: Tier 0 script-and-storyboard (text only) and Tier 3 detect-and-repair (planted defects such as a swapped date, a 6 LU loudness jump, a 200 ms desync, a wrong-white-balance shot, duplicated frames, an undisclosed synthetic shot).

### 3.2 Anatomy of a task

Every task is a directory containing:

- `brief.md` — audience, tone, runtime window, required beats, must-include facts, must-exclude content (e.g., "do not use clip 07, it has an on-screen error"), disclosure requirements
- `source_pack/` — see 3.3
- `assets/` — clips, stills, audio stems, each with a sidecar (`asset_id`, origin, license, transcript, shot description, timecodes of notable content, color-chart frames where present)
- `assets.manifest.json` — every asset's id, URL, license, checksum; the fetch script restores non-redistributable media from this file
- `delivery_spec.json` — resolution, frame rate, container/codec, color space, loudness target, caption requirements
- `ground_truth/` — hidden: fact ledger, trap list, clip-attribution map (which clips depict which entities/events), reference measurements of the source assets
- `task.json` — ids, track, variant, version, license, checksums

Required model outputs (write a JSON Schema for each):

- `video.mp4`
- `script.json` — narration segments with timestamps and, for every factual claim, source-pack citations (A1: the provided transcript, pre-aligned; A2: model-authored)
- `edl.otio` or `edl.json` — edit decision list: for every shot, asset id, source in/out, timeline in/out, applied effects/grade
- `manifest.json` — every asset used, its origin, a `synthetic: true/false` flag, TTS voice used (A2), and on-screen disclosure timestamps
- `captions.srt`

### 3.3 Source packs and grounding traps

Each source pack contains 5–15 documents: wire-style articles or official releases relevant to the clips, transcripts of every clip, a "verified facts" sheet, data tables, and image/clip metadata with provenance and captions. It also carries a hidden **fact ledger**: atomic facts labeled Supported / Contradicted-by-pack / Not-in-pack, plus the list of **key facts** the brief requires covering, and a **clip-attribution map** stating which clip depicts which person, place, event, and date.

Every pack includes **traps**: a low-authority document with plausible but wrong figures; an outdated statistic superseded elsewhere in the pack; two similarly named entities; a widely believed "fact" the pack explicitly refutes; a clip whose file name or caption does not match its content (misattributed B-roll); a visually similar clip from a different event or date. Score whether the model prefers the authoritative source and the correctly attributed footage.

### 3.4 Footage sourcing

Build an `assets/SOURCING.md` policy and a `scripts/fetch_assets.py`. Prioritize media that may be redistributed in the repo:

- **News:** Voice of America (US public domain), NASA, government press and briefing footage released under open terms (e.g., whitehouse.gov, UK Open Government Licence, EU audiovisual services with attribution), Wikimedia Commons news footage under CC BY / CC BY-SA, Internet Archive and Prelinger Archives public-domain newsreels.
- **Stock:** CC0 and CC BY stock footage (Wikimedia Commons, Internet Archive, CC0 stock libraries). Platform-licensed stock (e.g., Pexels, Pixabay) may be **referenced** by URL + checksum in the manifest but not redistributed, and must be reviewed against each platform's license for benchmark use.
- **Audio:** CC0 / CC BY music and SFX; narration stems recorded or synthesized for the benchmark under permissive terms, with voice-talent consent on file.
- Record license, author, URL, and retrieval date for every asset in the manifest. Prefer historical and institutional topics; avoid living private individuals and ongoing litigation or disputed events.

Topic mix (decide and justify; default 50/30/20): **archival/historical news** (newsreels, space program, infrastructure); **institutional/scientific** (agencies, research releases); **contemporary public-affairs clips** chosen so that the pack contains updates likely to contradict stale training knowledge (tests source-over-memory).

### 3.5 Scale

Pilot: ≥ 10 fully built tasks per variant (A1, A2) in the public dev set, each with 8–25 assets and 2–6 minutes of raw footage; Track B reuses the same tasks with the footage withheld or marked optional. Plan, and script the generation pipeline for, a v1.0 with ≥ 40 dev and ≥ 60 hidden tasks per variant. Runtime window default: 90–180 seconds.

## 4. Evaluation protocol

For each pillar, specify sub-metrics, the exact measurement method, the mapping to a 0–100 score, and the failure modes it catches. Defaults follow; adjust with justification.

### 4.1 Narrative consistency (default weight 25%)

- **Structure:** presence and ordering of hook, context, development, resolution; adherence to required beats (checklist-based judge rubric).
- **Internal consistency:** pairwise NLI between narration segments to detect contradictions; entity and name consistency across narration, lower-thirds, and captions; timeline coherence (A1: did the cut preserve the narration's chronology? A2: is the authored chronology consistent with the pack?).
- **Audio-visual alignment:** for each narration segment, does the footage on screen depict or support what is said? Computed two ways: deterministically from the EDL against the clip-attribution map (does the clip shown match the entity/event named?), and with a VLM judge on sampled frames paired with segment text. Report both.
- **Pacing and redundancy:** shot-length distribution within documentary norms; repeated footage detection; minimum distinct-asset usage; runtime within window.
- **Brief adherence:** topic drift, audience and tone match, must-exclude compliance (judge rubric + EDL check).

### 4.2 Factual accuracy through grounding (default weight 30%)

- **Claim extraction (A2 and all on-screen text):** decompose narration, titles, and lower-thirds into atomic claims (LLM with a deterministic prompt and pinned model version).
- **Claim verification against the source pack:** label each claim Supported / Contradicted / Unsupported with cited evidence (retrieval + NLI + LLM judge). Report **precision**, **contradiction rate**, **unsupported rate**, and **key-fact recall** against the hidden ledger.
- **Citation accuracy:** do the model's citations in `script.json` actually support the claims they are attached to?
- **Visual attribution (A1 and A2):** from the EDL and clip-attribution map, the rate of shots that depict a different person, place, event, or date than the narration asserts at that moment; misattributed-B-roll traps caught or fallen for; lower-third names/dates matching the person/footage on screen.
- **Implied-sequence check:** a judge rubric for juxtapositions that imply causation or reaction the pack does not support (news-editing ethics).
- **Trap resistance:** fraction of document and footage traps avoided.
- **Disclosure:** any generated, reenacted, or heavily manipulated footage is disclosed (manifest, OCR of on-screen text, and the gate in 4.5). Required for Track B; applies to Track A if the system alters footage content.
- **Scoring:** contradicted claims and misattributed footage cost more than unsupported claims; key-fact recall prevents the "say almost nothing" strategy. In A1, the grounding pillar is computed from visual attribution and on-screen text only, and the pillar weight is renormalized (document the exact formula).

### 4.3 Visual style and cohesion (default weight 20%)

- **Shot-to-shot consistency:** distribution of CLIP/DINO embedding distances between adjacent and non-adjacent shots; color-palette distance (e.g., earth mover's distance between LAB histograms); white balance and exposure consistency across shots. Mixed-source news and stock footage makes this a real editing skill: score whether the grade reconciles disparate sources without destroying them.
- **Source handling:** no stretched or squeezed assets; consistent treatment of mismatched aspect ratios and frame rates (pillarbox policy, proper frame-rate conversion, no judder from naive duplication); upscaled SD archival footage handled per the delivery spec.
- **Typography and graphics:** OCR lower-thirds and titles; consistent font family and size, safe-area placement, on-screen duration versus reading speed, contrast.
- **Transitions and framing:** consistency of transition types; cut points on natural action/speech boundaries (judge-assisted).
- **Track B additionally:** identity and scene consistency of recurring subjects across generated shots; style drift; visual match between generated shots and any real footage used.
- **Holistic judge:** VLM rubric applied to a storyboard contact sheet plus sampled clips (look consistency, B-roll relevance, "documentary feel"), calibrated against humans.

### 4.4 Technical quality (default weight 25%)

**Audio** (measure with ffmpeg `ebur128`, `astats`, `silencedetect`, plus ASR and source separation):

- Integrated loudness within target (default −16 LUFS ± 1 LU for online delivery; support a −23 LUFS EBU R128 profile via the delivery spec); true peak ≤ −1.0 dBTP; loudness range within spec; no clipping.
- Segment-level loudness stability: no narration segment deviates more than ±3 LU from the program's dialogue anchor; no abrupt jumps at cuts; location sound from news clips matched in level to the narration bed.
- Music ducking: music bed under narration (via stem separation, e.g., Demucs) at least `{{DUCK_DB}}` [default 15] dB below narration.
- Intelligibility and clarity: ASR word error rate of the delivered audio against `script.json`; a no-reference speech quality score (DNSMOS or NISQA); dead-air and noise-floor checks; narration stem delivered unaltered in A1 (full-reference comparison).
- Sync: caption timing versus ASR word timestamps; SyncNet-style offset on any on-camera speech from the news clips; A/V stream start offset and drift from container metadata; sound-bite audio aligned with its own picture after the cut (from the EDL).

**Video** (measure with ffprobe and frame analysis, using source assets as reference wherever possible):

- Spec conformance: exact resolution; constant frame rate equal to spec; codec/profile/pixel format; color primaries, transfer, and matrix tagged as specified (Rec. 709 by default); legal range.
- Frame integrity: dropped, duplicated, and frozen frames; black or near-black frames outside intentional fades; variable-frame-rate detection; frame-rate conversion artifacts.
- Perceptual quality: full-reference VMAF/SSIM between each delivered shot and its source clip (located via the EDL), generation-loss detection; no-reference VQA (e.g., DOVER or FAST-VQA) as a secondary signal and the primary signal for Track B.
- Color accuracy: ΔE2000 between delivered frames and source assets where the brief requires a neutral grade; absolute checks using color-chart frames embedded in selected stock assets; cross-shot white-balance and skin-tone consistency; detection of Rec. 601/709 matrix mix-ups, double-applied gamma, and banding.
- Graphics legibility: minimum text height as a fraction of frame height, WCAG-style contrast, safe margins.

### 4.5 Hard gates

A task scores 0, with the failure reported by category, if: the video fails to decode or violates the runtime window; the EDL references assets not in the bundle (Track A) or any generated shot is undisclosed (Track B); a realistic synthetic likeness of a real person appears; a required sidecar is missing or fails schema validation; the submission uses a must-exclude asset or content; or fewer than `{{MIN_DISTINCT_ASSETS}}` [default 5] distinct assets are used.

### 4.6 Aggregation and statistics

- Pillar scores 0–100; composite = weighted sum (defaults above, with A1 renormalization), weights published and configurable. The leaderboard shows composite, pillars, gate-failure rate, and A1/A2 separately; Track B has its own leaderboard page.
- Minimum 3 runs per task per system; report mean and 95% bootstrap confidence intervals over tasks. Require paired comparisons when claiming one system beats another.
- **Judge validation:** a human-rated calibration set (default ≥ 150 videos × 3 trained raters, ideally including working editors, using the same rubrics). Report Krippendorff's alpha among humans and Spearman correlation of each automated judge with the human mean. Judges below a published agreement threshold cannot be used for leaderboard results. Run every judge-based metric with at least two different judge models and report sensitivity. Blind judges to system identity; randomize presentation order in pairwise comparisons; strip metadata before judging.

## 5. Anti-gaming and contamination controls

- Public dev set; **hidden test set** scored through a defined submission process (a results bundle the harness validates, evaluated by maintainers or an evaluation server; publish hashes of the hidden set so it can be audited later).
- Minimum-content requirements (distinct assets, runtime, key-fact coverage) and length normalization so brevity, silence, or static frames cannot inflate consistency or precision.
- Rotate a fraction of hidden tasks each version; keep task ids stable and deprecate rather than modify.
- Contamination: because news topics are real, report scores split by topic age, and include tasks whose packs contain post-cutoff updates as the source-over-memory control.
- Detect and flag "citation stuffing" (citations that do not support the attached claim), "disclosure spam" (blanket disclaimers used to avoid specific disclosure), and "safe cutting" (using only the most generic stock to avoid attribution risk; penalized through key-fact and A/V-alignment coverage).

## 6. Infrastructure and reproducibility

- A `docubench` CLI: `fetch` (restore assets from manifests with checksum verification), `validate` (schema and gate checks on a submission), `score` (full evaluation), `report` (HTML/Markdown report with per-metric evidence such as frame grabs, EDL-vs-attribution tables, and loudness plots), `make-task` (build a task from a source-pack template and an asset folder).
- Dockerfile with pinned ffmpeg, Python dependencies, and model weights/versions for ASR, VQA, and embeddings; judge APIs behind a provider-agnostic interface. All randomness seeded. Deterministic metrics produce byte-identical outputs across runs; judge-based metrics record model, version, prompt hash, and raw responses.
- Unit tests for every metric using synthetic fixtures (a generated tone at a known LUFS, a clip with a known 200 ms offset, a frame sequence with known duplicates, a color-chart frame with known values, an EDL with a known misattributed shot). Metrics must recover planted values within stated tolerance.
- Baselines: at least three trivial baselines (random assembly in transcript order, template cut with evenly spaced shots, "narration over the first N clips") and a documented procedure for a small human-editor reference cut on a subset. Human reference cuts also seed the judge calibration set.

## 7. Repository deliverables

Produce this tree (adjust names if you have a good reason; document any deviation):

```
README.md                      # what, why, quickstart, leaderboard snapshot, citation
BENCHMARK.md                   # full specification (sections 2–6 of this prompt, expanded)
RUBRICS.md                     # human and model-judge rubrics with anchored examples
METRICS.md                     # every metric: definition, method, tolerance, score mapping, known limits
DATASHEET.md                   # datasheet for datasets; provenance; licensing; ethics
CONTRIBUTING.md                # how to add tasks and assets, propose metrics, submit results
SUBMISSION.md                  # results-bundle format, validator, hidden-set process
GOVERNANCE.md                  # versioning policy, deprecation, takedown and dispute process
LICENSE (Apache-2.0), LICENSE-DATA (CC BY 4.0), CITATION.cff, CHANGELOG.md
schemas/                       # JSON Schemas: task, brief, delivery_spec, asset, script, edl, manifest, captions, results
tasks/dev/trackA/a1/, a2/      # pilot tasks with source packs and asset manifests; ground_truth kept out of the public tree
tasks/dev/trackB/              # Track B variants referencing the same source packs
tasks/templates/               # source-pack and brief templates; asset sidecar template
assets/SOURCING.md             # footage/audio sourcing and licensing policy
docubench/                     # Python package: fetch/, metrics/, judges/, gates/, aggregation/, cli.py
judges/prompts/                # versioned judge prompts with hashes
tests/                         # fixtures and unit tests per metric
baselines/                     # trivial baselines and their results
leaderboard/                   # results JSON (Track A: A1, A2; Track B) + static site generator
docker/                        # Dockerfile, pinned lockfiles
kaggle/                        # dataset card, metadata, starter notebook (see section 8)
docs/                          # design rationale, roadmap (future tiers), judge-validation report template, FAQ
```

## 8. Publication targets

- **GitHub** is the canonical home: code, spec, dev set, leaderboard via PR or evaluation server.
- **Kaggle:** package the public dev set as a Kaggle Dataset containing all redistributable media plus manifests for the rest (respect size limits), with a dataset card and a starter notebook that fetches assets, runs a trivial baseline cut with ffmpeg, and scores it on the technical-quality and EDL-based alignment metrics end to end. Document why a classic Kaggle Competition is a poor fit for judge-based video metrics and what a code-competition variant would need.
- **Hugging Face:** dataset card mirroring the datasheet, if feasible.

## 9. Acceptance criteria for v0.1

- A newcomer can run `docubench fetch` and `docubench score` on a provided sample submission inside the container and get a report in under 15 minutes on a CPU-only machine for the deterministic metrics.
- All deterministic metrics have passing unit tests that recover planted values.
- At least 10 fully built dev tasks per variant (A1, A2), each with a source pack, traps, fact ledger, clip-attribution map, licensed assets or manifests, and delivery spec; every asset has a recorded license and provenance.
- Every judge prompt has an anchored rubric and a documented calibration plan; the judge-validation report template is complete even if the human study has not yet run.
- The spec states every default and every known limitation plainly, including: the cost of judge-based evaluation, contamination risk on real news topics, the gap between no-reference VQA and human perception, licensing constraints on footage breadth, and the fact that "documentary style" is culturally situated.

## 10. Working method

Work in phases and stop for review after each: (1) BENCHMARK.md, METRICS.md, RUBRICS.md, schemas, and SOURCING.md; (2) harness with deterministic metrics, fetch, and tests; (3) pilot tasks and baselines; (4) judges, leaderboard, Track B variants, Kaggle package. At each stop, summarize decisions made, assumptions, and open questions with a recommendation for each. Prefer a reasoned default over asking; never silently drop a requirement — mark it deferred with a reason.

Open questions you must resolve and justify: final pillar weights and the A1 renormalization; runtime window; loudness profile defaults; the TTS policy for A2 (provided voice only vs. declared choice); how archival SD footage is scored against an HD delivery spec; multilingual narration (default: English for v1.0, schema ready for language tags); minimum hardware for the full harness; and the choice of judge models plus the policy for swapping them without breaking leaderboard comparability (default: version the leaderboard by judge release).
