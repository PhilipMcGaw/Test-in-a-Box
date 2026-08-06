Bootstrap v2.1.4 removes the Pico `/layout` step.

The previous implementation downloaded the installer into a temporary
folder, ran `/layout`, copied one file, and then removed the temporary
folder. That made the flow unnecessarily destructive and could discard
useful installer files.

The corrected implementation now:

- resolves the current official PicoSDK installer URL;
- downloads the installer directly to `vendor/pico/installer/`;
- never executes it;
- never deletes it;
- records its URL, size and SHA-256;
- treats missing Pico runtime support as optional.
