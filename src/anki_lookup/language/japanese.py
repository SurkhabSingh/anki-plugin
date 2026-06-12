"""Japanese deinflection using a bounded condition-aware transform graph."""

from __future__ import annotations

from .generic import GenericLanguageProfile
from .models import MorphologyCandidate
from .transformer import SuffixTransform, expand_suffix_transforms

_V1 = frozenset({"v1"})
_VS = frozenset({"vs"})
_VK = frozenset({"vk"})
_V5U = frozenset({"v5u"})
_V5K = frozenset({"v5k"})
_V5R = frozenset({"v5r"})
_ADJ_I = frozenset({"adj-i"})
_TE = frozenset({"-te"})
_MASU = frozenset({"-masu"})

_GODAN_STEMS = (
    ("い", "う", "v5u"),
    ("き", "く", "v5k"),
    ("ぎ", "ぐ", "v5g"),
    ("し", "す", "v5s"),
    ("ち", "つ", "v5t"),
    ("に", "ぬ", "v5n"),
    ("び", "ぶ", "v5b"),
    ("み", "む", "v5m"),
    ("り", "る", "v5r"),
)

_GODAN_A_STEMS = (
    ("わ", "う", "v5u"),
    ("か", "く", "v5k"),
    ("が", "ぐ", "v5g"),
    ("さ", "す", "v5s"),
    ("た", "つ", "v5t"),
    ("な", "ぬ", "v5n"),
    ("ば", "ぶ", "v5b"),
    ("ま", "む", "v5m"),
    ("ら", "る", "v5r"),
)

_GODAN_E_STEMS = (
    ("え", "う", "v5u"),
    ("け", "く", "v5k"),
    ("げ", "ぐ", "v5g"),
    ("せ", "す", "v5s"),
    ("て", "つ", "v5t"),
    ("ね", "ぬ", "v5n"),
    ("べ", "ぶ", "v5b"),
    ("め", "む", "v5m"),
    ("れ", "る", "v5r"),
)

_GODAN_O_STEMS = (
    ("お", "う", "v5u"),
    ("こ", "く", "v5k"),
    ("ご", "ぐ", "v5g"),
    ("そ", "す", "v5s"),
    ("と", "つ", "v5t"),
    ("の", "ぬ", "v5n"),
    ("ぼ", "ぶ", "v5b"),
    ("も", "む", "v5m"),
    ("ろ", "る", "v5r"),
)


def _transform(
    suffix: str,
    replacement: str,
    reasons: str | tuple[str, ...],
    conditions_out: frozenset[str],
    *,
    conditions_in: frozenset[str] = frozenset(),
    minimum_stem_length: int = 1,
    terminal: bool = False,
) -> SuffixTransform:
    return SuffixTransform(
        suffix=suffix,
        replacement=replacement,
        reasons=(reasons,) if isinstance(reasons, str) else reasons,
        conditions_in=conditions_in,
        conditions_out=conditions_out,
        minimum_stem_length=minimum_stem_length,
        terminal=terminal,
    )


