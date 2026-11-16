# Footage, stills, and audio sourcing policy

Every asset in a DocuBench task carries a license and a provenance record in the task's `assets.manifest.json`. This document says what may be used, what may be *redistributed*, and what we learned sourcing the first task.

## The rule

**"Publicly viewable" is not "licensed."** A clip on YouTube, a newsreel on the Internet Archive, or a photo on a news site can be watched by anyone and still be fully copyrighted. We only use material in one of three states:

| State | What it means | Stored in repo / Kaggle? |
|---|---|---|
| **Redistributable** | Public domain (US-government works, expired copyright) or CC0 / CC BY / CC BY-SA with the attribution recorded | Yes — media is fetched by URL and verified by checksum; small files may be committed |
| **Reference-only** | Lawful to use under a platform license (e.g., some stock sites) but not to redistribute | No — manifest holds URL + checksum; `docubench fetch` downloads it to the user's machine |
| **Excluded** | Everything else | Never |

Each manifest entry records `origin`, `license`, `url`, `sha256`, `redistributable`, and the retrieval date. Each task's `D07`-style captions document quotes the archive's own caption verbatim so attribution is traceable.

## Approved sources

### News and archival footage
- **NASA Image and Video Library** (`images.nasa.gov`, API at `images-api.nasa.gov`): US-government works, public domain. Includes modern media reels that embed period footage, launch audio, and interviews. Check `secondary_creator` — items credited to non-NASA parties (e.g., universities) may carry restrictions.
- **NASA NSSDCA, NTRS, NASA History**: public-domain documents; NTRS scans have OCR text layers.
- **Voice of America** (US-government news service): public domain, but verify each item — VOA occasionally carries agency footage it does not own.
- **US government briefing and agency footage** (whitehouse.gov, DoD DVIDS, NOAA, USGS, NIH): public domain unless marked.
- **UK Open Government Licence**, **EU audiovisual services**: permissive with attribution; record the licence text.
- **Internet Archive**: *only* items whose metadata shows a public-domain or CC licence. The Prelinger collection is largely public domain; the general "movies and films" collection is not vetted.
- **Wikimedia Commons**: per-file licence; use the API's `imageinfo` extmetadata to record `LicenseShortName` and `Artist`.

### Stills
Same sources, plus JPL Photojournal (`photojournal.jpl.nasa.gov`, mirrored on `images-assets.nasa.gov`).

### Stock footage
- CC0 sources first (Wikimedia Commons, Internet Archive items marked CC0).
- Platform-licensed stock (Pexels, Pixabay, Mixkit) is **reference-only**: record the platform's licence text and date, never commit the file.

### Music and sound effects
- CC0 only for redistribution; CC BY acceptable with attribution in the task's credits card. Record composer, source URL, licence, and date.
- Period audio embedded in public-domain films may be used as sound bites under the film's licence.

### Narrator voices
Commissioned or synthesized voices used for A2 narration must have written consent and a licence covering benchmark distribution and derivative use; the voice talent is compensated. Reference files live under `assets/voices/` with the consent record.

## What we excluded, and why (task a2-0001)

- **"Shooting for Mars" (1964)** on the Internet Archive — a Hearst Metrotone newsreel. Not a government work; no licence in the item metadata. Excluded despite being the ideal period film.
- **WMAR-TV "Man Encounter Mars" (1965)** on the Internet Archive — rights held by E.W. Scripps; stream-only access granted to the University of Baltimore. Excluded.
- **NASA Science web page images** served from `assets.science.nasa.gov` — same public-domain images are available from `images-assets.nasa.gov`, which is what the manifest cites.

## Subjects and ethics

- Prefer historical, institutional, scientific, and natural subjects. No living private individuals as subjects.
- Public officials and agency staff speaking in an official capacity (press briefings, agency interviews) are acceptable; tasks still require a lower-third and interview year for every sound bite.
- No realistic synthetic likeness of any real person, in any track. Generated or re-created footage must be disclosed on screen and in the manifest.
- Honor takedown requests promptly; see `GOVERNANCE.md`. Deprecate the task version rather than silently editing it.

## Checklist for adding an asset

1. Find the item on an approved source; copy the canonical item URL.
2. Record title, description/caption, creator and credit fields **verbatim** from the archive.
3. Record the licence (or the public-domain basis) and the retrieval date.
4. Download the master rendition, compute `sha256`, and write both into the manifest.
5. Decide `redistributable`; if false, confirm `docubench fetch` can retrieve it without credentials.
6. Add an identification note if the title or filename could mislead; that note is what makes a trap fair.
