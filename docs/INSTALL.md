# Install

## Developer

```bash
scripts/bootstrap_dev.sh
make test
```

For local Whisper/audio packages:

```bash
scripts/bootstrap_local_ai.sh
```

The app uses `imageio-ffmpeg` so packaged builds can include an FFmpeg binary without asking physicians to install FFmpeg manually. Large Whisper model downloads are not automatic yet; the UI will need explicit model selection/download consent.

## End user

Future releases will provide OS installers from GitHub Releases. The installer must bundle the Python runtime, backend, desktop shell, frontend assets, and audio conversion support.
