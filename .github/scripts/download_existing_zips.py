import os
import subprocess

from slugs import slug_for

repo = os.environ["GH_REPO"]
os.makedirs("release-assets", exist_ok=True)

subprocess.run([
    "curl", "-sL", "-o", "release-assets/images-latest.zip",
    f"https://github.com/{repo}/releases/download/latest/images-latest.zip",
])

masechtot = {}   # masechet_name -> seder_name
with open("changed_files.txt", encoding="utf-8") as fh:
    for line in fh:
        parts = line.strip().split("/")
        if len(parts) >= 3 and parts[1] and parts[2]:
            masechtot[parts[2]] = parts[1]

seders = set(masechtot.values())

print("Masechtot with changes:", sorted(masechtot.keys()))
print("Sedarim with changes:", sorted(seders))

for masechet_name in masechtot:
    slug = slug_for(masechet_name)
    url = f"https://github.com/{repo}/releases/download/latest/masechet-{slug}.zip"
    subprocess.run(["curl", "-sL", "-o", f"release-assets/masechet-{slug}.zip", url])

for seder_name in seders:
    slug = slug_for(seder_name)
    url = f"https://github.com/{repo}/releases/download/latest/{slug}.zip"
    subprocess.run(["curl", "-sL", "-o", f"release-assets/{slug}.zip", url])
