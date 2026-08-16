import os
import subprocess
import zipfile

from slugs import slug_for

os.makedirs("release-assets", exist_ok=True)

groups = {}  # masechet_name -> "seder/masechet"
with open("changed_files.txt", encoding="utf-8") as fh:
    for line in fh:
        parts = line.strip().split("/")
        # parts[0] = "מאגר תמונות mdy", parts[1] = seder, parts[2] = masechet
        if len(parts) >= 3 and parts[1] and parts[2]:
            groups[parts[2]] = f"{parts[1]}/{parts[2]}"

print("Masechtot to update:", list(groups.keys()))


def is_valid_zip(path):
    if not (os.path.isfile(path) and os.path.getsize(path) > 0):
        return False
    r = subprocess.run(["unzip", "-l", path], capture_output=True)
    return r.returncode == 0


def strip_directory_entries(zip_path):
    """Remove any directory-only entries (e.g. 'images/seder/masechet/') that
    zip -u can leave behind from an older, already-dirty downloaded archive.
    -D only stops *new* entries from being added; it does not clean ones
    that were already present in the file we downloaded."""
    tmp_path = zip_path + ".clean.tmp"
    with zipfile.ZipFile(zip_path, "r") as src, \
         zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as dst:
        removed = 0
        for item in src.infolist():
            if item.filename.endswith("/"):
                removed += 1
                continue
            dst.writestr(item, src.read(item.filename))
    os.replace(tmp_path, zip_path)
    if removed:
        print(f"  stripped {removed} directory entrie(s) from {zip_path}")


def update_zip_with(zip_path, img_relpath):
    if is_valid_zip(zip_path):
        subprocess.run(["zip", "-q", "-D", "-u", "-r", zip_path, img_relpath], check=True)
    else:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        subprocess.run(["zip", "-q", "-D", "-r", zip_path, img_relpath], check=True)
    strip_directory_entries(zip_path)


main_zip = "release-assets/images-latest.zip"

for masechet_name, seder_masechet in groups.items():
    # img_path = images/<seder>/<masechet> - used as the target for ALL THREE
    # zips (masechet, seder, main), so only the actually-changed files get
    # touched even inside the bigger seder/main archives.
    img_path = os.path.join("images", seder_masechet)
    if not os.path.isdir(img_path):
        print(f"SKIP (not a dir): {img_path}")
        continue

    seder_name = seder_masechet.split("/", 1)[0]

    masechet_slug = slug_for(masechet_name)
    masechet_zip = f"release-assets/masechet-{masechet_slug}.zip"
    update_zip_with(masechet_zip, img_path)
    print(f"Updated {masechet_zip} (מסכת {masechet_name})")

    seder_slug = slug_for(seder_name)
    seder_zip = f"release-assets/{seder_slug}.zip"
    update_zip_with(seder_zip, img_path)
    print(f"Updated {seder_zip} (סדר {seder_name})")

    update_zip_with(main_zip, img_path)
    print(f"Updated {main_zip} (מסכת {masechet_name})")
