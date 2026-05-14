"""Ummia MCP server: teaching surface for the Sumerian 101 lessons
plus the dual-register Sumerian grammar reference.

Ummia (Sumerian 𒌝𒈪𒀀 *um-mi-a*, citation form `ummia` — ePSD2 lemma
`ummia[expert]N`, 453× attested in ED + Ur III + OB) is the canonical
Sumerian word for the master teacher of the e₂-dub-ba (scribal
school). The Old Babylonian "Schooldays" literary compositions use
exactly this term when a student addresses their teacher.

This server wraps Meadow's classroom-e₂-nun-na Sumerian 101 lesson
series in the Ummia teaching persona AND owns the dual-register
Sumerian grammar reference (Jagersma 2010 academic + Meadow / Siri
Nin temple companion). Each lesson is a self-contained teaching
prompt (see `lessons/lesson-101-N.md`); the grammar reference is
~80 KB of source material at `lessons/JAGERSMA_GRAMMAR.md` plus
`lessons/MEADOW_GRAMMAR.md`.

Tools:
- `start_here()`              returns the Ummia persona prompt + lesson menu
- `get_lesson_101_1()` … `_5()` return each lesson's full teaching markdown
- `get_grammar_reference()`   returns the dual-register grammar bundle

Resource:
- `oracc://grammar/sumerian`  same content as get_grammar_reference,
                              served as an MCP resource for spec-
                              complete clients (the resource registration
                              lives at the entry-point script in
                              servers/ummia/__main__.py)

The Ummia server has NO data tools of its own. The lessons direct
the agent to the four data MCPs (ePSD2, ETCSL, CDLI, OGSL) for
attestation lookups, sign rendering, and corpus reads.
"""

from __future__ import annotations

from ..log import log_call
from ..models.ummia import GrammarReferenceResponse
from ..paths import (
    GRAMMAR_DOC,
    LESSON_101_1_DOC,
    LESSON_101_2_DOC,
    LESSON_101_3_DOC,
    LESSON_101_4_DOC,
    LESSON_101_5_DOC,
    MEADOW_GRAMMAR_DOC,
    UMMIA_PROMPT_DOC,
)
from ..prompts import load_prompt

_ACADEMIC_GRAMMAR_CACHE: str | None = None
_TEMPLE_GRAMMAR_CACHE: str | None = None  # None = "file absent at startup"

_TEMPLE_HANDOFF_BANNER = (
    "\n\n"
    "═══════════════════════════════════════════════════════════════\n"
    "  TEMPLE REGISTER COMPANION — switching from academic to in-temple grammar\n"
    "  Above: Jagersma 2010 (rigorous, attested, period-aware).\n"
    "  Below: Meadow's Sumerian 101 classroom lessons + Siri Nin's commentary\n"
    "         (prayer-ready pedagogy; what the temple actually teaches).\n"
    "  Conflicts resolved per §18 of the temple file:\n"
    "    • temple composition → temple file is normative\n"
    "    • reading attested texts → Jagersma is normative\n"
    "═══════════════════════════════════════════════════════════════\n\n"
)


def _load_academic_grammar() -> str:
    """Read + cache lessons/JAGERSMA_GRAMMAR.md (Jagersma 2010)."""
    global _ACADEMIC_GRAMMAR_CACHE
    if _ACADEMIC_GRAMMAR_CACHE is None:
        if not GRAMMAR_DOC.exists():
            _ACADEMIC_GRAMMAR_CACHE = (
                "# lessons/JAGERSMA_GRAMMAR.md missing\n\n"
                f"Expected at {GRAMMAR_DOC}. Re-run the project setup."
            )
        else:
            _ACADEMIC_GRAMMAR_CACHE = GRAMMAR_DOC.read_text(encoding="utf-8")
    return _ACADEMIC_GRAMMAR_CACHE


def _load_temple_grammar() -> str | None:
    """Read + cache lessons/MEADOW_GRAMMAR.md, or None when absent.

    None means the temple companion isn't shipped with this deployment;
    callers should treat the bootstrap as academic-only.
    """
    global _TEMPLE_GRAMMAR_CACHE
    if _TEMPLE_GRAMMAR_CACHE is None and MEADOW_GRAMMAR_DOC.exists():
        _TEMPLE_GRAMMAR_CACHE = MEADOW_GRAMMAR_DOC.read_text(encoding="utf-8")
    return _TEMPLE_GRAMMAR_CACHE


