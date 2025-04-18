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

# =========== Mod Config ===========
APPID="1062090"
PUBLISHEDFILEID="3346918947"

# =========== GitHub Config ===========
REPO_OWNER="wuyilingwei"
REPO_NAME="Timberborn_Mods_Universal_Translate"

# =========== Command Config ===========
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
        -no_steam)
            PUSH_STEAM=false
            ;;
        -no_github)
            PUSH_GITHUB=false
            ;;
    esac
done

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
    if [ "$LOCAL" != "$REMOTE" ]; then
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

    cp -r "$CONTEXT_DIR"/* "$RELEASE_DIR"/
    cp -r "$MOD_INFO_DIR"/thumbnail.png "$RELEASE_DIR"/
    cp -r "$MOD_INFO_DIR"/workshop_data.json "$RELEASE_DIR"/
    cp -r "$MOD_INFO_DIR"/License.txt "$RELEASE_DIR"/

    for version in "${VERSIONS[@]}"; do
        RELEASE_VERSION_DIR="$RELEASE_DIR/$version"
        mkdir -p "$RELEASE_VERSION_DIR"
        cp -r "$MOD_INFO_DIR"/manifest.json "$RELEASE_VERSION_DIR"/
    done

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
