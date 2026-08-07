from pathlib import Path
import subprocess
import tempfile
import shutil
import sys
import time


# ==========================
# הגדרות
# ==========================

# שימוש: python compress_webp_cwebp.py ["נתיב/לתיקייה"] [מספר-קבצים-מקסימלי]
# מספר הקבצים המקסימלי מאפשר להריץ בקבוצות (batches) על מאגר גדול
# בלי שהריצה תיקח שעות ברצף - ניתן להריץ את הפקודה שוב ושוב
# והיא תמשיך מאיפה שהפסיקה (הודות לקובץ ההתקדמות).
ROOT_FOLDER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
MAX_FILES = int(sys.argv[2]) if len(sys.argv) > 2 else None

QUALITY = 75        # איכות WebP
METHOD = 6          # דחיסה חזקה ביותר
PASSES = 10         # מספר מעברי ניתוח (rate-distortion) - חיסכון נוסף קטן, בלי פגיעה באיכות
THREADS = True      # שימוש בכל המעבדים

# תמונות גדולות מהמסגרת הזו יוקטנו (תוך שמירה על יחס הרוחב-גובה),
# רק אם הן באמת גדולות ממנה - לעולם לא מגדילים תמונה קטנה יותר.
# 1280x720 זו רזולוציית HD מלאה למסך/thumbnail רגיל, ולא יורגש הבדל בתצוגה רגילה.
MAX_WIDTH = 1280
MAX_HEIGHT = 720

MAKE_BACKUP = False # לא ליצור גיבויים

# קובצי מעקב נפרדים לריצה הזו (עם ההקטנה) - כדי לא לגעת בהיסטוריה
# של הריצה הקודמת (compress_progress.log) וכדי שאפשר יהיה להריץ שוב בלי בעיה
LOG_FILE = Path("compress_errors_resize.log")
PROGRESS_FILE = Path("compress_progress_resize.log")  # קבצים שכבר טופלו (הצלחה/כשלון) - לא ניגע בהם שוב


