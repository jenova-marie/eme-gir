"""Pydantic response models for the MCP tools, organized per-server domain.

Each response model documents the actual JSON shape a tool returns, so
FastMCP can emit an outputSchema in tools/list. Without these, every
tool's schema defaults to a generic `{result: dict[str, Any]}` wrapper
that's useless for LLM reasoning and triggers the "OUTPUT SCHEMA
RECOMMENDED" warning in MCP client UIs.

Submodule layout (all importable as `eme_gir.models.<submodule>`):

| Submodule | Domain | Selected models |
|---|---|---|
| `common` | Cross-domain building blocks | `_Permissive`, `ErrorResponse`, `EntryHeader`, `AttestationLine`, `Suffix` |
| `epsd2`  | Eme-gir dictionary + corpus  | `TranslateEnglishResponse`, `LookupEntryResponse`, `SeeExamplesResponse`, `FindVerbFormResponse`, `ParsePhraseResponse`, … |
| `etcsl`  | Oxford literary corpus       | `ETCSLSearchEnglishResponse`, `ETCSLLookupTextResponse`, … |
| `cdli`   | CDLI artifact catalogue      | `CDLIArtifact`, `LookupArtifactResponse`, `FindArtifactsResponse` |
| `ogsl`   | OGSL sign rendering          | `SignInfo`, `LookupSignResponse`, `CuneifyResponse` |
| `ummia`  | Ummia teaching MCP           | `GrammarReferenceResponse` |

The flat re-exports below preserve the pre-split import surface:
existing callers can keep writing `from eme_gir.models import X` for
any symbol. New code in per-server entry points should prefer the
specific submodule import (`from eme_gir.models.epsd2 import …`) to
make the server's data dependencies explicit.

Conventions:
- Fields use the same NAMES + TYPES as the legacy dict literals in
  mcp_server.py — the models serialize identically so existing clients
  see no change in tool output.
- Each tool returns its success-shape model OR `ErrorResponse`;
  FastMCP serializes the Union as JSON Schema `anyOf`.
- `ConfigDict(extra="allow")` is set on every response model so future
  additions to the dict shape don't break in-flight upgrades.
"""

from __future__ import annotations

from .cdli import (
    CDLIArtifact,
    FindArtifactsResponse,
    LookupArtifactResponse,
)
from .common import (
    AttestationLine,
    EntryHeader,
    ErrorResponse,
    Suffix,
    _Permissive,
)
from .epsd2 import (
    AnalyzeFormResponse,
    AnalyzeMatch,
    CaseChunk,
    CollocationHit,
    Compound,
    FindCollocationsResponse,
    FindCompoundResponse,
    FindPhrasePatternResponse,
    FindVerbFormResponse,
    GetInflectionsResponse,
    LemmaCandidate,
    LookupEntryResponse,
    MorphRow,
    ParsePhraseResponse,
    PatternToken,
    Period,
    PhrasePatternHit,
    SeeExamplesResponse,
    Sense,
    Spelling,
    TokenAnalysis,
    TokenCandidate,
    TranslateEnglishResponse,
    TranslateSumerianResponse,
    VerbFormFilterSpec,
    VerbFormMatch,
)
from .etcsl import (
    ETCSLBlock,
    ETCSLEnglishHit,
    ETCSLLemmaHit,
    ETCSLLine,
    ETCSLLinesWithLemmaResponse,
    ETCSLLookupTextResponse,
    ETCSLSearchEnglishResponse,
    ETCSLSearchSumerianResponse,
)
from .ogsl import (
    CuneifyResponse,
    LookupSignResponse,
    SignInfo,
)
from .ummia import GrammarReferenceResponse

__all__ = [
    # common
    "_Permissive",
    "AttestationLine",
    "EntryHeader",
    "ErrorResponse",
    "Suffix",
    # epsd2
    "AnalyzeFormResponse",
    "AnalyzeMatch",
    "CaseChunk",
    "CollocationHit",
    "Compound",
    "FindCollocationsResponse",
    "FindCompoundResponse",
    "FindPhrasePatternResponse",
    "FindVerbFormResponse",
    "GetInflectionsResponse",
    "LemmaCandidate",
    "LookupEntryResponse",
    "MorphRow",
    "ParsePhraseResponse",
    "PatternToken",
    "Period",
    "PhrasePatternHit",
    "SeeExamplesResponse",
    "Sense",
    "Spelling",
    "TokenAnalysis",
    "TokenCandidate",
    "TranslateEnglishResponse",
    "TranslateSumerianResponse",
    "VerbFormFilterSpec",
    "VerbFormMatch",
    # etcsl
    "ETCSLBlock",
    "ETCSLEnglishHit",
    "ETCSLLemmaHit",
    "ETCSLLine",
    "ETCSLLinesWithLemmaResponse",
    "ETCSLLookupTextResponse",
    "ETCSLSearchEnglishResponse",
    "ETCSLSearchSumerianResponse",
    # cdli
    "CDLIArtifact",
    "FindArtifactsResponse",
    "LookupArtifactResponse",
    # ogsl
    "CuneifyResponse",
    "LookupSignResponse",
    "SignInfo",
    # ummia
    "GrammarReferenceResponse",
]
