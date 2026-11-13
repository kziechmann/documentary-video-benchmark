# DocuBench

**A public benchmark for AI documentary video editing.** Give a system a brief, a sealed pack of sources, and a bundle of news clips, stock footage, stills, and audio stems. Score the cut it delivers on four pillars: narrative consistency, factual grounding, visual cohesion, and technical quality.

> Status: **v0.1 draft**. Dev set and harness under construction. Nothing on the leaderboard yet.

## Why this benchmark

Video models are judged almost entirely on single-clip aesthetics. Documentary work is the opposite problem: dozens of mismatched sources, a story that has to hold together for three minutes, claims that have to be true, and delivery specs that have to be met. Nobody measures that. DocuBench does, with metrics that an editor would recognize and a fact-checker would sign off on.

## What a task looks like

```
tasks/dev/trackA/a2/a2-0001-mariner4/
├── brief.md               # audience, tone, runtime, required beats, must-exclude
├── source_pack/           # 5–15 documents: primary sources, transcripts, facts sheet, data, traps
├── assets.manifest.json   # every clip/still/stem: id, license, URL, checksum
├── assets/                # redistributable media (the rest is fetched by checksum)
├── delivery_spec.json     # 1920x1080, 29.97p, Rec. 709, −16 LUFS, captions required
└── ground_truth/          # hidden: fact ledger, trap list, clip-attribution map
```

The system returns `video.mp4`, `script.json` (narration with claim-level citations), `edl.json` (which asset is on screen when), `manifest.json` (origin and `synthetic` flag per asset), and `captions.srt`.

## Tracks and variants

| | Input footage | Narration | Ranked against |
|---|---|---|---|
| **A1 — Cut to narration** | provided | provided (audio + transcript) | A1 |
| **A2 — Write and cut** | provided | written by the system, rendered with the provided TTS voice | A2 |
| **B — Generated visuals** | optional / absent; system may generate shots | as A2 | B only |

Track B is a separate category. It is never ranked against Track A.

## How scoring works

| Pillar | Weight | Measured by |
|---|---|---|
| Narrative consistency | 25 | beat checklist, cross-segment NLI, EDL-vs-attribution alignment, VLM alignment judge, pacing |
| Factual grounding | 30 | claim precision / contradiction / key-fact recall against the pack, citation accuracy, visual attribution, trap resistance |
| Visual cohesion | 20 | cross-shot embedding and palette distance, source handling (aspect, frame rate), typography OCR, holistic VLM judge |
| Technical quality | 25 | EBU R128 loudness, true peak, ducking, ASR WER, sync; spec conformance, frame integrity, VMAF/SSIM and ΔE2000 vs source, legibility |

Hard gates zero a task: undecodable video, runtime outside the window, EDL referencing assets not in the bundle, undisclosed generated footage, a must-exclude asset used, fewer than 5 distinct assets.

Deterministic metrics are byte-reproducible inside the container. Judge-based metrics ship with their prompts, model versions, and a human-calibration report; a judge that does not clear the published agreement threshold cannot feed the leaderboard. Results report mean and 95% bootstrap CI over ≥ 3 runs per task. Full definitions: [`METRICS.md`](METRICS.md), rubrics: [`RUBRICS.md`](RUBRICS.md), spec: [`BENCHMARK.md`](BENCHMARK.md).

## Quickstart

```bash
docker run --rm -v $PWD:/work ghcr.io/{{ORG}}/docubench:0.1 \
  docubench fetch tasks/dev/trackA/a2/a2-0001-mariner4        # restore assets, verify checksums
docubench validate submissions/my-system/a2-0001-mariner4/     # schemas + gates
docubench score    submissions/my-system/a2-0001-mariner4/     # all metrics → results.json
docubench report   submissions/my-system/a2-0001-mariner4/     # HTML report with frame grabs and loudness plots
```

Deterministic metrics run CPU-only in under 15 minutes per task. Judge metrics need API keys for at least two judge providers (`DOCUBENCH_JUDGE_*`).

## Footage and licensing

Every asset carries a license and provenance record. Redistributed media is public domain or CC0 / CC BY (NASA, Voice of America, government briefing footage, Wikimedia Commons, Internet Archive and Prelinger newsreels). Platform-licensed stock is referenced by URL and checksum only. "Publicly viewable" is not "licensed": see [`assets/SOURCING.md`](assets/SOURCING.md). Takedown requests: [`GOVERNANCE.md`](GOVERNANCE.md).

## Submitting results

Run the dev set, open a PR with your `results.json` and run logs per [`SUBMISSION.md`](SUBMISSION.md). Hidden-set scoring is done by maintainers from a validated results bundle; hidden task hashes are published so the set can be audited later.

## Roadmap

- v0.1 — Track A (A1, A2) dev set, deterministic harness, trivial baselines
- v0.2 — judge calibration study, Track B, Kaggle dataset package
- v1.0 — hidden set (≥ 60 tasks per variant), human-editor reference cuts, leaderboard
- Later — Tier 0 script-and-storyboard (text only), Tier 3 detect-and-repair

## License and citation

Code: MIT. Task metadata, annotations, and documentation: CC BY 4.0. Media: per-asset, see manifests. Cite via [`CITATION.cff`](CITATION.cff).
