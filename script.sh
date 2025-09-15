#!/bin/bash
set -eu

echo "----------------------------------------"

# =========== Path Config ===========
BASE_DIR="/home/Timberborn"
GIT_DIR="$BASE_DIR/git"
STEAMCMDDIR="$BASE_DIR/steam"
MOD_INFO_DIR="$BASE_DIR/mod_info"
RELEASE_DIR="$BASE_DIR/release"
CONTEXT_DIR="$GIT_DIR/mod"
MANIFEST_FILE="$MOD_INFO_DIR/manifest.json"
VERSIONS_FILE="$GIT_DIR/versions.txt"
VENV_DIR="$BASE_DIR/venv"

# =========== Mod Config ===========
APPID="1062090"
PUBLISHEDFILEID="3346918947"

# =========== GitHub Config ===========
REPO_OWNER="wuyilingwei"
REPO_NAME="Timberborn_Mods_Universal_Translate"

# =========== Command Config ===========
GETUPDATE=true
FORCE_UPDATE=false
OVERWRITE=false
PUSH_STEAM=true
PUSH_GITHUB=true

# =========== Command Line Args ===========
for arg in "$@"; do
    case "$arg" in
        -force)
            FORCE_UPDATE=true
            ;;
        -overwrite)
            OVERWRITE=true
            ;;
        -skip_update)
            GETUPDATE=false
            ;;
        -no_steam)
            PUSH_STEAM=false
            ;;
        -no_github)
            PUSH_GITHUB=false
            ;;
    esac
done

# =========== Ensure Virtual Environment ===========
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Virtual environment not found. Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r "$BASE_DIR/requirments.txt"
else
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# =========== Main ===========
echo "Run time:$(date)"

# =========== Fetch Updates ===========
cd "$GIT_DIR"

echo "Fetching origin updates..."
git fetch origin main

LOCAL=$(git rev-parse main)
REMOTE=$(git rev-parse origin/main)

echo "Local commit: $LOCAL"
echo "Remote commit: $REMOTE"

