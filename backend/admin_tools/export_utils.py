"""
Shared helpers for admin CSV export tasks.
"""
import re

from questionnaires.scoring import (
    PERMA_ITEM_CODES,
    perma_score_column_names,
    perma_score_row_values,
    ensure_scores,
)


def build_psych_item_headers_and_columns(psy_questions, milestone_suffix):
    """
    Build item-level CSV headers and question-id column mapping for psychometric exports.
    Returns (headers, question_ids).
    """
    headers = []
    question_ids = []
    tag_counters = {}

    for question in psy_questions:
        match = re.match(r"^\[([^\]]+)\]", question.content)
        tag = re.sub(r"[^a-zA-Z0-9]", "", match.group(1)).upper() if match else "PSYCH"
        tag_counters[tag] = tag_counters.get(tag, 0) + 1
        relative_order = tag_counters[tag]

        if tag == "PERMA":
            code = PERMA_ITEM_CODES[relative_order - 1]
            header_name = f"PERMA_{code.upper()}_{milestone_suffix}"
        else:
            header_name = f"{tag}_Q{relative_order}_{milestone_suffix}"

        headers.append(header_name)
        question_ids.append(question.id)

    return headers, question_ids


def append_psych_item_values(row, resp_map, question_ids):
    """Append raw item response labels to a CSV row."""
    for question_id in question_ids:
        answer = resp_map.get(question_id)
        if answer:
            value = answer.selected_option.label if answer.selected_option else (answer.text_value or "")
            row.append(value.replace("\n", " "))
        else:
            row.append("")


def append_perma_score_values(row, response_set):
    """Append computed PERMA subscale scores for a milestone response set."""
    if response_set:
        scores = ensure_scores(response_set)
        row.extend(perma_score_row_values(scores))
    else:
        row.extend(perma_score_row_values({}))


def extend_headers_with_perma_scores(headers, milestone_suffix):
    """Add PERMA subscale score column headers after item columns."""
    headers.extend(perma_score_column_names(milestone_suffix))
