"""Tests for RAG search utilities and text processing."""

import pytest

from app.services.rag import reciprocal_rank_fusion
from app.utils.text_processing import chunk_text


class TestChunking:
    """Tests for text chunking."""

    def test_empty_text(self):
        """Empty text should return no chunks."""
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        """Text shorter than chunk_size should return a single chunk."""
        text = "This is a short document."
        chunks = chunk_text(text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_multiple_chunks(self):
        """Long text should be split into overlapping chunks."""
        words = ["word"] * 300
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=10)
        assert len(chunks) > 1

    def test_overlap_present(self):
        """Consecutive chunks should share overlapping content."""
        # Create text where each word is unique for easy verification
        words = [f"word{i}" for i in range(200)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=50, chunk_overlap=10)

        # Words at the end of chunk 0 should appear at the start of chunk 1
        chunk0_words = chunks[0].split()
        chunk1_words = chunks[1].split()

        # Last 10 words of chunk 0 should be the first 10 words of chunk 1
        assert chunk0_words[-10:] == chunk1_words[:10]

    def test_custom_chunk_size(self):
        """Custom chunk size should be respected."""
        text = " ".join(["word"] * 100)
        chunks = chunk_text(text, chunk_size=25, chunk_overlap=5)
        # Each chunk should have at most 25 words
        for chunk in chunks:
            assert len(chunk.split()) <= 25


class TestReciprocalRankFusion:
    """Tests for reciprocal rank fusion."""

    def test_single_list(self):
        """Single list should maintain order."""
        result = reciprocal_rank_fusion([["a", "b", "c"]])
        assert result == ["a", "b", "c"]

    def test_two_lists_agreement(self):
        """Item ranked high in both lists should be first."""
        result = reciprocal_rank_fusion([["a", "b", "c"], ["a", "c", "b"]])
        assert result[0] == "a"

    def test_two_lists_boosting(self):
        """Item appearing in both lists gets boosted over single-list items."""
        result = reciprocal_rank_fusion([["a", "b", "c"], ["b", "d", "e"]])
        # 'b' appears in both, should rank high
        assert "b" in result[:2]

    def test_empty_lists(self):
        """Empty input should return empty result."""
        assert reciprocal_rank_fusion([]) == []
        assert reciprocal_rank_fusion([[]]) == []

    def test_no_overlap(self):
        """Lists with no common items should return all items."""
        result = reciprocal_rank_fusion([["a", "b"], ["c", "d"]])
        assert set(result) == {"a", "b", "c", "d"}
