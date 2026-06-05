"""
Psychometric scoring for the longitudinal battery.
PERMA Profiler subscales use item means (0-10); N and Lon are not reverse-scored.
"""
from .models import Response

PERMA_ITEM_CODES = [
    "A1", "E1", "P1", "N1", "A2", "H1", "M1", "R1", "M2", "E2", "Lon", "H2",
    "P2", "N2", "A3", "N3", "E3", "H3", "R2", "M3", "R3", "P3", "Hap",
]

# (scores JSON key, human-readable CSV column prefix)
PERMA_EXPORT_SCORES = [
    ("PERMA_P", "PERMA_PositiveEmotion"),
    ("PERMA_E", "PERMA_Engagement"),
    ("PERMA_R", "PERMA_Relationships"),
    ("PERMA_M", "PERMA_Meaning"),
    ("PERMA_A", "PERMA_Accomplishment"),
    ("PERMA_N", "PERMA_NegativeEmotion"),
    ("PERMA_H", "PERMA_Health"),
    ("PERMA_LON", "PERMA_Loneliness"),
    ("PERMA_OVERALL", "PERMA_Overall"),
]


def perma_score_column_names(milestone_suffix):
    """CSV header names for PERMA subscale scores at a given milestone."""
    return [f"{label}_{milestone_suffix}" for _, label in PERMA_EXPORT_SCORES]


def perma_score_row_values(scores):
    """Ordered PERMA score values for a CSV row; empty string if missing."""
    if not scores:
        return [""] * len(PERMA_EXPORT_SCORES)
    return [scores.get(key, "") for key, _ in PERMA_EXPORT_SCORES]


def calculate_scores(val_map):
    """
    Compute all battery scores from a question-order -> numeric_value map.
    Returns a dict suitable for ResponseSet.scores.
    """
    if not val_map:
        return {}

    scores = {}

    perma_p_orders = [3, 13, 22]
    perma_e_orders = [2, 10, 17]
    perma_r_orders = [8, 19, 21]
    perma_m_orders = [7, 9, 20]
    perma_a_orders = [1, 5, 15]
    perma_n_orders = [4, 14, 16]
    perma_h_orders = [6, 12, 18]
    perma_lon_order = 11
    perma_overall_orders = [3, 13, 22, 2, 10, 17, 8, 19, 21, 7, 9, 20, 1, 5, 15, 23]

    def get_mean(orders):
        vals = [val_map[o] for o in orders if o in val_map]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    if any(o in val_map for o in range(1, 24)):
        scores["PERMA_P"] = get_mean(perma_p_orders)
        scores["PERMA_E"] = get_mean(perma_e_orders)
        scores["PERMA_R"] = get_mean(perma_r_orders)
        scores["PERMA_M"] = get_mean(perma_m_orders)
        scores["PERMA_A"] = get_mean(perma_a_orders)
        scores["PERMA_N"] = get_mean(perma_n_orders)
        scores["PERMA_H"] = get_mean(perma_h_orders)
        scores["PERMA_LON"] = float(val_map.get(perma_lon_order, 0.0))
        scores["PERMA_OVERALL"] = get_mean(perma_overall_orders)

    phq_orders = list(range(24, 33))
    if any(o in val_map for o in phq_orders):
        scores["PHQ9_TOTAL"] = sum(val_map[o] for o in phq_orders if o in val_map)

    gad_orders = list(range(33, 40))
    if any(o in val_map for o in gad_orders):
        scores["GAD7_TOTAL"] = sum(val_map[o] for o in gad_orders if o in val_map)

    panas_pa_orders = [42, 43, 46, 48]
    panas_na_orders = [40, 41, 44, 45, 47]
    if any(o in val_map for o in range(40, 49)):
        scores["PANAS_PA"] = sum(val_map[o] for o in panas_pa_orders if o in val_map)
        scores["PANAS_NA"] = sum(val_map[o] for o in panas_na_orders if o in val_map)

    grat_gto_orders = list(range(49, 63))
    grat_gta_orders = list(range(63, 75))
    grat_all_orders = list(range(49, 75))
    if any(o in val_map for o in grat_all_orders):
        scores["GRAT_GTO"] = sum(val_map[o] for o in grat_gto_orders if o in val_map)
        scores["GRAT_GTA"] = sum(val_map[o] for o in grat_gta_orders if o in val_map)
        scores["GRAT_TOTAL"] = sum(val_map[o] for o in grat_all_orders if o in val_map)

    if any(o in val_map for o in range(75, 80)):
        sidas_item1 = val_map.get(75, 0)
        if sidas_item1 == 0:
            scores["SIDAS_TOTAL"] = 0
        else:
            sidas_item2 = val_map.get(76, 0)
            sidas_item3 = val_map.get(77, 0)
            sidas_item4 = val_map.get(78, 0)
            sidas_item5 = val_map.get(79, 0)
            scores["SIDAS_TOTAL"] = sidas_item1 + (10 - sidas_item2) + sidas_item3 + sidas_item4 + sidas_item5

    return scores


def calculate_and_save_scores(response_set):
    """Calculate scores from responses and persist on the ResponseSet."""
    responses = Response.objects.filter(response_set=response_set).select_related(
        "question", "selected_option"
    )

    val_map = {}
    for response in responses:
        if response.question and response.selected_option is not None:
            val_map[response.question.order] = response.selected_option.numeric_value

    scores = calculate_scores(val_map)
    if not scores:
        return

    response_set.scores = scores
    response_set.save(update_fields=["scores"])


def ensure_scores(response_set):
    """Return scores for a response set, computing and saving if absent."""
    if not response_set.scores:
        calculate_and_save_scores(response_set)
        response_set.refresh_from_db()
    return response_set.scores or {}
