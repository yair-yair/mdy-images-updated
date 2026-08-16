import os
import subprocess

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


for masechet_name, seder_masechet in groups.items():
    img_path = os.path.join("images", seder_masechet)
    if not os.path.isdir(img_path):
        print(f"SKIP (not a dir): {img_path}")
        continue

    masechet_zip = f"release-assets/masechet-{masechet_name}.zip"
    if is_valid_zip(masechet_zip):
        subprocess.run(["zip", "-q", "-u", "-r", masechet_zip, img_path], check=True)
    else:
        if os.path.exists(masechet_zip):
            os.remove(masechet_zip)
        subprocess.run(["zip", "-q", "-r", masechet_zip, img_path], check=True)
    print(f"Updated {masechet_zip}")

    main_zip = "release-assets/images-latest.zip"
    if is_valid_zip(main_zip):
        subprocess.run(["zip", "-q", "-u", "-r", main_zip, img_path], check=True)
    else:
        if os.path.exists(main_zip):
            os.remove(main_zip)
        subprocess.run(["zip", "-q", "-r", main_zip, img_path], check=True)
    print(f"Updated {main_zip} (מסכת {masechet_name})")