def _load_grammar() -> str:
    """Single-string view: academic + (optional) temple, concatenated
    with the handoff banner. Used by the `oracc://grammar/sumerian`
    resource where a single markdown blob is the right wire shape."""
    academic = _load_academic_grammar()
    temple = _load_temple_grammar()
    if temple is None:
        return academic
    return academic + _TEMPLE_HANDOFF_BANNER + temple


# ─── Resource body (registered by entry-point) ─────────────────


@log_call
def grammar_cheatsheet() -> str:
    """Body for the `oracc://grammar/sumerian` MCP resource. Returns
    the combined academic + temple grammar references as a single
    markdown document. The resource registration (uri / name / title /
    description / mime_type) lives at the entry-point script in
    servers/ummia/__main__.py."""
    return _load_grammar()


# ─── Tools ─────────────────────────────────────────────────────


@log_call
def start_here() -> str:
    """⭐ CALL THIS FIRST, BEFORE ANY OTHER TOOL ON THIS SERVER.

    Returns the Ummia persona prompt — your identity for this
    session is **Ummia, master teacher of the scribes of the
    Temple of Inanna's Light**. The returned markdown sets up:

      • Your voice and teaching ethos (patient, encouraging, full
        of "rules AND exceptions to every rule").
      • The five lessons available on this server, each with a
        short description of what the student walks away knowing.
      • The teaching workflow (recap, section-by-section, drills
        with hidden answers, attestation lookups, end-of-lesson
        exercise, preview the next).
      • The dual-register Sumerian grammar reference Ummia owns
        (see `get_grammar_reference()`) — Jagersma 2010 academic +
        Meadow temple companion. Pull it once per session as a
        teacher's reference.
      • How this server composes with the four eme-gir data MCPs
        (epsd2, ogsl, etcsl, cdli) — Ummia has no data tools.
      • Attribution / licensing carry-through for ePSD2, ETCSL,
        and CDLI.

    Adopt the Ummia persona immediately after reading this prompt.
    When the student names a lesson (or asks which to start with),
    call the matching `get_lesson_101_N()` tool — those returns are
    YOUR teaching scripts, structured for the teacher, not the
    student. Walk them section by section.
    """
    return load_prompt(UMMIA_PROMPT_DOC)


@log_call
def get_lesson_101_1() -> str:
    """Lesson 101-1 — Introduction to Sumerian. Returns the full
    teaching prompt for this lesson as markdown.

    Topics covered (in order):
      1. Pronunciation of ŋ ("ng"), š ("sh"), ḫ ("kh").
      2. The three jobs of a cuneiform sign: logogram (whole word),
         syllable (phonetic), determinative (silent category marker).
      3. Subscript numbers (du, du₂, du₁₀, du₁₁ …) and period
         spelling drift (du₁₀ vs. dug).
      4. Nouns — human vs. non-human class (not male/female); simple
         single-sign nouns; compound nouns joined by hyphens.
      5. Plurals — `-ene` (human only), reduplication, or unmarked.
      6. Adjectives — after the noun; verb-as-adjective via `-a`;
         the auslaut; the silent g of kala(g); occasional unmarked
         adjectives; doubled adjective ⇒ plural noun.
      7. End-of-lesson three-takeaway summary for adjectives.

    Lesson is structured as numbered sections (§1–§7) with per-section
    drills (answers in `<details>` blocks) and an end-of-lesson
    exercise + answer key. Walk section by section; don't dump.
    """
    return load_prompt(LESSON_101_1_DOC)


@log_call
def get_lesson_101_2() -> str:
    """Lesson 101-2 — Basic Verbs. Returns the full teaching prompt
    for this lesson as markdown.

    Topics covered (in order):
      0. Recap of 101-1.
      1. Verb terminology — transitive vs. intransitive, active vs.
         passive; diagnostic question for classification.
      2. Anatomy of a verbal chain: [prefixes]-[VERB]-[suffixes].
         Worked example: `lugal-e e₂ mu-un-du₃`. Default tense is
         perfective past; default word order SOV.
      3. Simple verbs (du₃, du, gi₄, dim₂) vs. compound verbs
         (inim–gi₄, gu₃–de₂, igi–bar, za₃-mi₂–dug₄) — the long-dash
         convention.
      4. Participles and passives — both readings of the `-a` ending
         on a verb base.
      5. The genitive `-ak` ("of") — three rules (consonant-final,
         vowel-final, anything-following).
      6. The "pesky -a" three-tip heuristic — is it adjective?
         verb-participle? noun-genitive?

    Sections (§1–§7) each have drills; full exercise + answer key at
    §8. This is where the student first sees the verbal chain — pace
    it carefully.
    """
    return load_prompt(LESSON_101_2_DOC)