def get_dimensions(file):
    result = subprocess.run(
        ["webpinfo", str(file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    width = height = None
    for line in result.stdout.decode(errors="replace").splitlines():
        line = line.strip()
        if line.startswith("Width:"):
            width = int(line.split(":")[1].strip())
        elif line.startswith("Height:"):
            height = int(line.split(":")[1].strip())
    return width, height


total_files = 0
changed_files = 0
saved_bytes = 0
failed_files = 0
skipped_done = 0


def log_error(file, message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{file} :: {message}\n")


def mark_done(file):
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{file}\n")


def load_done():
    if not PROGRESS_FILE.exists():
        return set()
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return set(line.rstrip("\n") for line in f)


def compress_image(file):

    global changed_files, saved_bytes, failed_files

    temp_file = None

    try:

        old_size = file.stat().st_size

        # קובץ זמני באותה תיקייה של הקובץ המקורי (לא ב-/tmp) -
        # נמנע מבעיות דיסק/כונן שונה בריצות ארוכות על מאגר גדול
        temp_file = Path(
            tempfile.mktemp(
                suffix=".webp",
                dir=str(file.parent),
            )
        )

        command = [
            "cwebp",
            "-q",
            str(QUALITY),
            "-m",
            str(METHOD),
            "-pass",
            str(PASSES),
            "-af",
            "-sharp_yuv",
            "-quiet",
        ]

        if THREADS:
            command.append("-mt")

        # הקטנה רק אם התמונה גדולה יותר מהמסגרת המותרת - לעולם לא מגדילים
        width, height = get_dimensions(file)
        if width and height and (width > MAX_WIDTH or height > MAX_HEIGHT):
            scale = min(MAX_WIDTH / width, MAX_HEIGHT / height)
            new_w = max(1, round(width * scale))
            new_h = max(1, round(height * scale))
            command += ["-resize", str(new_w), str(new_h)]

        command += [
            str(file),
            "-o",
            str(temp_file)
        ]

        # ננסה עד פעמיים - לפעמים cwebp "מצליח" (קוד יציאה 0) אבל לא כותב
        # בפועל את קובץ הפלט (למשל בעיית דיסק זמנית). ניסיון חוזר פותר את זה.
        result = None
        for attempt in range(1, 3):
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            if result.returncode != 0:
                break

            if temp_file.exists():
                break

            if attempt < 2:
                time.sleep(0.5)

        if result.returncode != 0:
            failed_files += 1
            print("שגיאה:", file, flush=True)
            print(result.stderr.decode(errors="replace"), flush=True)
            log_error(file, result.stderr.decode(errors="replace"))
            return

        if not temp_file.exists():
            failed_files += 1
            print("שגיאה:", file, "cwebp דיווח הצלחה אך קובץ הפלט לא נוצר", flush=True)
            log_error(
                file,
                "cwebp reported success (exit code 0) but the output file "
                "was not created, even after a retry",
            )
            return

        new_size = temp_file.stat().st_size

        # מחליף רק אם החדש קטן יותר
        if new_size < old_size:

            if MAKE_BACKUP:
                backup = file.with_suffix(".backup.webp")
                shutil.copy2(file, backup)

            shutil.move(str(temp_file), str(file))

            saved = old_size - new_size
            saved_bytes += saved
            changed_files += 1

            print(
                f"✓ {file} "
                f"{old_size/1024:.1f}KB → "
                f"{new_size/1024:.1f}KB "
                f"חיסכון {saved/1024:.1f}KB",
                flush=True,
            )

        else:
            temp_file.unlink()

    except Exception as e:
        failed_files += 1
        print("בעיה:", file, e, flush=True)
        log_error(file, str(e))

        try:
            if temp_file is not None and temp_file.exists():
                temp_file.unlink()
        except Exception:
            pass


# ==========================

t0 = time.time()
done_set = load_done()

print(f"מתחיל סריקה בתיקייה: {ROOT_FOLDER}", flush=True)
print(f"({len(done_set)} קבצים כבר טופלו בעבר ויידלגו)", flush=True)
if MAX_FILES:
    print(f"מגבלת קבצים לריצה הזו: {MAX_FILES}\n", flush=True)

processed_this_run = 0

for file in sorted(ROOT_FOLDER.rglob("*.webp")):

    if ".git" in file.parts:
        continue

    key = str(file)

    if key in done_set:
        skipped_done += 1
        continue

    # אם התמונה כבר בגודל תקין - אין טעם לדחוס אותה שוב (דחיסה כפולה
    # ללא צורך רק מוסיפה אובדן איכות בלי לחסוך כמעט כלום). מסמנים כטופל ומדלגים.
    width, height = get_dimensions(file)
    if width and height and width <= MAX_WIDTH and height <= MAX_HEIGHT:
        skipped_done += 1
        mark_done(key)
        continue

    if MAX_FILES is not None and processed_this_run >= MAX_FILES:
        print(f"\nהגעתי למגבלת {MAX_FILES} קבצים לריצה הזו - עוצר כאן.", flush=True)
        break

    total_files += 1
    processed_this_run += 1
    compress_image(file)
    mark_done(key)


print("\n======================")
print("הסתיים (ריצה זו)")
print("======================")

print("קבצים שעובדו בריצה הזו:", total_files)
print("קבצים שדולגו (כבר טופלו קודם):", skipped_done)
print("תמונות שהוקטנו:", changed_files)
print("תמונות שנכשלו:", failed_files)
print(f"חיסכון בריצה זו: {saved_bytes/1024/1024:.2f} MB")
print(f"זמן ריצה: {time.time()-t0:.1f} שניות")

if failed_files:
    print(f"\nפרטי הכשלונות נשמרו בקובץ: {LOG_FILE}")

remaining = 0
for file in ROOT_FOLDER.rglob("*.webp"):
    if ".git" in file.parts:
        continue
    if str(file) not in load_done():
        remaining += 1

print(f"\nנשארו {remaining} קבצים שטרם עובדו בתיקייה הזו. הרץ שוב את הסקריפט כדי להמשיך.")