def _polite_rules() -> tuple[SuffixTransform, ...]:
    rules = [
        _transform("ませんでした", "ます", ("negative", "-た"), _MASU),
        _transform("ませんかった", "ます", ("negative", "-た"), _MASU),
        _transform("ません", "ます", "negative", _MASU),
        _transform("ましたら", "ます", "-たら", _MASU),
        _transform("ましたり", "ます", "-たり", _MASU),
        _transform("ました", "ます", "-た", _MASU),
        _transform("まして", "ます", "-て", _MASU),
        _transform("ますれば", "ます", "-ば", _MASU),
        _transform("ますりゃ", "ます", ("-ば", "-ゃ"), _MASU),
        _transform("ましょう", "ます", "volitional", _MASU),
        _transform("ましょっか", "ます", "volitional slang", _MASU),
        _transform("ますまい", "ます", "-まい", _MASU),
        _transform("ます", "る", "-ます", _V1, conditions_in=_MASU),
    ]
    for stem, dictionary_ending, condition in _GODAN_STEMS:
        rules.append(
            _transform(
                stem + "ます",
                dictionary_ending,
                "-ます",
                frozenset({condition}),
                conditions_in=_MASU,
            )
        )
    rules.extend(
        (
            _transform(
                "します",
                "する",
                "-ます",
                _VS,
                conditions_in=_MASU,
                minimum_stem_length=0,
            ),
            _transform(
                "きます",
                "くる",
                "-ます",
                _VK,
                conditions_in=_MASU,
                minimum_stem_length=0,
            ),
            _transform(
                "来ます",
                "来る",
                "-ます",
                _VK,
                conditions_in=_MASU,
                minimum_stem_length=0,
            ),
            _transform(
                "來ます",
                "來る",
                "-ます",
                _VK,
                conditions_in=_MASU,
                minimum_stem_length=0,
            ),
        )
    )
    return tuple(rules)


def _te_and_past_rules() -> tuple[SuffixTransform, ...]:
    return (
        _transform("くて", "い", "-て", _ADJ_I, conditions_in=_TE),
        _transform("て", "る", "-て", _V1, conditions_in=_TE),
        _transform("いて", "く", "-て", frozenset({"v5k"}), conditions_in=_TE),
        _transform("いで", "ぐ", "-て", frozenset({"v5g"}), conditions_in=_TE),
        _transform("して", "す", "-て", frozenset({"v5s"}), conditions_in=_TE),
        _transform("って", "う", "-て", frozenset({"v5u"}), conditions_in=_TE),
        _transform("って", "つ", "-て", frozenset({"v5t"}), conditions_in=_TE),
        _transform("って", "る", "-て", frozenset({"v5r"}), conditions_in=_TE),
        _transform("んで", "ぬ", "-て", frozenset({"v5n"}), conditions_in=_TE),
        _transform("んで", "ぶ", "-て", frozenset({"v5b"}), conditions_in=_TE),
        _transform("んで", "む", "-て", frozenset({"v5m"}), conditions_in=_TE),
        _transform(
            "して",
            "する",
            "-て",
            _VS,
            conditions_in=_TE,
            minimum_stem_length=0,
        ),
        _transform(
            "きて",
            "くる",
            "-て",
            _VK,
            conditions_in=_TE,
            minimum_stem_length=0,
        ),
        _transform("来て", "来る", "-て", _VK, conditions_in=_TE, minimum_stem_length=0),
        _transform("來て", "來る", "-て", _VK, conditions_in=_TE, minimum_stem_length=0),
        _transform("かった", "い", "-た", _ADJ_I),
        _transform("た", "る", "-た", _V1),
        _transform("いた", "く", "-た", frozenset({"v5k"})),
        _transform("いだ", "ぐ", "-た", frozenset({"v5g"})),
        _transform("した", "す", "-た", frozenset({"v5s"})),
        _transform("った", "う", "-た", frozenset({"v5u"})),
        _transform("った", "つ", "-た", frozenset({"v5t"})),
        _transform("った", "る", "-た", frozenset({"v5r"})),
        _transform("んだ", "ぬ", "-た", frozenset({"v5n"})),
        _transform("んだ", "ぶ", "-た", frozenset({"v5b"})),
        _transform("んだ", "む", "-た", frozenset({"v5m"})),
        _transform("した", "する", "-た", _VS, minimum_stem_length=0),
        _transform("きた", "くる", "-た", _VK, minimum_stem_length=0),
        _transform("来た", "来る", "-た", _VK, minimum_stem_length=0),
        _transform("來た", "來る", "-た", _VK, minimum_stem_length=0),
    )