@log_call
def get_lesson_101_3() -> str:
    """Lesson 101-3 — Case Markers, Possession & Pronouns. Returns
    the full teaching prompt for this lesson as markdown.

    Topics covered (in order):
      0. Recap of 101-2.
      1. Noun class deeper — human vs. non-human, with full lists.
      2. Conjugation prefixes — `/mu-/` ventive, `/ba-/` non-human
         subject / change of state / passive, `/i₃-/` default vocalic.
      3. The eight case endings — dative `-ra` (human), locative-
         terminative `-e` (non-human), ablative `-ta`, terminative
         `-še₃`, comitative `-da`, locative `-a`, equative `-gin₇`,
         genitive `-ak`.
      4. Ergative `-e` revisited; absolutive `-0` on intransitive
         subjects; why the zero matters in normalization.
      5. The copula — `-me-en` (I am / you are), `-am₃` (he/she/it
         is).
      6. Possessives — `-ŋu₁₀` (my), `-zu` (your), `-ani` (his/her),
         `-bi` (its). Possessive + genitive vowel-fusion shenanigans.
      7. PNC order (Possession · Number · Case) — worked example
         `lugal-zu-ne-ra`.
      8. Independent pronouns — `ŋa₂-e`, `za-e`, `e-ne`, `e-ne-ne`.
      9. Case markers inside the verbal chain — every case ending
         has a verbal-chain twin (`-ta` ↔ `-ta-`, `-a` ↔ `-ni-`,
         `-da` ↔ `-da-`, etc.).

    This is the LONGEST lesson. Pace it ruthlessly. Two sessions if
    the student is tiring. End-of-lesson exercise at §11 (10 items
    Part A + 3 items Part B).
    """
    return load_prompt(LESSON_101_3_DOC)


@log_call
def get_lesson_101_4() -> str:
    """Lesson 101-4 — Advanced Verbs: Person, Tense & Reduplication.
    Returns the full teaching prompt for this lesson as markdown.

    Topics covered (in order):
      0. Recap of 101-3.
      1. Person markers on intransitive verbs (perfective):
         `-en, -en, -0, -enden, -enzen, -eš`. Worked on `ŋen`/`re₇`.
      2. Person markers on transitive perfective verbs — finally the
         meaning of `-un-` in `mu-un-du₃` is revealed: `-n-` is the
         3rd-singular-human agent marker. Full table from 1st-sg
         (`-0-`) through 3rd-plural (`-n-VB-eš`).
      3. Initial person prefixes — why SVC sometimes shows `in-` /
         `ib-` instead of `i₃-`.
      4. Aspect — perfective (default; English simple past) vs.
         imperfective (English present/future).
      5. Imperfective form #1 — add `-e` to the verb.
      6. Imperfective form #2 — reduplicate the verb base
         (sometimes with a base change: ŋar → ŋa₂-ŋa₂, naŋ → na₈-na₈).
      7. Imperfective form #3 — change the base entirely (dug₄ → e).
      8. Perfective reduplication — a SEPARATE phenomenon that
         marks a plural subject (intransitive) or plural object
         (transitive), not aspect.
      9. Transitive imperfective endings — `-en, -en, -e/-VB-,
         -enden, -enzen, -ene`.

    Mnemonic to drill: "perfective puts the agent BEFORE the verb;
    imperfective puts the agent AFTER the verb." End-of-lesson
    exercise at §11 (9 items Part A + 3 items Part B). For verb-form
    queries the student isn't sure about, reach for
    `eme-gir-epsd2.find_verb_form`.
    """
    return load_prompt(LESSON_101_4_DOC)


