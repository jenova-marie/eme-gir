"""Sumerian morphology helpers — suffix peeling, verbal prefix detection, token cleanup.

Shared by `mcp_server.py` (for `translate_sumerian`, `parse_phrase`) and
`build_inflected_collocations.py` (for the case-aware corpus n-gram
ingest). Extracted into its own module so both can use them without
duplication and so the suffix table is the single source of truth.

The canonical reference for what these helpers encode is
`prompt/SUMERIAN_GRAMMAR.md` §3 (noun cases), §5.2 (possessives), §7.2
(verbal prefix chain). Detection is heuristic — many surface forms are
genuinely ambiguous (`-e` is ergative on a noun OR directive case OR
3sg verbal-agreement on a verb; `-a` is locative on a noun OR
nominalizer on a verb; `-bi` is 3sg-nonperson-possessive OR
demonstrative). The peeler reports the lexicographically most-likely
reading and lists alternates in `ambiguous_with` so callers can decide.

Suffix-peeling is right-to-left, longest-first, stopping at the first
unmatched iteration to avoid over-stripping (e.g. won't peel `-a` off
`ama` "mother"; lemma validation happens at the caller).

The Suffix dataclass lives in `mcp_models.py` because it's a Pydantic
response type used by tools — we import it here rather than redefine it.
"""

from __future__ import annotations

import re

from mcp_models import Suffix


# Suffix patterns, LONGEST-FIRST so multi-morpheme combos match before
# their shorter components. Each entry is:
#   (regex anchored at $, role, kind, ambiguous_with_list)
# `kind` ∈ {'case', 'possessive', 'plural', 'verbal_agreement'}.
SUMERIAN_SUFFIX_TABLE: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    # ─── Multi-morpheme combos (peel as a unit when possible) ──────────────
    ("-zu-ne-ne$",   "2pl_possessive",                "possessive", ()),
    ("-a?ne-ne$",    "3pl_h_possessive",              "possessive", ()),
    ("-bi-ne$",      "3pl_nh_possessive",             "possessive", ()),
    # ─── Case suffixes (longest first to disambiguate from possessives) ───
    ("-gin₇$",       "equative",                      "case",       ()),
    ("-šè$",         "terminative",                   "case",       ()),
    ("-še₃$",        "terminative",                   "case",       ()),
    ("-še$",         "terminative",                   "case",       ()),
    ("-ta$",         "ablative_instrumental",         "case",       ()),
    ("-da$",         "comitative",                    "case",       ()),
    ("-ra$",         "dative",                        "case",       ()),
    ("-ak$",         "genitive",                      "case",       ()),
    # ─── Plural marker (person class) ─────────────────────────────────────
    ("-e?ne$",       "plural",                        "plural",     ("3sg_h_possessive (when bare -ne)",)),
    # ─── Single-syllable possessives (must come before single-letter cases)
    ("-ŋu₁₀$",       "1sg_possessive",                "possessive", ()),
    ("-zu$",         "2sg_possessive",                "possessive", ()),
    ("-a?ni$",       "3sg_h_possessive",              "possessive", ()),
    ("-bi$",         "3sg_nh_possessive_or_anaphoric","possessive", ("demonstrative ('this/that')",)),
    ("-me$",         "1pl_possessive",                "possessive", ()),
    # ─── Single-letter case suffixes (most ambiguous) ─────────────────────
    ("-a$",          "locative",                      "case",       (
        "nominalizer (-a on a finite verb makes it a relative/subordinate clause)",
        "genitive (the consonantal -k often elides, leaving only -a)",
    )),
    ("-e$",          "ergative",                      "case",       (
        "directive (-e 'at, to' on a non-person noun, collides with ergative)",
        "3sg/3pl ergative verbal agreement (when attached to a verb stem in marû)",
    )),
)

# Verbal prefix inventory (§7.2). Used to identify a token as a verb form
# and extract its prefix chain. Order matters less here since we match
# anchored at the start; we just need to know which fragments are valid.
VERBAL_PREFIXES: tuple[str, ...] = (
    # modal
    "ḫe₂", "na", "ga", "bara", "nu",
    # conjugation prefixes
    "mu", "ba", "bi₂", "al", "i₃", "i", "e",
    # ventive / dimensional indicators (typically follow conj. prefix)
    "na", "ni", "ši", "ta", "da", "bi",
    # person markers (immediately before root)
    "n", "b",
)

