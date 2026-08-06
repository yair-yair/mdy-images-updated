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
THREADS = True      # שימוש בכל המעבדים

MAKE_BACKUP = False # לא ליצור גיבויים

LOG_FILE = Path("compress_errors.log")
PROGRESS_FILE = Path("compress_progress.log")  # קבצים שכבר טופלו (הצלחה/כשלון) - לא ניגע בהם שוב


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
            "-af",
            "-sharp_yuv",
            "-quiet",
        ]

        if THREADS:
            command.append("-mt")

        command += [
            str(file),
            "-o",
            str(temp_file)
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if result.returncode != 0:
            failed_files += 1
            print("שגיאה:", file, flush=True)
            print(result.stderr.decode(errors="replace"), flush=True)
            log_error(file, result.stderr.decode(errors="replace"))
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