def _auxiliary_rules() -> tuple[SuffixTransform, ...]:
    return (
        _transform("ている", "て", "-いる", _TE, conditions_in=_V1),
        _transform("でいる", "で", "-いる", _TE, conditions_in=_V1),
        _transform("てる", "て", "-いる", _TE, conditions_in=_V1),
        _transform("でる", "で", "-いる", _TE, conditions_in=_V1),
        _transform("ておる", "て", "-いる", _TE, conditions_in=_V5R),
        _transform("でおる", "で", "-いる", _TE, conditions_in=_V5R),
        _transform("とる", "て", "-いる", _TE, conditions_in=_V5R),
        _transform("ておく", "て", "-おく", _TE, conditions_in=_V5K),
        _transform("でおく", "で", "-おく", _TE, conditions_in=_V5K),
        _transform("とく", "て", "-おく", _TE, conditions_in=_V5K),
        _transform("どく", "で", "-おく", _TE, conditions_in=_V5K),
        _transform("ないでおく", "ない", "-おく", _ADJ_I, conditions_in=_V5K),
        _transform("ないどく", "ない", "-おく", _ADJ_I, conditions_in=_V5K),
        _transform("ないでいる", "ない", "-いる", _ADJ_I, conditions_in=_V1),
        _transform("てしまう", "て", "-しまう", _TE, conditions_in=_V5U),
        _transform("でしまう", "で", "-しまう", _TE, conditions_in=_V5U),
        _transform("ちゃう", "て", "-ちゃう", _TE, conditions_in=_V5U),
        _transform("じゃう", "で", "-ちゃう", _TE, conditions_in=_V5U),
    )


def _negative_rules() -> tuple[SuffixTransform, ...]:
    rules = [
        _transform(
            "しなくて",
            "する",
            ("negative", "-て"),
            _VS,
            minimum_stem_length=0,
        ),
        _transform(
            "しなかった",
            "する",
            ("negative", "-た"),
            _VS,
            minimum_stem_length=0,
        ),
        _transform(
            "しない",
            "する",
            "negative",
            _VS,
            conditions_in=_ADJ_I,
            minimum_stem_length=0,
        ),
        _transform(
            "こなくて",
            "くる",
            ("negative", "-て"),
            _VK,
            minimum_stem_length=0,
        ),
        _transform(
            "こなかった",
            "くる",
            ("negative", "-た"),
            _VK,
            minimum_stem_length=0,
        ),
        _transform(
            "こない",
            "くる",
            "negative",
            _VK,
            conditions_in=_ADJ_I,
            minimum_stem_length=0,
        ),
        _transform("なくて", "る", ("negative", "-て"), _V1),
        _transform("なかった", "る", ("negative", "-た"), _V1),
        _transform("ない", "る", "negative", _V1, conditions_in=_ADJ_I),
        _transform("くなかった", "い", ("negative", "-た"), _ADJ_I),
        _transform("くない", "い", "negative", _ADJ_I, conditions_in=_ADJ_I),
        _transform("くありませんでした", "い", ("-ます", "negative", "-た"), _ADJ_I),
        _transform("くありませんかった", "い", ("-ます", "negative", "-た"), _ADJ_I),
        _transform("くありません", "い", ("-ます", "negative"), _ADJ_I),
    ]
    for stem, dictionary_ending, condition in _GODAN_A_STEMS:
        rules.extend(
            (
                _transform(
                    stem + "なくて",
                    dictionary_ending,
                    ("negative", "-て"),
                    frozenset({condition}),
                ),
                _transform(
                    stem + "なかった",
                    dictionary_ending,
                    ("negative", "-た"),
                    frozenset({condition}),
                ),
                _transform(
                    stem + "ない",
                    dictionary_ending,
                    "negative",
                    frozenset({condition}),
                    conditions_in=_ADJ_I,
                ),
            )
        )
    return tuple(rules)


