import pandas as pd
from loopresources.drillhole.resample import merge_interval_tables
from loopresources.drillhole import DhConfig


def test_merge_interval_tables_basic():
    # Table 1: finer lithology intervals
    t1 = pd.DataFrame(
        {
            DhConfig.holeid: ["DH001", "DH001", "DH001"],
            DhConfig.sample_from: [0.0, 10.0, 20.0],
            DhConfig.sample_to: [10.0, 20.0, 30.0],
            "LITHO": ["A", "B", "C"],
        }
    )

    # Table 2: a single interval that spans part of table1
    t2 = pd.DataFrame(
        {
            DhConfig.holeid: ["DH001"],
            DhConfig.sample_from: [5.0],
            DhConfig.sample_to: [25.0],
            "UNIT": ["X"],
        }
    )

    merged = merge_interval_tables([t1, t2])

    # Expect boundaries: 0,5,10,20,25,30 -> five atomic intervals
    assert len(merged) == 5
    assert list(merged[DhConfig.sample_from]) == [0.0, 5.0, 10.0, 20.0, 25.0]
    assert list(merged[DhConfig.sample_to]) == [5.0, 10.0, 20.0, 25.0, 30.0]

    # LITHO should follow t1, UNIT should be present only where t2 covers
    assert list(merged["LITHO"]) == ["A", "A", "B", "C", "C"]
    # UNIT has NaN where not covered by t2
    unit_list = [v if pd.notna(v) else None for v in merged["UNIT"]]
    assert unit_list == [None, "X", "X", "X", None]


def test_merge_interval_tables_duplicate_columns_renamed():
    # Two tables that both contain a column named 'LITHO'. The second should be
    # renamed to 'LITHO_2' in the result to avoid collision.
    t1 = pd.DataFrame(
        {
            DhConfig.holeid: ["DH002", "DH002"],
            DhConfig.sample_from: [0.0, 10.0],
            DhConfig.sample_to: [10.0, 20.0],
            "LITHO": ["AA", "BB"],
        }
    )

    t2 = pd.DataFrame(
        {
            DhConfig.holeid: ["DH002"],
            DhConfig.sample_from: [0.0],
            DhConfig.sample_to: [20.0],
            "LITHO": ["XX"],
        }
    )

    merged = merge_interval_tables([t1, t2])

    # Two atomic intervals: 0-10 and 10-20
    assert len(merged) == 2
    assert list(merged[DhConfig.sample_from]) == [0.0, 10.0]
    assert list(merged[DhConfig.sample_to]) == [10.0, 20.0]

    # Original LITHO from t1 should be present
    assert list(merged["LITHO"]) == ["AA", "BB"]
    # The second table's LITHO should have been renamed (e.g. LITHO_2)
    renamed_col = None
    for c in merged.columns:
        if c.startswith("LITHO_"):
            renamed_col = c
            break
    assert renamed_col is not None
    assert list(merged[renamed_col]) == ["XX", "XX"]
