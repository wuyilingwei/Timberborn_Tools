import os
import subprocess
import shutil
import zipfile
import logging


class Releaser:
    def __init__(self, base_dir, app_id, published_file_id, repo_owner, repo_name):
        self.base_dir = base_dir
        self.git_dir = os.path.join(base_dir, "git")
        self.steamcmd_dir = os.path.join(base_dir, "steam")
        self.mod_info_dir = os.path.join(base_dir, "mod_info")
        self.release_dir = os.path.join(base_dir, "release")
        self.context_dir = os.path.join(self.git_dir, "mod")
        self.manifest_file = os.path.join(self.mod_info_dir, "manifest.json")
        self.versions_file = os.path.join(self.git_dir, "versions.txt")
        self.app_id = app_id
        self.published_file_id = published_file_id
        self.logger = logging.getLogger(self.__class__.__name__)

    def update_version(self, overwrite=False):
        if not os.path.exists(self.manifest_file):
            self.logger.warning("No manifest.json found, skipping version update.")
            return None

        with open(self.manifest_file, "r", encoding="utf-8") as f:
            content = f.read()

        current_version = None
        new_version = None
        if overwrite:
            self.logger.info("Overwrite enabled, skipping version update.")
        else:
            import re
            match = re.search(r'"Version":\s*"(\d+\.\d+\.\d+)"', content)
            if match:
                current_version = match.group(1)
                self.logger.info(f"Current version: {current_version}")
                version_parts = current_version.split(".")
                version_parts[-1] = str(int(version_parts[-1]) + 1)
                new_version = ".".join(version_parts)
                self.logger.info(f"New version: {new_version}")
                content = content.replace(current_version, new_version)
                with open(self.manifest_file, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                self.logger.error("Version not found in manifest.json!")
        return new_version

    def prepare_release(self):
        if not os.path.exists(self.versions_file) or os.path.getsize(self.versions_file) == 0:
            self.logger.error("versions.txt is empty or does not exist!")
            raise FileNotFoundError("versions.txt is empty or does not exist!")

        with open(self.versions_file, "r", encoding="utf-8") as f:
            versions = [v.strip() for v in f.read().split(",") if v.strip()]

        self.logger.info(f"All game versions: {versions}")

        if os.path.exists(self.release_dir):
            shutil.rmtree(self.release_dir)
        os.makedirs(self.release_dir, exist_ok=True)

        # Copy common files
        shutil.copytree(self.context_dir, self.release_dir, dirs_exist_ok=True)
        for file_name in ["thumbnail.png", "workshop_data.json", "License.txt", "joinus.txt"]:
            src = os.path.join(self.mod_info_dir, file_name)
            if os.path.exists(src):
                shutil.copy(src, self.release_dir)

        # Copy version-specific files
        for version in versions:
            version_dir = os.path.join(self.release_dir, version)
            os.makedirs(version_dir, exist_ok=True)
            shutil.copy(self.manifest_file, version_dir)

        return versions

    def upload_to_steam(self, new_version):
        changenote = f"Automated Updates {new_version or 'unknown'}"
        vdf_path = os.path.join(self.steamcmd_dir, "workshop.vdf")
        with open(vdf_path, "w", encoding="utf-8") as f:
            f.write(
                f"""
"workshopitem"
{{
    "appid"            "{self.app_id}"
    "publishedfileid"  "{self.published_file_id}"
    "contentfolder"    "{self.release_dir}"
    "changenote"       "{changenote}"
}}
"""
            )

        self.logger.info("Uploading to Steam Workshop...")
        subprocess.run(
            [os.path.join(self.steamcmd_dir, "steamcmd.sh"), "+workshop_build_item", vdf_path, "+quit"],
            check=True,
        )
        self.logger.info("Steam Workshop upload completed.")

    def upload_to_github(self, new_version):
        git_tag = f"v{new_version}"
        self.logger.info(f"Creating Git tag: {git_tag}")
        subprocess.run(["git", "tag", git_tag], cwd=self.git_dir, check=True)
        subprocess.run(["git", "push", "origin", git_tag], cwd=self.git_dir, check=True)

        # Create release archive
        tmp_folder = os.path.join(self.base_dir, "Timberborn_Mods_Universal_Translate_Github")
        if os.path.exists(tmp_folder):
            shutil.rmtree(tmp_folder)
        shutil.copytree(self.release_dir, tmp_folder)

        release_zip = os.path.join(self.base_dir, f"{new_version}.zip")
        with zipfile.ZipFile(release_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(tmp_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmp_folder)
                    zipf.write(file_path, arcname)

        shutil.rmtree(tmp_folder)

        # Create GitHub release
        release_notes = f"Automated Update to {new_version}"
        self.logger.info(f"Creating GitHub Release {git_tag}...")
        subprocess.run(
            [
                "gh",
                "release",
                "create",
                git_tag,
                "--repo",
                f"{self.repo_owner}/{self.repo_name}",
                "--title",
                git_tag,
                "--notes",
                release_notes,
                release_zip,
            ],
            check=True,
        )
        os.remove(release_zip)
        self.logger.info(f"GitHub Release {git_tag} created.")

    def run(self, overwrite=False, push_steam=True, push_github=True):
        self.logger.info("Starting release process...")
        new_version = self.update_version(overwrite)
        versions = self.prepare_release()

        if push_steam:
            self.upload_to_steam(new_version)

        if push_github:
            self.upload_to_github(new_version)

        self.logger.info("Release process completed.")