def _derived_verb_rules() -> tuple[SuffixTransform, ...]:
    rules = [
        _transform("られる", "る", "potential or passive", _V1, conditions_in=_V1),
        _transform("させる", "る", "causative", _V1, conditions_in=_V1),
        _transform(
            "さす",
            "る",
            "short causative",
            _V1,
            conditions_in=frozenset({"v5s"}),
        ),
        _transform("ろ", "る", "imperative", _V1),
        _transform("れば", "る", "-ば", _V1),
        _transform("りゃ", "る", ("-ば", "-ゃ"), _V1),
        _transform("ちゃ", "る", "-ちゃ", _V1),
        _transform("ちまう", "る", "-ちまう", _V1),
        _transform("なさい", "る", "-なさい", _V1),
        _transform("そう", "る", "-そう", _V1),
        _transform("すぎる", "る", "-すぎる", _V1, conditions_in=_V1),
        _transform("過ぎる", "る", "-過ぎる", _V1, conditions_in=_V1),
        _transform("たい", "る", "-たい", _V1, conditions_in=_ADJ_I),
        _transform("ず", "る", "-ず", _V1),
        _transform("ぬ", "る", "-ぬ", _V1),
        _transform("んかった", "る", ("-ん", "-た"), _V1),
        _transform("んばかり", "る", "-んばかり", _V1),
        _transform("んとする", "る", "-んとする", _V1),
        _transform("ん", "る", "-ん", _V1),
        _transform("ざる", "る", "-ざる", _V1),
        _transform("ねば", "る", "-ねば", _V1),
        _transform("にゃ", "る", ("-ねば", "-ゃ"), _V1),
        _transform("よう", "る", "volitional", _V1),
        _transform("よっか", "る", "volitional slang", _V1),
        _transform("るまい", "る", "-まい", _V1),
        _transform("まい", "る", "-まい", _V1),
        _transform("たがる", "たい", "-がる", _ADJ_I, conditions_in=_V5R),
        _transform("やがる", "る", "-やがる", _V1, conditions_in=_V5R),
        _transform("したら", "する", "-たら", _VS, minimum_stem_length=0),
        _transform("したり", "する", "-たり", _VS, minimum_stem_length=0),
        _transform("しろ", "する", "imperative", _VS, minimum_stem_length=0),
        _transform("すれば", "する", "-ば", _VS, minimum_stem_length=0),
        _transform("しよう", "する", "volitional", _VS, minimum_stem_length=0),
        _transform(
            "できる",
            "する",
            "potential",
            _VS,
            conditions_in=_V1,
            minimum_stem_length=0,
        ),
        _transform(
            "される",
            "する",
            "passive",
            _VS,
            conditions_in=_V1,
            minimum_stem_length=0,
        ),
        _transform(
            "させる",
            "する",
            "causative",
            _VS,
            conditions_in=_V1,
            minimum_stem_length=0,
        ),
        _transform(
            "さす",
            "する",
            "short causative",
            _VS,
            conditions_in=frozenset({"v5s"}),
            minimum_stem_length=0,
        ),
        _transform("きたら", "くる", "-たら", _VK, minimum_stem_length=0),
        _transform("きたり", "くる", "-たり", _VK, minimum_stem_length=0),
        _transform(
            "こられる",
            "くる",
            "potential or passive",
            _VK,
            conditions_in=_V1,
            minimum_stem_length=0,
        ),
        _transform(
            "こさせる",
            "くる",
            "causative",
            _VK,
            conditions_in=_V1,
            minimum_stem_length=0,
        ),
        _transform("こい", "くる", "imperative", _VK, minimum_stem_length=0),
        _transform("くれば", "くる", "-ば", _VK, minimum_stem_length=0),
        _transform("こよう", "くる", "volitional", _VK, minimum_stem_length=0),
    ]
    for stem, dictionary_ending, condition in _GODAN_A_STEMS:
        output = frozenset({condition})
        rules.extend(
            (
                _transform(
                    stem + "れる",
                    dictionary_ending,
                    "passive",
                    output,
                    conditions_in=_V1,
                ),
                _transform(
                    stem + "せる",
                    dictionary_ending,
                    "causative",
                    output,
                    conditions_in=_V1,
                ),
                _transform(
                    stem + "す",
                    dictionary_ending,
                    "short causative",
                    output,
                    conditions_in=frozenset({"v5s"}),
                ),
                _transform(stem + "ず", dictionary_ending, "-ず", output),
                _transform(stem + "ぬ", dictionary_ending, "-ぬ", output),
                _transform(stem + "んかった", dictionary_ending, ("-ん", "-た"), output),
                _transform(stem + "んばかり", dictionary_ending, "-んばかり", output),
                _transform(stem + "んとする", dictionary_ending, "-んとする", output),
                _transform(stem + "ん", dictionary_ending, "-ん", output),
                _transform(stem + "ざる", dictionary_ending, "-ざる", output),
                _transform(stem + "ねば", dictionary_ending, "-ねば", output),
                _transform(
                    stem + "にゃ",
                    dictionary_ending,
                    ("-ねば", "-ゃ"),
                    output,
                ),
            )
        )
    for stem, dictionary_ending, condition in _GODAN_E_STEMS:
        output = frozenset({condition})
        rules.extend(
            (
                _transform(
                    stem + "る",
                    dictionary_ending,
                    "potential",
                    output,
                    conditions_in=_V1,
                ),
                _transform(stem, dictionary_ending, "imperative", output),
                _transform(stem + "ば", dictionary_ending, "-ば", output),
            )
        )
    for stem, dictionary_ending, condition in _GODAN_O_STEMS:
        output = frozenset({condition})
        rules.extend(
            (
                _transform(stem + "う", dictionary_ending, "volitional", output),
                _transform(stem + "っか", dictionary_ending, "volitional slang", output),
            )
        )
    for stem, dictionary_ending, condition in _GODAN_STEMS:
        output = frozenset({condition})
        conditional_contraction = "や" if condition == "v5u" else stem + "ゃ"
        rules.extend(
            (
                _transform(
                    conditional_contraction,
                    dictionary_ending,
                    ("-ば", "-ゃ"),
                    output,
                ),
                _transform(stem + "なさい", dictionary_ending, "-なさい", output),
                _transform(stem + "そう", dictionary_ending, "-そう", output),
                _transform(
                    stem + "すぎる",
                    dictionary_ending,
                    "-すぎる",
                    output,
                    conditions_in=_V1,
                ),
                _transform(
                    stem + "過ぎる",
                    dictionary_ending,
                    "-過ぎる",
                    output,
                    conditions_in=_V1,
                ),
                _transform(
                    stem + "たい",
                    dictionary_ending,
                    "-たい",
                    output,
                    conditions_in=_ADJ_I,
                ),
                _transform(
                    stem + "やがる",
                    dictionary_ending,
                    "-やがる",
                    output,
                    conditions_in=_V5R,
                ),
                _transform(
                    dictionary_ending + "まい",
                    dictionary_ending,
                    "-まい",
                    output,
                ),
            )
        )
    return tuple(rules)


