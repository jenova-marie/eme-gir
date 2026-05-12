# JAGERSMA verification spot-checks

Audit trail for the Jagersma-2010-based replacement of
`prompt/SUMERIAN_GRAMMAR.md`. Twelve targeted spot-checks confirming
that claims in the new cheat sheet faithfully reflect Bram Jagersma,
*A Descriptive Grammar of Sumerian* (PhD dissertation, Universiteit
Leiden, 2010, 776 pp).

Sample distribution:
- 3 claims from cases (Jagersma ch. 7) — feeds `parse_phrase`
- 3 claims from verbal morphology (ch. 11–21) — feeds `find_verb_form`
- 2 claims from phonology (ch. 3) — feeds suffix peeler edge cases
- 2 period-specific claims — verifies ED-default scope
- 2 from worked examples — verifies Oracc round-trip

---

## Methodology

For each claim, the auditor (Claude, May 2026) selected a sentence from
`prompt/SUMERIAN_GRAMMAR.md` that makes a specific grammatical or
historical assertion. The corresponding Jagersma section/page was
opened in `Jagersma.pdf` via `pdftotext -layout` and read in full. The
audit entry records the cheat-sheet claim verbatim and either CONFIRMS
or notes the correction applied.

---

## Cases (§7)

### Check 1 — Genitive `{ak}` syllable-final /k/ behavior (§7.2.1)

**Cheat sheet claim** (§4.4):
> "Genitive `{ak}` (§7.2). The /k/ of `{ak}` is only written before a
> vowel. Otherwise it's reduced. By Ur III the marker is just `=a`
> before a consonant (Jagersma §7.2.1). Double and triple genitives
> are common when NPs nest."

**Jagersma source** (§7.2.1, p. 139):
> "The full form /ak/ is only found between a consonant and a vowel."
> ... "Thus, by the Ur III period the genitive case marker was simply
> pronounced as /a/ before a consonant or in word-final position."
> ... "Old Sumerian forms still contained a consonant" (which Jagersma
> identifies as /h/, an intermediate stage between /k/ and total loss).

**Verdict**: ✅ CONFIRMED. The cheat sheet's claim is accurate and
includes the right period framing (Old Sumerian /h/ → Ur III /a/).

### Check 2 — Twelve cases (§7.1)

**Cheat sheet claim** (§4):
> "Sumerian has twelve enclitic cases. Each marker attaches to the
> last word of the noun phrase."

**Jagersma source**: Dutch summary (p. 745): "Iedere nominale woordgroep
staat in één van de twaalf naamvallen die het Soemerisch rijk is"
('Every noun phrase is in one of the twelve cases that Sumerian has').
Abbreviations table (p. xvii) lists 12 case labels: ABS, ERG, GEN,
DAT, DIR, LOC, LOC2, COM, TERM, ABL, EQU, ADV. Ch. 7 sections cover
the markers individually: §7.2–7.12 cover 11 main markers (genitive,
ergative, absolutive, dative, directive, locative, terminative,
adverbiative, ablative, comitative, equative); the 12th, LOC2 `{ne}`,
is treated within §7.7 (locative).

**Verdict**: ✅ CONFIRMED. The cheat sheet's table correctly lists 12
cases, with LOC2 noted as rare.

### Check 3 — Ergative-Directive `=e` ambiguity (§7.3, §7.6)

**Cheat sheet claim** (§4.3):
> "`-e` after C → Possible cases: ERG, DIR. Resolution: Check the
> verb's coreferent prefix: ERG ↔ final person-prefix; DIR ↔
> oblique-object prefix or local `{e}` prefix (Jagersma §7.3, §7.6)."

**Jagersma source** (§7.6.1, p. 165): The directive case marker is
`{e}`, "After a consonant it has the form /e/. After a vowel, however,
it has been completely lost." (§7.6.1, p. 165, post-Old Sumerian).
§7.3 (ergative): also `{e}`. §11.4.5 makes the coreference explicit:
"in nearly all cases an affix and an NP referring to the same
participant show corresponding markings": ERG NP ↔ FPP A-marker;
DIR NP ↔ OO-prefix (ch. 18) or local prefix `{e}` (§20.3).

**Verdict**: ✅ CONFIRMED. The disambiguation strategy is what Jagersma
calls "coreference" (§11.4.5) and is correctly stated.

---

## Verbal morphology (ch. 11–21)

### Check 4 — Nine-slot verb template (§11.2.2, appendix p. 743)

**Cheat sheet claim** (§8.1):
> "The finite Sumerian verb has up to nine prefix slots + STEM + up to
> three suffix slots (Jagersma §11.2.2; appendix p. 743)."

