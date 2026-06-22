# audio_matcher

An open-source learning project for experimenting with audio fingerprinting and
song matching ideas inspired by Shazam.

## Development Environment

Create the conda environment:

```bash
conda env create -f environment.yml
```

Activate it:

```bash
conda activate audio_matcher
```

If the environment already exists and `environment.yml` changes later, update it:

```bash
conda env update -f environment.yml --prune
```

Run the downloader:

```bash
python src/download_youtube_audio.py
```