@log_call
def get_lesson_101_5() -> str:
    """Lesson 101-5 — Advanced Case Markers, Modal Prefixes &
    Subordination. Returns the full teaching prompt for this lesson
    as markdown.

    Topics covered (in order):
      0. Recap of 101-4.
      1. Direct objects expressed in the verbal chain (mirror of
         agent placement — perfective after the verb, imperfective
         before).
      2. Modal prefixes:
           • `nu-` "not" (negative; flips to `la-`/`li-` before
             `ba-`/`bi₂-`).
           • `ga-` "let me/us" (cohortative; 1st-person only;
             vowel-harmonized; negated as `ga-ra-`).
           • `ḫa-` "may he/she/it" (precative; vowel-harmonized to
             `ḫa-ba-`, `ḫe₂-`, `ḫu-mu-`).
           • `ba-ra-` "absolutely not" (categorical negative).
         Plus a Siri-Nin compilation table for less-common modals
         (prohibitive, affirmative, contrapunctive, additive).
      3. Compound verbs revisited — possessives on the noun part
         (`igi-ŋu₁₀ in-ši-bar`); oblique objects marked with `-e`,
         `-a`, or unmarked; auxiliary verbs `ak`/`du₁₁` substituting
         in the chain.
      4. Imperatives — verb fronted, often with `-a`. Bare imperative
         (`šum₂-ma` "give!") vs. chain-retained imperative
         (`šum₂-ma-ab` "give it!").
      5. Non-finite forms — perfective `-a` participle (already known);
         imperfective active `-e(d)` participle ("the one who…" /
         "in order to…").
      6. Subordinate clauses — the `lu₂ … -a` construction.

    This is the series finale. End-of-lesson exercise at §8 (10 items
    Part A + 3 items Part B). Close with the §9 "Where to go from
    here" reading — quote it to the student verbatim. The lesson
    series is meant to feel COMPLETE; the student has a foundation
    even if Sumerian isn't done with them.
    """
    return load_prompt(LESSON_101_5_DOC)


@log_call
def get_grammar_reference() -> GrammarReferenceResponse:
    """Return BOTH Sumerian grammar references — academic + temple —
    as a structured response. Ummia's teacher's-reference shelf.

    Call this once per session, on top of `start_here()`. The
    response carries:

    1. `academic` (always present, ~40 KB): the Jagersma-2010-based
       reference from lessons/JAGERSMA_GRAMMAR.md. Comprehensive
       distillation of Bram Jagersma's *A Descriptive Grammar of
       Sumerian* (PhD diss., Leiden 2010, 776 pp). Covers transliteration
       conventions, phonology, the twelve enclitic cases with ambiguity
       tables, gender/plural, pronouns/numerals/adjectives, the nine-slot
       finite-verb template, perfective vs imperfective inflection,
       preformatives (vocalic + modal + negative), dimensional prefixes,
       ventive + middle, non-finite forms, copular/nominal clauses, and
       nominalization-based subordination. Every grammatical rule carries
       an inline Jagersma section citation (e.g. §7.3).

    2. `temple` (optional, ~48 KB): the temple-register companion from
       lessons/MEADOW_GRAMMAR.md — Meadow's Sumerian 101 classroom-
       e₂-nun-na lessons plus Entu Siri Nin's commentary. The PNC
       mnemonic, the 'pesky -a' three-tip heuristic, the perfective-
       default temple composition style, the Emesal liturgical register,
       and worked temple examples (dedication formulas, royal-
       inscription lines, prayer-direct imperatives). Cite as
       `(Meadow §101-N)` or `(Siri Nin)`. None when the deployment
       doesn't ship the temple file.

    3. `combined`: both documents concatenated with a separator banner,
       ready to drop into a system prompt as a single context blob.

    4. `temple_available`: a True/False flag for the temple companion's
       presence.

    Use the academic part for rigor and attested-form questions; use the
    temple part for prayer composition and in-house liturgical style.
    Section §18 of the temple file documents where the two diverge and
    which is normative when they do.

    Default period for unspecified-period translations: ED (Early
    Dynastic, ~2900-2350 BCE) — Jagersma's primary descriptive ground.

    (Spec-complete MCP clients can read the `combined` form from the
    `oracc://grammar/sumerian` resource instead — but most production
    clients only surface tools, so this is exposed as a tool too.)
    """
    academic = _load_academic_grammar()
    temple = _load_temple_grammar()
    combined = academic if temple is None else academic + _TEMPLE_HANDOFF_BANNER + temple
    return GrammarReferenceResponse(
        academic=academic,
        temple=temple,
        combined=combined,
        temple_available=temple is not None,
    )
