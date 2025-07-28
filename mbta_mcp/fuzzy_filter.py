"""Fuzzy filtering utilities for client-side data filtering."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def fuzzy_match(query: str, text: str) -> bool:
    """Simple fuzzy matching based on substring and similarity.

    Args:
        query: Search query string
        text: Text to match against

    Returns:
        True if text matches query fuzzy criteria
    """
    if not query or not text:
        return False

    query_lower = query.lower().strip()
    text_lower = text.lower().strip()

    # Exact substring match gets highest priority
    if query_lower in text_lower:
        return True

    # Check if all query words appear in text
    query_words = query_lower.split()
    text_words = text_lower.split()

    # All query words must have at least one match in text
    for query_word in query_words:
        found_match = False
        for text_word in text_words:
            if query_word in text_word or text_word in query_word:
                found_match = True
                break
        if not found_match:
            return False

    return True


def filter_data_fuzzy(
    data: list[dict[str, Any]],
    query: str,
    search_fields: list[str],
    max_results: int = 50,
) -> list[dict[str, Any]]:
    """Filter a list of data objects using fuzzy matching.

    Args:
        data: List of data objects to filter
        query: Search query string
        search_fields: List of field paths to search in each object (e.g., ["attributes.name", "id"])
        max_results: Maximum number of results to return

    Returns:
        Filtered list of data objects
    """
    if not query.strip():
        return data[:max_results]

    filtered = []

    for item in data:
        # Check each search field for a match
        for field_path in search_fields:
            field_value = _get_nested_field(item, field_path)
            if field_value and fuzzy_match(query, str(field_value)):
                filtered.append(item)
                break  # Found a match, move to next item

        if len(filtered) >= max_results:
            break

    return filtered


def _get_nested_field(obj: dict[str, Any], field_path: str) -> Any:
    """Get a nested field value from an object using dot notation.

    Args:
        obj: Object to get field from
        field_path: Dot-separated field path (e.g., "attributes.name")

    Returns:
        Field value or None if not found
    """
    try:
        current = obj
        for field in field_path.split("."):
            if isinstance(current, dict) and field in current:
                current = current[field]
            else:
                return None
    except (KeyError, TypeError):
        return None
    else:
        return current
