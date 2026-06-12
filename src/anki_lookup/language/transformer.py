"""Bounded condition-aware suffix transformation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .models import MorphologyCandidate


@dataclass(frozen=True)
class SuffixTransform:
    suffix: str
    replacement: str
    reasons: tuple[str, ...]
    conditions_in: frozenset[str]
    conditions_out: frozenset[str]
    minimum_stem_length: int = 1
    terminal: bool = False

    def apply(self, value: str) -> str | None:
        if self.suffix:
            if not value.endswith(self.suffix):
                return None
            stem_length = len(value) - len(self.suffix)
            if stem_length < self.minimum_stem_length:
                return None
            return value[:stem_length] + self.replacement
        if len(value) < self.minimum_stem_length:
            return None
        return value + self.replacement


@dataclass(frozen=True)
class _TransformState:
    term: str
    conditions: frozenset[str]
    reasons: tuple[str, ...]
    trace: frozenset[tuple[int, str]]
    depth: int


def expand_suffix_transforms(
    value: str,
    rules: tuple[SuffixTransform, ...],
    *,
    max_depth: int = 8,
    max_results: int = 96,
    max_states: int = 256,
) -> tuple[MorphologyCandidate, ...]:
    """Expand a term through a finite reverse-inflection graph.

    Empty conditions represent an unconstrained source form. Once a transform has
    assigned conditions, the next transform must accept at least one of them.
    Intermediate conditions beginning with ``-`` are graph-only states and are not
    returned as dictionary candidates.
    """

    if not value:
        return ()

    results = [MorphologyCandidate(value)]
    queue = deque([_TransformState(value, frozenset(), (), frozenset(), 0)])
    seen_states: set[tuple[str, frozenset[str]]] = {(value, frozenset())}
    seen_candidates: set[tuple[str, frozenset[str]]] = {(value, frozenset())}
    processed_states = 0

    while queue and processed_states < max_states and len(results) < max_results:
        state = queue.popleft()
        processed_states += 1
        if state.depth >= max_depth:
            continue

        for rule_index, rule in enumerate(rules):
            if state.conditions and not state.conditions.intersection(rule.conditions_in):
                continue
            trace_frame = (rule_index, state.term)
            if trace_frame in state.trace:
                continue

            transformed = rule.apply(state.term)
            if transformed is None or transformed == state.term:
                continue

            reasons = rule.reasons + state.reasons
            conditions = rule.conditions_out
            candidate_key = (transformed, conditions)
            if (
                conditions
                and all(not item.startswith("-") for item in conditions)
                and candidate_key not in seen_candidates
            ):
                seen_candidates.add(candidate_key)
                results.append(MorphologyCandidate(transformed, reasons, conditions))
                if len(results) >= max_results:
                    break

            state_key = (transformed, conditions)
            if rule.terminal or state_key in seen_states:
                continue
            seen_states.add(state_key)
            queue.append(
                _TransformState(
                    transformed,
                    conditions,
                    reasons,
                    state.trace | {trace_frame},
                    state.depth + 1,
                )
            )

    return tuple(results)
