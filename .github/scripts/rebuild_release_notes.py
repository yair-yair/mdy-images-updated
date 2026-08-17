import os

from slugs import slug_for

ROOT = "מאגר תמונות mdy"
IMG_EXT = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff")


def count_images(path):
    total = 0
    for _, _, files in os.walk(path):
        total += sum(1 for f in files if f.lower().endswith(IMG_EXT))
    return total


lines = []

if os.path.isdir(ROOT):
    sedarim = sorted(
        d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))
    )
    for seder_name in sedarim:
        seder_path = os.path.join(ROOT, seder_name)
        seder_count = count_images(seder_path)
        if seder_count > 0:
            lines.append(f"{slug_for(seder_name)}.zip = {seder_name} ({seder_count} images)")

        masechtot = sorted(
            d for d in os.listdir(seder_path) if os.path.isdir(os.path.join(seder_path, d))
        )
        for masechet_name in masechtot:
            masechet_path = os.path.join(seder_path, masechet_name)
            masechet_count = count_images(masechet_path)
            if masechet_count > 0:
                slug = slug_for(masechet_name)
                lines.append(
                    f"masechet-{slug}.zip = {seder_name}/{masechet_name} ({masechet_count} images)"
                )

os.makedirs("dist", exist_ok=True)
with open("dist/mapping.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

body = (
    "קבצים אוטומטיים, מתעדכנים אוטומטית ומיידית בכל תמונה חדשה שנוספת.\n"
    "כל תמונה עוברת קודם דחיסת cwebp (איכות 75) לפני שהיא נכנסת לקבצי ההורדה.\n\n"
    "- images-latest.zip: כל המאגר\n\n"
    "מיפוי בין שם הקובץ באנגלית (שם התיקייה בפועל בעברית):\n"
    "```\n" + "\n".join(lines) + "\n```\n"
)
with open("release_body.md", "w", encoding="utf-8") as fh:
    fh.write(body)

print(f"Rebuilt release notes with {len(lines)} entries")
