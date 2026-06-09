from strings import STRINGS


def test_both_languages_present():
    assert "en" in STRINGS
    assert "ru" in STRINGS


def test_same_keys_in_both_languages():
    assert set(STRINGS["en"].keys()) == set(STRINGS["ru"].keys())


def test_no_empty_strings():
    for lang, strings in STRINGS.items():
        for key, value in strings.items():
            assert value.strip(), f"Пустая строка: [{lang}]['{key}']"


def test_format_strings_consistent():
    for key in STRINGS["en"]:
        en_has_fmt = "{}" in STRINGS["en"][key]
        ru_has_fmt = "{}" in STRINGS["ru"][key]
        assert en_has_fmt == ru_has_fmt, (
            f"Несоответствие {{}} в ключе '{key}': "
            f"en={STRINGS['en'][key]!r}, ru={STRINGS['ru'][key]!r}"
        )