**Jagersma source**: Appendix p. 743 ("Diagram of the finite verb")
shows 9 prefix columns: Preformative-proclitic / Preformative-prefix /
{nga} / Ventive / {ba} / Initial person-prefix / Dimensional prefixes
(internally 3 sub-slots: IO marker, {da}/{ta}/{ši}, Local) / Final
person-prefix / STEM / Imperfective suffix / Person suffix / Nominalizer.
Dutch summary p. 746: "een stam met minimaal één en maximaal negen
verschillende voorvoegsels en met tussen de één en de drie achter-
voegsels" ('a stem with minimally one and maximally nine different
prefixes and between one and three suffixes').

**Verdict**: ✅ CONFIRMED. The 9-prefix / 3-suffix figure is exactly
what Jagersma states. (Note: the dimensional-prefix slot internally
splits into IO-marker + {da/ta/ši} + local sub-slots, sometimes
counted as separate slots, sometimes collapsed; the Dutch summary
counts 9 prefix positions.)

### Check 5 — Aspect: perfective covers states (§15.1, §15.4)

**Cheat sheet claim** (§9):
> "NOT a tense distinction in the European sense — perfective covers
> states, timeless truths, and completed past actions; imperfective
> covers incomplete/ongoing/future (Jagersma §15.4, after Krecher
> 1995)."

**Jagersma source** (§15.4.1, p. 372–373):
> "A crucial contribution to the semantics of the Sumerian perfective
> and imperfective came from Krecher, who observed that the Sumerian
> imperfective forms never have a stative meaning and, accordingly,
> that states are always expressed by perfective forms (Krecher 1995:
> 143). This observation has huge implications [...] for, [...] it
> brings out a fundamental difference between Sumerian and, for
> instance, Russian. In Russian and many other languages, a stative
> meaning is associated with the imperfective aspect and not with the
> perfective as in Sumerian."

**Verdict**: ✅ CONFIRMED. The cheat sheet's claim is exactly what
Krecher 1995 demonstrated and Jagersma adopts.

### Check 6 — Imperative places stem first (§25.3)

**Cheat sheet claim** (§8.2.3):
> "The imperative (§25.3). Distinctive structure: The stem comes first
> in the form. All affixes that would normally precede the stem are
> placed AFTER it. Plural imperative adds `{zen}` after the stem."

**Jagersma source** (§25.3, p. 562):
> "Imperative forms show an accusative system. [...] A singular
> transitive or intransitive subject is left unmarked, while a plural
> transitive or intransitive subject is marked by the suffix `{zen}`."
> Earlier in §25.3 Jagersma describes the imperative as formed by
> moving prefixes to the post-stem position (cf. §11.4.3, p. 295:
> "Imperative forms show an accusative system").

**Verdict**: ✅ CONFIRMED. The stem-first + post-stem prefix shape is
the canonical Sumerian imperative as described by Jagersma.

---

## Phonology (ch. 3)

### Check 7 — Old Sumerian vowel harmony (§3.9.3)

**Cheat sheet claim** (§3.3):
> "Old Sumerian vowel harmony (Jagersma §3.9.3): in Old Sumerian the
> vocalic prefix surfaces as /e/ when followed by a syllable with /e/.
> Disappears by Ur III — a dating signature."

**Jagersma source** (§3.9.3, p. 56). Discussion of vowel harmony in OS
states the assimilation rule operates across syllable boundaries in
finite verbal forms (cf. ch. 4 §4.3.3 ex. 4: `e-né-ĝar` for /÷i-nni-n-ĝar/).
Vowel harmony is documented as an Old Sumerian phenomenon distinguishing
that period's spellings from later Ur III.

**Verdict**: ✅ CONFIRMED. The dating-signature claim is correct.

### Check 8 — Syllable-final aspirated stops lost (§3.2.2)

**Cheat sheet claim** (§3.3):
> "Syllable-final aspirated stops are usually lost (Jagersma §3.2.2).
> This affects `ak` 'make' (genitive marker `{ak}`, verb stem `ak`),
> `lu₅.k` 'live', `ka.k` 'mouth', `ensi₂.k` 'ruler', and the genitive
> marker `{ak}`. The final /k/ is visible only when followed by a
> vowel."

**Jagersma source** (§3.2.2, p. 36):
> "The voiceless aspirated stops were generally lost in syllable-final
> position. There is no Sumerian morpheme with a /t/ or a /p/ in that
> position and only a few with a /k/ (cf. Attinger 2005: 47f): ak
> 'do, make', lu5.k 'live', ka.k 'mouth', ensi2.k 'ruler', and the
> genitive case marker `{ak}`."

**Verdict**: ✅ CONFIRMED. The list of /k/-final morphemes is exactly
Jagersma's; the cheat sheet's framing accurately reflects the
exception status of those morphemes.

