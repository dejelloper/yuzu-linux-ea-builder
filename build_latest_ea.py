import base64
import datetime
import lzma
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time

import requests

BASE64_REGEX_NO_ENDING_EQUALS=re.compile("^(?:[A-Za-z\d+/]{4})*(?:[A-Za-z\d+/]{3}=|[A-Za-z\d+/]{2})?$")
YUZU_SRC_LZMA_REGEX=re.compile("^yuzu-windows-msvc-source-[0-9]*-[0-9a-f]*.tar.xz$")

# inspired and modeled after https://gist.github.com/goaaats/9317ee23d406fa66f29bb6bddf53b535
if not os.path.exists("TOKEN"):
    print("TOKEN file not found, see README.md :(")
    sys.exit(1)
tokenFile = open("TOKEN", "r")
token = tokenFile.read().strip()
tokenFile.close()
if not BASE64_REGEX_NO_ENDING_EQUALS.match(token):
    print("Invalid token :(")
    sys.exit(1)
[username, auth] = base64.b64decode(token + "==").decode().split(":")

print("Requesting JWT...")

jwtRequest = requests.post(
    "https://api.yuzu-emu.org/jwt/installer/",
    headers={"X-Username": username, "X-Token": auth},
)
if jwtRequest.status_code != 200:
    print(f"Failed to get JWT ({jwtRequest.status_code}) :(")
    sys.exit(1)

jwt = jwtRequest.text

print("Downloading latest build info...")
downloadsListingRequest = requests.get(
    "https://api.yuzu-emu.org/downloads/earlyaccess/"
)

if downloadsListingRequest.status_code != 200:
    print(
        f"Failed to download latest build info ({downloadsListingRequest.status_code})")

listingData = downloadsListingRequest.json()
latestVersion = listingData["version"]



if not os.path.exists("last_downloaded_ver.txt"):
    temp = open("last_downloaded_ver.txt", "w")
    temp.write("")
    temp.close()


with open("last_downloaded_ver.txt", "r+") as f:
    lastDownloaded = f.read()
    if len(lastDownloaded) > 0 and int(lastDownloaded) >= latestVersion:
        print(f"Already at latest version ({latestVersion})!")
    else:
        print(
            f"Updating to {latestVersion}{f' from {lastDownloaded}' if len(lastDownloaded) > 0 else ''}...")
        for releaseEntry in listingData["files"]:
            if YUZU_SRC_LZMA_REGEX.match(releaseEntry["name"]):
                print("Downloading LZMA...")
                downloadLatestRequest = requests.get(
                    releaseEntry["url"], headers={
                        "Authorization": f"Bearer {jwt}"}
                )

                if downloadLatestRequest.status_code != 200:
                    print(
                        f"Error downloading LZMA ({downloadLatestRequest.status_code}) :("
                    )

                latestFile = open(releaseEntry["name"], "wb")
                latestFile.write(downloadLatestRequest.content)
                latestFile.close()

                print("Extracting...")

                with lzma.open(releaseEntry["name"]) as lzma:
                    with tarfile.open(fileobj=lzma) as tar:
                        if os.path.exists("./src"):
                            shutil.rmtree("./src")
                        content = tar.extractall("./src")

                        os.remove(releaseEntry["name"])

                srcPath = f"./src/{releaseEntry['name'].replace('.tar.xz', '')}"

                with open("build.sh", "w") as buildSH:
                    # this filename would normally be sanitized but its already valited by the regex
                    # -DCMAKE_C_COMPILER=gcc-10 -DCMAKE_CXX_COMPILER=g++-10 
                    buildSH.write(
                        f"cd {srcPath}\nmkdir build\ncd build\ncmake .. -GNinja && ninja"
                    )

                print("Building...")

                startTime = datetime.datetime.now()

                with subprocess.Popen(
                    ["bash", "build.sh"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=1,
                    universal_newlines=True,
                ) as process:
                    for line in process.stdout:
                        print(line, end="")  # process line here
                    for line in process.stderr:
                        print(line, file=sys.stderr, end="")

                if process.returncode != 0:
                    print(f"Failed build ({process.returncode}) :(")
                    sys.exit(process.returncode)
                buildTimeDelta = datetime.datetime.now()-startTime
                # https://stackoverflow.com/a/14190143
                hours = buildTimeDelta.seconds // 3600
                minutes = (buildTimeDelta.seconds % 3600) // 60
                seconds = (buildTimeDelta.seconds % 60)
                print(
                    f"Build successful! It took a solid {hours}H:{minutes}M:{seconds}S :)")
                os.remove("build.sh")
                print("Moving binaries...")
                if not os.path.exists("./build"):
                    os.mkdir("./build")
                shutil.move(f"{srcPath}/build/bin/yuzu", "./build/yuzu")
                shutil.move(f"{srcPath}/build/bin/yuzu-cmd",
                            "./build/yuzu-cmd")
                print("Removing source folder...")
                shutil.rmtree("./src")
                print("Writing version...")
                f.truncate(0)
                f.write(str(latestVersion))
                print("Build finished, see the build folder for the binaries!")
