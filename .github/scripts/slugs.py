import hashlib

SLUG = {
    "סדר זרעים": "seder-1-zeraim",
    "סדר מועד": "seder-2-moed",
    "סדר נשים": "seder-3-nashim",
    "סדר נזיקין": "seder-4-nezikin",
    "סדר קדשים": "seder-5-kodashim",
    "סדר טהרות": "seder-6-taharot",

    "ברכות": "berachot", "פאה": "peah", "דמאי": "demai", "כלאים": "kilayim",
    "שביעית": "sheviit", "תרומות": "terumot", "מעשרות": "maasrot",
    "מעשר שני": "maaser-sheni", "חלה": "challah", "ערלה": "orlah", "ביכורים": "bikkurim",

    "שבת": "shabbat", "עירובין": "eruvin", "פסחים": "pesachim", "שקלים": "shekalim",
    "יומא": "yoma", "סוכה": "sukkah", "ביצה": "beitzah", "ראש השנה": "rosh-hashanah",
    "תענית": "taanit", "מגילה": "megillah", "מועד קטן": "moed-katan", "חגיגה": "chagigah",

    "יבמות": "yevamot", "כתובות": "ketubot", "נדרים": "nedarim", "נזיר": "nazir",
    "סוטה": "sotah", "גיטין": "gittin", "קידושין": "kiddushin",

    "בבא קמא": "bava-kamma", "בבא מציעא": "bava-metzia", "בבא בתרא": "bava-batra",
    "סנהדרין": "sanhedrin", "מכות": "makkot", "שבועות": "shevuot", "עדיות": "eduyot",
    "עבודה זרה": "avodah-zarah", "אבות": "avot", "הוריות": "horayot",

    "זבחים": "zevachim", "מנחות": "menachot", "חולין": "chullin", "בכורות": "bechorot",
    "ערכין": "arachin", "תמורה": "temurah", "כריתות": "keritot", "מעילה": "meilah",
    "תמיד": "tamid", "מידות": "middot", "קינים": "kinnim",

    "כלים": "keilim", "אהלות": "oholot", "נגעים": "negaim", "פרה": "parah",
    "טהרות": "taharot-masechet", "מקואות": "mikvaot", "נדה": "niddah",
    "מכשירין": "machshirin", "זבים": "zavim", "טבול יום": "tevul-yom",
    "ידיים": "yadayim", "עוקצין": "uktzin",
}


def slug_for(hebrew_name: str) -> str:
    """Same fallback rule as release-images.yml: misc-<md5 prefix> for unknown names."""
    if hebrew_name in SLUG:
        return SLUG[hebrew_name]
    return "misc-" + hashlib.md5(hebrew_name.encode("utf-8")).hexdigest()[:8]
