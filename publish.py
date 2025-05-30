# Generate by AI form sh
import subprocess
import os
import re
from datetime import datetime

print("----------------------------------------")

# =========== Path Config ===========
BASE_DIR = "/home/Timberborn"
GIT_DIR = os.path.join(BASE_DIR, "git")
STEAMCMDDIR = os.path.join(BASE_DIR, "steam")
MOD_INFO_DIR = os.path.join(BASE_DIR, "mod_info")
RELEASE_DIR = os.path.join(BASE_DIR, "release")
CONTEXT_DIR = os.path.join(GIT_DIR, "mod")
MANIFEST_FILE = os.path.join(MOD_INFO_DIR, "manifest.json")
VERSIONS_FILE = os.path.join(GIT_DIR, "versions.txt")

# =========== Mod Config ===========
APPID = "1062090"
PUBLISHEDFILEID = "3346918947"

# =========== GitHub Config ===========
REPO_OWNER = "wuyilingwei"
REPO_NAME = "Timberborn_Mods_Universal_Translate"

# =========== Command Config ===========
FORCE_UPDATE = False
OVERWRITE = False
PUSH_STEAM = True
PUSH_GITHUB = True

# =========== Command Line Args ===========
for arg in sys.argv:
    if arg == "-force":
        FORCE_UPDATE = True
    elif arg == "-overwrite":
        OVERWRITE = True
    elif arg == "-no_steam":
        PUSH_STEAM = False
    elif arg == "-no_github":
        PUSH_GITHUB = False

# =========== Main ===========
print("Run time:", datetime.now())

# =========== Fetch Updates ===========
os.chdir(GIT_DIR)

print("Fetching origin updates...")
subprocess.run(["git", "fetch", "origin", "main"])

LOCAL = subprocess.check_output(["git", "rev-parse", "main"]).decode().strip()
REMOTE = subprocess.check_output(["git", "rev-parse", "origin/main"]).decode().strip()

print("Local commit:", LOCAL)
print("Remote commit:", REMOTE)

# =========== Check Updates ===========
if LOCAL != REMOTE or FORCE_UPDATE:
    if LOCAL != REMOTE:
        print("Detected updates, pulling...")
    else:
        print("Forced update, pulling...")

    subprocess.run(["git", "pull", "origin", "main"])

    os.makedirs(MOD_INFO_DIR)

    # =========== Update Version ===========
    if os.path.isfile(MANIFEST_FILE):
        if OVERWRITE:
            print("enabled -overwrite, skip version update.")
            new_version = re.search(r'"Version":\s*"2\.0\.\d+', open(MANIFEST_FILE).read()).group()
        else:
            current_version = re.search(r'"Version":\s*"2\.0\.\d+', open(MANIFEST_FILE).read()).group()
            if not current_version:
                print("Error: Can't find version in manifest.json!")
            else:
                print("Now version:", current_version)
                last_digit = int(current_version.split(".")[-1])
                version_head = ".".join(current_version.split(".")[:2])
                new_last_digit = last_digit + 1
                new_version = f"{version_head}.{new_last_digit}"
                print("Version updated to:", new_version)
                with open(MANIFEST_FILE, "r+") as file:
                    file_data = file.read()
                    file.seek(0)
                    file.write(re.sub(re.escape(current_version), new_version, file_data))

    else:
        print("No manifest.json found, skip version update.")

    if not os.path.getsize(VERSIONS_FILE):
        print("Error: versions.txt is empty or not exists!")
        exit(1)

    # =========== Create Release ===========
    with open(VERSIONS_FILE, "r") as file:
        VERSIONS = file.read().strip().split(",")

    print("All game versions:", VERSIONS)

    shutil.rmtree(RELEASE_DIR, ignore_errors=True)
    os.makedirs(RELEASE_DIR)

    shutil.copytree(os.path.join(CONTEXT_DIR, "*"), RELEASE_DIR)
    shutil.copyfile(os.path.join(MOD_INFO_DIR, "thumbnail.png"), os.path.join(RELEASE_DIR, "thumbnail.png"))
    shutil.copyfile(os.path.join(MOD_INFO_DIR, "workshop_data.json"), os.path.join(RELEASE_DIR, "workshop_data.json"))
    shutil.copyfile(os.path.join(MOD_INFO_DIR, "License.txt"), os.path.join(RELEASE_DIR, "License.txt"))

    for version in VERSIONS:
        RELEASE_VERSION_DIR = os.path.join(RELEASE_DIR, version)
        os.makedirs(RELEASE_VERSION_DIR)
        shutil.copyfile(os.path.join(MOD_INFO_DIR, "manifest.json"), os.path.join(RELEASE_VERSION_DIR, "manifest.json"))

    # =========== Push to Steam Workshop ===========
    if PUSH_STEAM:
        os.chdir(STEAMCMDDIR)
        changenote = f"Automated Updates {new_version}" if new_version else "Automated Updates unknown"

        with open("workshop.vdf", "w") as file:
            file.write(f'''
            "workshopitem"
            {{
                "appid"            "{APPID}"
                "publishedfileid"  "{PUBLISHEDFILEID}"
                "contentfolder"    "{RELEASE_DIR}"
                "changenote"       "{changenote}"
            }}
            ''')

        print("Content of workshop.vdf:")
        print(open("workshop.vdf").read())

        print("Uploading to Steam Workshop...")
        subprocess.run(["./steamcmd.sh", "+login", "wuyilingwei", f"+workshop_build_item {os.path.abspath('workshop.vdf')}", "+quit"], check=True, text=True)

    else:
        print("Info: -push_steam is disabled by user; skipping Steam Workshop upload.")

    # =========== Push to GitHub ===========
    if PUSH_GITHUB:
        GIT_TAG = f"v{new_version}"
        print("Checking or creating Git tag:", GIT_TAG)

        if not subprocess.run(["git", "rev-parse", GIT_TAG], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            subprocess.run(["git", "tag", GIT_TAG], check=True)
            subprocess.run(["git", "push", "origin", GIT_TAG], check=True)
        else:
            print("Tag", GIT_TAG, "already exists. Skip creating tag.")

        shutil.copytree(RELEASE_DIR, "Timberborn_Mods_Universal_Translate_Github")

        RELEASE_ZIP = f"{new_version}.zip"
        print("Creating release archive:", RELEASE_ZIP)
        shutil.make_archive(RELEASE_ZIP.split(".")[0], "zip", ".", "Timberborn_Mods_Universal_Translate_Github")

        shutil.rmtree("Timberborn_Mods_Universal_Translate_Github")

        RELEASE_NOTES = f"Automated Update to {new_version}"

        print(f"Creating GitHub Release {GIT_TAG} in {REPO_OWNER}/{REPO_NAME}...")
        subprocess.run(["gh", "release", "create", GIT_TAG, "--repo", f"{REPO_OWNER}/{REPO_NAME}", "--title", GIT_TAG, "--notes", RELEASE_NOTES, RELEASE_ZIP], check=True)

        if os.path.isfile(RELEASE_ZIP):
            print("Cleaning up", RELEASE_ZIP)
            os.remove(RELEASE_ZIP)

        print(f"GitHub Release {GIT_TAG} created and {RELEASE_ZIP} uploaded.")

    else:
        print("Info: -push_github is disabled by user; skipping GitHub release.")

else:
    print("No updates detected, skip.")

exit(0)