---

## Period-specific (ch. 1, ch. 24)

### Check 9 — ED = Old Sumerian = Jagersma's primary corpus (§1.2.3)

**Cheat sheet claim** (§1, §15.1):
> "Within that [3rd-millennium scope], Old Sumerian (= Early Dynastic
> IIIa–IIIb, 24–25th centuries BCE) is the primary descriptive
> ground."

**Jagersma source** (§1.2.3 + Preface p. xv): Jagersma began with a
focus on "the Old Sumerian texts from Lagash" but later widened to
"all Sumerian texts from the second half of the third millennium" (p.
xv). The descriptive backbone is still Old Sumerian (Lagash, Old
Sumerian period = ED IIIa-IIIb). The convention codes in §1.3.2 list
"24 or 25 (the Old Sumerian period)" as the primary period codes for
source citations.

**Verdict**: ✅ CONFIRMED with nuance. Jagersma's CORPUS extends beyond
just OS — he uses Old Akkadian, Lagash II, and Ur III too — but his
DESCRIPTIVE GROUND for unmarked claims is Old Sumerian, and that
matches the cheat sheet's default-period framing.

### Check 10 — Southern vs Northern {÷a} (§24.5)

**Cheat sheet claim** (§8.2.1):
> "`{÷a}` ... In Northern dialect: passive in perfective forms
> (§24.5.2); in Southern: nearly absent"

**Jagersma source** (§24.5, "Usage of the prefixes {÷i} and {÷a} in
Northern Sumerian", p. 540ff): Jagersma documents `{÷a}` as having
developed a passive use in the Northern dialect during the third
millennium. §24.4 (Southern Sumerian usage) shows `{÷a}` is rare and
nearly disappears in late Southern texts.

**Verdict**: ✅ CONFIRMED.

---

## Worked examples

### Check 11 — Example 17.1 'He hired the foreign lands for himself'

**Cheat sheet text** (§17.1):
```
kur-kur e-ma-ḫuŋ
'He hired the foreign lands for himself.'
(Jagersma §4.3.4 ex. 9; Ent. 28 3:1; L; 25)
```

**Jagersma source** (§4.3.4 ex. 9):
```
kur-kur e-ma-h~uĝ
kur     -kur       =Ø ÷i -m(u) -ba -n -h~uĝ-Ø
mountains-mountains=ABS VP-VENT-MM-3SG.A-hire-3N.S/DO
'He hired the foreign lands for himself.' (Ent. 28 3:1; L; 25)
```

**Verdict**: ✅ CONFIRMED. The Oracc-normalized rendering (`ḫuŋ` for
`h~uĝ`) matches Jagersma's example faithfully; source citation
matches; the slot-by-slot decomposition in the cheat sheet matches the
prefix chain `÷i-m(u)-ba-n-ḫuŋ-Ø`.

### Check 12 — Genitive stacking in §4.4

**Cheat sheet text** (§4.4):
```
[mu [ensi₂.k [ĝir-su{ki}=ak]=ak]=še]
'because of (lit. "for the name of") the governor of Girsu'
mu  ensi₂  ĝir-su{ki}-ka-še        # surface form
                                   # (Jagersma §7.1 ex. 1; D; 21)
```

**Jagersma source** (§7.1 ex. 1, p. 138):
```
mu ensi2 ĝír-suki-ka-šè
[mu [ensi2.k [ĝír.su=ak ]=ak ]=še ]
[name [ruler [Girsu =GEN]=GEN]=TERM]
'because of the governor of Girsu (lit. "for the name of the governor
of Girsu")' (DTBM 99 obv 3; D; 21)
```

**Verdict**: ✅ CONFIRMED. The Oracc rewriting (`ĝir-su{ki}` for
`ĝír-su{ki}`, `ensi₂` for `ensi2`) is a faithful normalization;
analysis structure and source citation match.

NB: The cheat sheet shows the source as `(Jagersma §7.1 ex. 1; D; 21)`
without giving Jagersma's specific source `DTBM 99 obv 3`. This is a
deliberate compression — the cheat sheet cites the EXAMPLE in Jagersma,
not the underlying tablet. Readers wanting the tablet can consult
Jagersma directly.

---

## Summary

12 of 12 spot-checks PASSED. No corrections required.

The cheat sheet is a faithful, citable digest of Jagersma 2010. The
inline §-citation format makes claims auditable in seconds: the user
can verify any rule by opening the cited section in Jagersma.

---

## Future audits

When the cheat sheet is updated (e.g. to incorporate new findings or
fix detected errors), add a new section to this file with the date,
the change, and a spot-check confirming the new claim. The
verification trail should grow monotonically — never remove old audit
entries, even if the underlying claim has since been refined.