def _contracted_te_rules() -> tuple[SuffixTransform, ...]:
    conjugations = (
        ("っ", "う", "v5u", "ちゃ", "ちまう"),
        ("い", "く", "v5k", "ちゃ", "ちまう"),
        ("い", "ぐ", "v5g", "じゃ", "じまう"),
        ("し", "す", "v5s", "ちゃ", "ちまう"),
        ("っ", "つ", "v5t", "ちゃ", "ちまう"),
        ("ん", "ぬ", "v5n", "じゃ", "じまう"),
        ("ん", "ぶ", "v5b", "じゃ", "じまう"),
        ("ん", "む", "v5m", "じゃ", "じまう"),
        ("っ", "る", "v5r", "ちゃ", "ちまう"),
    )
    rules: list[SuffixTransform] = []
    for stem, dictionary_ending, condition, short, emphatic in conjugations:
        output = frozenset({condition})
        rules.extend(
            (
                _transform(stem + short, dictionary_ending, "-ちゃ", output),
                _transform(stem + emphatic, dictionary_ending, "-ちまう", output),
            )
        )
    return tuple(rules)


def _irregular_iku_rules() -> tuple[SuffixTransform, ...]:
    rules: list[SuffixTransform] = []
    for dictionary_form in ("いく", "行く", "逝く", "往く"):
        stem = dictionary_form[:-1]
        output = frozenset({"v5k"})
        rules.extend(
            (
                _transform(stem + "った", dictionary_form, "-た", output, minimum_stem_length=0),
                _transform(
                    stem + "って",
                    dictionary_form,
                    "-て",
                    output,
                    conditions_in=_TE,
                    minimum_stem_length=0,
                ),
                _transform(
                    stem + "ったら",
                    dictionary_form,
                    "-たら",
                    output,
                    minimum_stem_length=0,
                ),
                _transform(
                    stem + "ったり",
                    dictionary_form,
                    "-たり",
                    output,
                    minimum_stem_length=0,
                ),
            )
        )
    return tuple(rules)


