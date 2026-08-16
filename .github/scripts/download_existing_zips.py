import os
import subprocess

repo = os.environ["GH_REPO"]
os.makedirs("release-assets", exist_ok=True)

subprocess.run([
    "curl", "-sL", "-o", "release-assets/images-latest.zip",
    f"https://github.com/{repo}/releases/download/latest/images-latest.zip",
])

masechtot = set()
with open("changed_files.txt", encoding="utf-8") as fh:
    for line in fh:
        parts = line.strip().split("/")
        if len(parts) >= 3 and parts[2]:
            masechtot.add(parts[2])

print("Masechtot with changes:", sorted(masechtot))

for m in sorted(masechtot):
    url = f"https://github.com/{repo}/releases/download/latest/masechet-{m}.zip"
    subprocess.run(["curl", "-sL", "-o", f"release-assets/masechet-{m}.zip", url])