# =========== Check Updates ===========
if [ "$LOCAL" != "$REMOTE" ] || [ "$FORCE_UPDATE" = true ]; then
    if [ "$LOCAL" != "$REMOTE" ] && [ "$GETUPDATE" = true ]; then
        echo "Detected updates, pulling..."
    else
        echo "Forced update, pulling..."
    fi

    git pull origin main
    
    mkdir -p "$MOD_INFO_DIR"
    
    # =========== Update Version ===========
    if [ -f "$MANIFEST_FILE" ]; then
        if [ "$OVERWRITE" = true ]; then
            echo "enabled -overwrite, skip version update."
            new_version=$(grep -oP '"Version":\s*"\K2\.0\.\d+' "$MANIFEST_FILE" || echo "")
        else
            current_version=$(grep -oP '"Version":\s*"\K2\.0\.\d+' "$MANIFEST_FILE" || echo "")
            if [ -z "$current_version" ]; then
                echo "Error: Can't find version in manifest.json!"
            else
                echo "Now version: $current_version"
                last_digit=$(echo "$current_version" | awk -F'.' '{print $3}')
                version_head=$(echo "$current_version" | awk -F'.' '{print $1"."$2}')
                new_last_digit=$((last_digit + 1))
                new_version="${version_head}.${new_last_digit}"
                echo "Version updated to: $new_version"
                sed -i "0,/${current_version}/s/${current_version}/${new_version}/" "$MANIFEST_FILE"
            fi
        fi
    else
        echo "No manifest.json found, skip version update."
    fi

    if [ ! -s "$VERSIONS_FILE" ]; then
        echo "Error: versions.txt is empty or not exists!"
        exit 1
    fi

    # =========== Create Release ===========
    sed -i 's/\r$//' "$VERSIONS_FILE"
    sed -i 's/^,\|,$//g' "$VERSIONS_FILE"

    IFS=',' read -r -a VERSIONS < "$VERSIONS_FILE" || true
    echo "All game versions: ${VERSIONS[@]}"

    rm -rf "$RELEASE_DIR"
    mkdir -p "$RELEASE_DIR"

    # 检查 CONTEXT_DIR 是否存在且非空
    if [ -d "$CONTEXT_DIR" ] && [ "$(ls -A "$CONTEXT_DIR")" ]; then
        cp -r "$CONTEXT_DIR"/* "$RELEASE_DIR"/
    else
        echo "Warning: $CONTEXT_DIR is empty or does not exist. Skipping copy."
    fi

    cp -r "$MOD_INFO_DIR"/thumbnail.png "$RELEASE_DIR"/
    cp -r "$MOD_INFO_DIR"/workshop_data.json "$RELEASE_DIR"/
    cp -r "$MOD_INFO_DIR"/License.txt "$RELEASE_DIR"/

    for version in "${VERSIONS[@]}"; do
        RELEASE_VERSION_DIR="$RELEASE_DIR/$version"
        mkdir -p "$RELEASE_VERSION_DIR"
        cp -r "$MOD_INFO_DIR"/manifest.json "$RELEASE_VERSION_DIR"/
    done

    # =========== Convert TOML to CSV ===========
    DATA_DIR="$GIT_DIR/data"
    MOD_DIR="$GIT_DIR/mod"

    echo "Converting TOML files to CSV..."
    python3 - <<EOF
import os
import re
import toml
import csv
import shutil

data_dir = "$DATA_DIR"
mod_dir = "$MOD_DIR"

# 第一阶段：处理所有 TOML 文件（包括 default）
default_files = {}  # 存储 default 版本的文件信息

for file_name in os.listdir(data_dir):
    if file_name.endswith(".toml"):
        # 提取 mod_id 和 version
        if "_default.toml" in file_name:
            # 处理 default 版本
            mod_id = file_name.replace("_default.toml", "")
            version = "default"
        else:
            match = re.search(r"(\\d+)_version-(.+)\\.toml", file_name)
            if not match:
                print(f"Skipping file {file_name}: does not match expected pattern")
                continue
            mod_id, version = match.groups()
        
        version_folder = f"version-{version}" if version != "default" else "default"
        toml_path = os.path.join(data_dir, file_name)
        output_dir = os.path.join(mod_dir, version_folder, "Localizations")
        os.makedirs(output_dir, exist_ok=True)

        # 读取 TOML 文件
        try:
            with open(toml_path, "r", encoding="utf-8") as toml_file:
                data = toml.load(toml_file)
            
            # 收集所有语言代码
            all_languages = set()
            for key, translations in data.items():
                if isinstance(translations, dict):
                    for lang_code in translations.keys():
                        if lang_code != "raw":
                            all_languages.add(lang_code)
            
            # 为每种语言生成 CSV 文件
            generated_files = []
            for lang_code in all_languages:
                csv_file_name = f"{lang_code}_{mod_id}.csv"
                csv_path = os.path.join(output_dir, csv_file_name)
                
                with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(["ID", "Text", "Comment"])
                    
                    # 遍历所有翻译条目
                    for translation_key, translations in data.items():
                        if isinstance(translations, dict) and lang_code in translations:
                            translation_text = translations[lang_code]
                            writer.writerow([translation_key, translation_text, "-"])
                
                generated_files.append((csv_file_name, csv_path))
                print(f"Generated CSV: {csv_path}")
            
            # 如果是 default 版本，记录生成的文件
            if version == "default":
                default_files[mod_id] = {
                    'output_dir': output_dir,
                    'files': generated_files
                }
                
        except Exception as e:
            print(f"Failed to process {toml_path}: {e}")

# 第二阶段：将 default 文件复制到其他版本文件夹
if default_files:
    print("Copying default files to other version folders...")
    version_dirs = [d for d in os.listdir(mod_dir) if d.startswith("version-") and os.path.isdir(os.path.join(mod_dir, d))]
    
    for mod_id, default_info in default_files.items():
        for version_dir in version_dirs:
            target_localization_dir = os.path.join(mod_dir, version_dir, "Localizations")
            os.makedirs(target_localization_dir, exist_ok=True)
            
            for csv_file_name, source_path in default_info['files']:
                target_path = os.path.join(target_localization_dir, csv_file_name)
                
                # 只在目标文件不存在时复制
                if not os.path.exists(target_path):
                    shutil.copy2(source_path, target_path)
                    print(f"Copied default file to: {target_path}")
                else:
                    print(f"Skipped copying to {target_path} (file already exists)")
EOF

    echo "TOML to CSV conversion completed."

    # =========== Push to Steam Workshop ===========
    if [ "$PUSH_STEAM" = true ]; then
        cd "$STEAMCMDDIR"
        changenote="Automated Updates ${new_version:-unknown}"

        cat <<EOF > workshop.vdf
"workshopitem"
{
    "appid"            "$APPID"
    "publishedfileid"  "$PUBLISHEDFILEID"
    "contentfolder"    "$RELEASE_DIR"
    "changenote"       "$changenote"
}
EOF

        echo "Content of workshop.vdf:"
        cat workshop.vdf

        echo "Uploading to Steam Workshop..."
        "$STEAMCMDDIR/steamcmd.sh" \
            +login wuyilingwei \
            +workshop_build_item "$(pwd)/workshop.vdf" \
            +quit || {
                echo "Error: SteamCMD Upload Failed!"
            }
    else
        echo "Info: -push_steam is disabled by user; skipping Steam Workshop upload."
    fi

    # =========== Push to GitHub ===========
    if [ "$PUSH_GITHUB" = true ]; then
        GIT_TAG="v${new_version}"
        echo "Checking or creating Git tag: $GIT_TAG"

        if ! git rev-parse "$GIT_TAG" >/dev/null 2>&1; then
            git tag "$GIT_TAG" || {
                echo "Error: Failed to create tag $GIT_TAG!"
            }
            git push origin "$GIT_TAG"
        else
            echo "Tag $GIT_TAG already exists. Skip creating tag."
        fi

        cd "$BASE_DIR"
        TMP_FOLDER="Timberborn_Mods_Universal_Translate_Github"
        rm -rf "$TMP_FOLDER"
        cp -r release "$TMP_FOLDER"

        RELEASE_ZIP="${new_version}.zip"
        echo "Creating release archive: $RELEASE_ZIP"
        zip -r "$RELEASE_ZIP" "$TMP_FOLDER"

        rm -rf "$TMP_FOLDER"

        RELEASE_NOTES="Automated Update to $new_version"

        echo "Creating GitHub Release $GIT_TAG in $REPO_OWNER/$REPO_NAME..."
        gh release create "$GIT_TAG" \
            --repo "$REPO_OWNER/$REPO_NAME" \
            --title "$GIT_TAG" \
            --notes "$RELEASE_NOTES" \
            "$RELEASE_ZIP" || {
                echo "Error: GitHub Release creation failed!"
            }

        if [ -f "$RELEASE_ZIP" ]; then
            echo "Cleaning up $RELEASE_ZIP..."
            rm -f "$RELEASE_ZIP"
        fi

        echo "GitHub Release $GIT_TAG created and $RELEASE_ZIP uploaded."
    else
        echo "Info: -push_github is disabled by user; skipping GitHub release."
    fi

else
    echo "No updates detected, skip."
fi

exit 0