def _conditional_past_rules() -> tuple[SuffixTransform, ...]:
    conjugations = (
        ("た", "る", "v1"),
        ("いた", "く", "v5k"),
        ("いだ", "ぐ", "v5g"),
        ("した", "す", "v5s"),
        ("った", "う", "v5u"),
        ("った", "つ", "v5t"),
        ("った", "る", "v5r"),
        ("んだ", "ぬ", "v5n"),
        ("んだ", "ぶ", "v5b"),
        ("んだ", "む", "v5m"),
    )
    rules: list[SuffixTransform] = []
    for surface, dictionary_ending, condition in conjugations:
        output = frozenset({condition})
        rules.extend(
            (
                _transform(surface + "ら", dictionary_ending, "-たら", output),
                _transform(surface + "り", dictionary_ending, "-たり", output),
            )
        )
    return tuple(rules)


def _adjective_rules() -> tuple[SuffixTransform, ...]:
    return (
        _transform("そう", "い", "-そう", _ADJ_I),
        _transform("すぎる", "い", "-すぎる", _ADJ_I, conditions_in=_V1),
        _transform("過ぎる", "い", "-過ぎる", _ADJ_I, conditions_in=_V1),
        _transform("かったら", "い", "-たら", _ADJ_I),
        _transform("かったり", "い", "-たり", _ADJ_I),
        _transform("く", "い", "-く", _ADJ_I),
        _transform("さ", "い", "-さ", _ADJ_I),
        _transform("き", "い", "-き", _ADJ_I),
        _transform("げ", "い", "-げ", _ADJ_I),
        _transform("気", "い", "-げ", _ADJ_I),
        _transform("がる", "い", "-がる", _ADJ_I, conditions_in=_V5R),
    )


def _continuative_rules() -> tuple[SuffixTransform, ...]:
    rules = [
        _transform("し", "する", "continuative", _VS, minimum_stem_length=0),
        _transform("き", "くる", "continuative", _VK, minimum_stem_length=0),
    ]
    for stem, dictionary_ending, condition in _GODAN_STEMS:
        rules.append(
            _transform(
                stem,
                dictionary_ending,
                "continuative",
                frozenset({condition}),
            )
        )
    rules.append(
        _transform(
            "",
            "る",
            "continuative",
            _V1,
            terminal=True,
        )
    )
    return tuple(rules)


_RULES = (
    *_polite_rules(),
    *_auxiliary_rules(),
    *_negative_rules(),
    *_derived_verb_rules(),
    *_contracted_te_rules(),
    *_irregular_iku_rules(),
    *_conditional_past_rules(),
    *_adjective_rules(),
    *_te_and_past_rules(),
    *_continuative_rules(),
)


class JapaneseLanguageProfile(GenericLanguageProfile):
    def language_codes(self) -> tuple[str, ...]:
        return ("ja", "jpn")

    def expand_query(self, value: str) -> tuple[MorphologyCandidate, ...]:
        return expand_suffix_transforms(self.normalize(value), _RULES)
