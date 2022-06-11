This script was made by me because there is no early-access updater/installer for yuzu on linux. It probably has some issues, use at your own risk, etc. Make an issue if you have issues :)

**Dependencies**:
* `python3-requests` (looking to remove this in the future so this project can be zero-dependent)

**How 2 Use**:

1. Make sure you have everything required for a regular build (https://yuzu-emu.org/wiki/building-for-linux/) if you are unable to successfully build with the script, please make sure you can build the regular way before making an issue.
2. Create a file named `TOKEN` (no file extensoin)
3. Put your early access token in that file
4. Run build_latest_ea.py
5. ???
6. Profit (binaries)


**Credits**:
* @goaaats for their gist that this project was based off of: https://gist.github.com/goaaats/9317ee23d406fa66f29bb6bddf53b535
* @yuzu-emu for being chill about this project and being a GOATed emulator