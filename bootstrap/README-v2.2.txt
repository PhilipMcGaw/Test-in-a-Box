Bootstrap v2.2 fixes WinPython release-asset resolution.

The checksum manifest may name a newer asset than the GitHub release marked
"latest". The previous bootstrap constructed:

  /releases/latest/download/<asset>

which returned HTTP 404 when the selected file belonged to another release.

The corrected bootstrap now:

- selects the filename and SHA-256 from the official checksum manifest;
- looks for that exact filename on the official WinPython download page;
- falls back to recent tags from GitHub's public releases Atom feed;
- tries only official download locations;
- does not use the GitHub REST API;
- verifies the downloaded file against the manifest SHA-256.
