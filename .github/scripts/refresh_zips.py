"""
מרענן את קבצי ה-zip של המסכתות שהושפעו (אחרי מחיקה / שינוי מספור / הוספה).

לכל zip שמושפע (מסכת, סדר, וה-zip הראשי):
  1. מסיר ממנו את כל הרשומות של התיקיות שהושפעו (images/<סדר>/<מסכת>/...)
  2. מוסיף מחדש את כל הקבצים של אותן תיקיות כפי שהם עכשיו בריפו
מסכתות אחרות בתוך ה-zip של הסדר/הראשי לא נוגעים בהן.

קלט: changed_files.txt (נתיבים יחסיים לשורש הריפו) + zip-ים קיימים בתיקיית release-assets
פלט: אותם zip-ים, מעודכנים, באותה תיקייה.
DRY_RUN=1 - רק דוח השוואה, בלי לשנות כלום.
"""
import os
import sys
import zipfile

from slugs import slug_for

ROOT = "מאגר תמונות mdy"
OUT = "release-assets"
IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff")
DRY = os.environ.get("DRY_RUN") == "1"

affected = {}  # seder -> set(masechet)
with open("changed_files.txt", encoding="utf-8") as fh:
    for line in fh:
        parts = line.strip().split("/")
        # [שורש, סדר, מסכת, קובץ]
        if len(parts) >= 4 and parts[0] == ROOT and parts[1] and parts[2]:
            affected.setdefault(parts[1], set()).add(parts[2])

if not affected:
    print("אין מסכתות מושפעות - אין מה לעשות")
    sys.exit(0)

print("מסכתות מושפעות:", {s: sorted(m) for s, m in affected.items()})


REPORT = []


def emit_notice(msg):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        esc = msg.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::notice title=zip-report::{esc}")


def disk_files(seder, masechet):
    base = os.path.join(ROOT, seder, masechet)
    res = {}
    for dirpath, _, files in os.walk(base):
        for f in files:
            if f.lower().endswith(IMG_EXT):
                p = os.path.join(dirpath, f)
                rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
                res["images/" + rel] = p
    return res


def is_valid(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0 and zipfile.is_zipfile(path)


def rebuild(zip_path, folders, allow_create):
    prefixes = tuple(f"images/{s}/{m}/" for s, m in folders)
    wanted = {}
    for s, m in folders:
        wanted.update(disk_files(s, m))

    ok = is_valid(zip_path)
    if not ok and not allow_create:
        sys.exit(f"שגיאה: {zip_path} חסר או פגום. לא בונים zip חלקי. עוצרים.")

    old_names = set()
    if ok:
        with zipfile.ZipFile(zip_path) as z:
            old_names = {n for n in z.namelist() if n.startswith(prefixes) and not n.endswith("/")}

    extra = sorted(old_names - set(wanted))      # ב-zip אבל לא בריפו (יוסרו)
    missing = sorted(set(wanted) - old_names)    # בריפו אבל לא ב-zip (יתווספו)
    print(f"{os.path.basename(zip_path)}: ב-zip {len(old_names)} | בריפו {len(wanted)} | "
          f"יוסרו {len(extra)} | יתווספו {len(missing)}")
    for n in extra[:5]:
        print("   יוסר:", n)
    for n in missing[:5]:
        print("   יתווסף:", n)
    # דוח גם כהערה (annotation) של ההרצה, כדי שכלי המחיקה יוכל לקרוא אותו
    note = (f"{os.path.basename(zip_path)}: ב-zip {len(old_names)} | בריפו {len(wanted)} | "
            f"יוסרו {len(extra)} | יתווספו {len(missing)}")
    for n in extra[:5]:
        note += "\n   יוסר: " + n
    for n in missing[:5]:
        note += "\n   יתווסף: " + n
    REPORT.append(note)

    if DRY:
        return

    if not wanted and not ok:
        print("   התיקייה ריקה - לא יוצרים zip")
        return

    tmp = zip_path + ".new"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as dst:
        if ok:
            with zipfile.ZipFile(zip_path) as src:
                for item in src.infolist():
                    if item.filename.endswith("/") or item.filename.startswith(prefixes):
                        continue
                    dst.writestr(item, src.read(item.filename))
        for arc in sorted(wanted):
            dst.write(wanted[arc], arc)

    with zipfile.ZipFile(tmp) as z:
        if z.testzip() is not None:
            sys.exit(f"שגיאה: {tmp} פגום")
        got = {n for n in z.namelist() if n.startswith(prefixes) and not n.endswith("/")}
    if got != set(wanted):
        sys.exit(f"שגיאה: התוכן של {tmp} לא תואם לריפו")
    os.replace(tmp, zip_path)


os.makedirs(OUT, exist_ok=True)
all_folders = [(s, m) for s, ms in affected.items() for m in sorted(ms)]

rebuild(f"{OUT}/images-latest.zip", all_folders, allow_create=False)

for seder, ms in affected.items():
    folders = [(seder, m) for m in sorted(ms)]
    rebuild(f"{OUT}/{slug_for(seder)}.zip", folders, allow_create=False)
    for m in sorted(ms):
        rebuild(f"{OUT}/masechet-{slug_for(m)}.zip", [(seder, m)], allow_create=True)

emit_notice("\n".join(REPORT))
print("סיום" + (" (בדיקה בלבד)" if DRY else ""))