_SUFFIX_PATTERNS = tuple(
    (re.compile(rx, re.UNICODE), role, kind, alts)
    for rx, role, kind, alts in SUMERIAN_SUFFIX_TABLE
)

# Determinatives like {d}, {ŋeš}, {ki}, {mušen} are silent classifiers that
# don't participate in grammatical role analysis. Strip them before peeling.
_DET_PATTERN = re.compile(r"\{[^}]*\}")

# Surface punctuation to clean off the edges of a token. Half-brackets and
# square brackets are publication markers (damaged / fully-broken signs);
# parens/commas/etc. occasionally creep in from copied-and-pasted text.
_TOKEN_STRIP = "⸢⸣[](),;:!?"


def strip_token(s: str) -> str:
    """Strip determinatives + punctuation + whitespace from a token."""
    s = _DET_PATTERN.sub("", s).strip().strip(_TOKEN_STRIP)
    return s


def peel_suffixes(token: str) -> tuple[str, list[Suffix]]:
    """Iteratively peel grammatical suffixes from the right of a token.

    Returns (base, suffix_chain_left_to_right). When no suffix matches,
    returns (token, []) — meaning the token is its own base.

    The peeler stops at the FIRST non-match to avoid over-eager stripping
    (e.g. it won't peel `-a` off `ama` "mother", because after peeling we'd
    need a base like `am` which isn't a valid lemma surface form — but the
    peeler doesn't validate against the dictionary, it just stops on no
    regex match. Lemma validation happens at the caller).
    """
    suffixes_right_to_left: list[Suffix] = []
    remaining = token
    # Guard against pathological cases (token shorter than 2 chars can't
    # carry a suffix in the patterns we recognize, since all our suffix
    # spellings start with '-').
    while len(remaining) >= 2:
        for pattern, role, kind, alts in _SUFFIX_PATTERNS:
            m = pattern.search(remaining)
            if m:
                surface = m.group(0)
                suffixes_right_to_left.append(Suffix(
                    spelling=surface,
                    role=role,
                    kind=kind,
                    ambiguous_with=list(alts),
                ))
                remaining = remaining[: m.start()]
                break
        else:
            # No pattern matched on this iteration — stop peeling.
            break
    # We peeled right-to-left; reverse so the caller sees them in
    # input order (base-first, outermost case last).
    return remaining, list(reversed(suffixes_right_to_left))


def detect_verbal_prefixes(token: str) -> str | None:
    """If the token starts with one or more verbal prefixes, return them
    joined as the prefix chain. Returns None when no prefix matched.

    Conservative: only flags the prefix chain when at least ONE recognized
    prefix matches at the start. Not exhaustive — many verbal forms have
    prefix chains that the caller should also cross-check against
    `morphology.kind='prefix'` entries for the matched verb's lemma. This
    is just a coarse 'looks like a verb form' signal for parse_phrase.
    """
    parts = token.split("-")
    prefix_chain: list[str] = []
    # Sort prefixes longest-first so 'bi₂' wins over 'b' on greedy match.
    by_length = sorted(VERBAL_PREFIXES, key=len, reverse=True)
    for piece in parts[:-1]:  # don't consume the root (last piece)
        # Each piece must be exactly a recognized prefix to count.
        if piece in by_length:
            prefix_chain.append(piece)
        else:
            break
    return "-".join(prefix_chain) if prefix_chain else None


def outermost_case(suffixes: list[Suffix]) -> str | None:
    """From a peeled suffix chain, return the role of the outermost case
    suffix (the rightmost-attached one) or None if no case suffix is present.

    This is the signal callers want for "what grammatical role is this
    nominal token playing?" — possessives and plurals don't change the
    case-bearing slot, only the case itself does.
    """
    for s in reversed(suffixes):
        if s.kind == "case":
            return s.role
    return None
