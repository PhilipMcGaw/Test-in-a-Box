# Updater Roadmap Note

The no-Git updater supports:

- ✅ Stable channel
  - latest published GitHub release;
  - newest tag when no release exists;
  - clear message when neither exists.
- ✅ Development channel
  - latest configured branch, currently `main`.
- ✅ Local Python, vendor files, logs, results, runs and sequences preserved.
- ✅ `webapp/config.json` preserved.
- ✅ Application backup before replacement.
- ✅ Optional bootstrap after updating dependencies.
- ✅ No Git installation required.

Future improvements:

- ⬜ In-application **Help → Check for Updates** interface.
- ⬜ Display commit identity for development updates.
- ⬜ Signed update manifest or published archive hashes.
- ⬜ One-click rollback interface.
