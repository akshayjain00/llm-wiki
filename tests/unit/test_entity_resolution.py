"""Unit tests for entity_resolution.py"""
from __future__ import annotations

import pytest

from llm_wiki.entity_resolution import (
    AliasRegistry,
    alias_id,
    normalize,
    slugify,
)


class TestNormalize:
    def test_lowercase(self) -> None:
        assert normalize("Alpha Project") == "alpha project"

    def test_punctuation_stripped(self) -> None:
        # Hyphens are preserved (used for slug matching); ! is stripped → space → collapsed
        assert normalize("Beta-Service!") == "beta-service"
        assert normalize("HCV (Health)") == "hcv health"

    def test_whitespace_collapsed(self) -> None:
        assert normalize("  foo   bar  ") == "foo bar"

    def test_unicode_nfkd(self) -> None:
        result = normalize("Ångström")
        assert "a" in result.lower()

    def test_empty(self) -> None:
        assert normalize("") == ""


class TestSlugify:
    def test_basic(self) -> None:
        assert slugify("Alpha Project") == "alpha-project"

    def test_multiple_spaces(self) -> None:
        assert slugify("foo  bar") == "foo-bar"


class TestAliasRegistry:
    def test_single_match(self) -> None:
        reg = AliasRegistry()
        reg.register("Alpha", "project:alpha", "slug")
        node_id, ambiguous, _ = reg.resolve("Alpha")
        assert node_id == "project:alpha"
        assert not ambiguous

    def test_case_insensitive_resolve(self) -> None:
        reg = AliasRegistry()
        reg.register("Alpha Project", "project:alpha", "title")
        node_id, ambiguous, _ = reg.resolve("alpha project")
        assert node_id == "project:alpha"
        assert not ambiguous

    def test_ambiguous_multiple_entities(self) -> None:
        reg = AliasRegistry()
        reg.register("Atlas", "project:atlas-v1", "slug")
        reg.register("Atlas", "project:atlas-v2", "slug")
        node_id, ambiguous, _ = reg.resolve("Atlas")
        assert node_id is None
        assert ambiguous

    def test_no_match(self) -> None:
        reg = AliasRegistry()
        node_id, ambiguous, _ = reg.resolve("Unknown")
        assert node_id is None
        assert not ambiguous

    def test_deduplicated_all_aliases(self) -> None:
        reg = AliasRegistry()
        reg.register("Alpha", "project:alpha", "slug")
        reg.register("Alpha", "project:alpha", "title")  # same norm+node_id
        all_a = reg.all_aliases()
        assert len(all_a) == 1

    def test_empty_alias_not_registered(self) -> None:
        reg = AliasRegistry()
        reg.register("", "project:alpha", "slug")
        assert reg._map == {}


class TestAliasId:
    def test_deterministic(self) -> None:
        a = alias_id("project:alpha", "Alpha")
        b = alias_id("project:alpha", "Alpha")
        assert a == b

    def test_different_entities_differ(self) -> None:
        a = alias_id("project:alpha", "Alpha")
        b = alias_id("project:beta", "Alpha")
        assert a != b
