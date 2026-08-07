from pathlib import Path
import subprocess
import tempfile
import shutil


# ==========================
# הגדרות
# ==========================

# עובד על כל המאגר ב-GitHub
ROOT_FOLDER = Path(".")


QUALITY = 75        # איכות WebP
METHOD = 6          # דחיסה חזקה ביותר
THREADS = True      # שימוש בכל המעבדים

MAKE_BACKUP = False # לא ליצור גיבויים


# ==========================

total_files = 0
changed_files = 0
saved_bytes = 0


def compress_image(file):

    global changed_files, saved_bytes

    old_size = file.stat().st_size


    temp_file = Path(
        tempfile.mktemp(
            suffix=".webp"
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


    try:

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )


        if result.returncode != 0:

            print("שגיאה:", file)
            print(result.stderr.decode())
            return



        new_size = temp_file.stat().st_size



        # מחליף רק אם החדש קטן יותר
        if new_size < old_size:


            if MAKE_BACKUP:

                backup = file.with_suffix(".backup.webp")

                shutil.copy2(
                    file,
                    backup
                )


            shutil.move(
                str(temp_file),
                str(file)
            )


            saved = old_size - new_size

            saved_bytes += saved
            changed_files += 1


            print(
                f"✓ {file} "
                f"{old_size/1024:.1f}KB → "
                f"{new_size/1024:.1f}KB "
                f"חיסכון {saved/1024:.1f}KB"
            )


        else:

            temp_file.unlink()



    except Exception as e:


        print(
            "בעיה:",
            file,
            e
        )


        if temp_file.exists():

            temp_file.unlink()



# ==========================


print("מתחיל סריקה...\n")


for file in ROOT_FOLDER.rglob("*.webp"):


    # לא לגעת בקבצי GitHub
    if ".git" in file.parts:
        continue


    total_files += 1

    compress_image(file)



print("\n======================")
print("הסתיים")
print("======================")


print(
    "סה״כ תמונות:",
    total_files
)


print(
    "תמונות שהוקטנו:",
    changed_files
)


print(
    f"חיסכון כולל: {saved_bytes/1024/1024:.2f} MB"
)
