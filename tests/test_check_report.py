from analysis import check_report as cr


def test_numerals_are_found_as_whole_numbers():
    assert cr.numerals("blocked 25/25, from 0.0 to 13.3 %, of 3,749; see `4bad83a`.") == \
        ["25", "25", "0.0", "13.3", "3749"]


def test_a_numeral_printed_in_no_source_is_reported_with_its_line():
    report = "Line one says 114 of 419.\nLine two says 115 and 41.\n"
    sources = "| once | 114 | 114 |\n| all | 419 | 193 |\n"
    assert cr.missing(report, sources) == [(2, "115"), (2, "41")]


def test_part_of_a_longer_number_is_not_a_match():
    assert cr.missing("7.1 and 13\n", "0.0 to 7.13 and 113\n") == [(1, "7.1"), (1, "13")]
