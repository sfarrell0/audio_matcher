# Audio Matcher Plan

## Purpose
Build a Shazam-like audio matching project as a learning exercise, with the system understood in stages through notebooks before any larger product surface is added. The goal is to make the architecture clear, reproducible, and easy to reason about end to end.

## Current Foundation
Stage 1 is the existing library-building workflow:
- `src/download_youtube_audio.py` produces the local music folder.
- `music_registry.csv` records the downloaded tracks and their metadata.
- The local music folder plus the registry are the only required starting assets for the project.

This stage is the baseline for everything else. It defines the initial corpus the matcher will learn from and search against.


## Stage 2 and Stage 3
These stages define the core matching architecture and are worth careful discussion before implementation.

The intended direction is a Shazam-like approach built around landmark hashes:
- A track is represented in a way that can survive short clips and offsets.
- A query clip is turned into the same kind of representation.
- The system compares query representation against the local library and ranks candidate matches.
- The design should explain how the matching signal is formed and why it is expected to be robust.

The purpose of these stages is to define the architecture at a high level, not to commit to code-level mechanics yet.

## Stage 4
Evaluation is also worth discussing explicitly.

The first success criterion should be simple and concrete:
- the correct track is ranked first on a small curated set of clips.

The evaluation plan should also leave room for a tiny repeatable benchmark so changes can be understood over time. The emphasis is on whether the system is behaving correctly and consistently, not on building a large formal test suite up front.

## Stage 5
Stage 5 is future work.

It can mention possible extensions such as:
- a UI
- microphone input
- larger libraries
- broader search or scaling ideas

These are not part of the first deliverable. They are only included to show where the project could go after the core notebook-driven prototype is understood.

## Notebook Approach
Use notebooks as the main way to explore and document the system.

Each notebook should:
- focus on one stage or one conceptual question
- explain the reasoning behind architectural decisions
- make the data flow visible
- help the system be understood, not just executed

The notebooks should read like technical documentation for the project as it develops.

## Success Criteria
The project is successful when:
- the architecture is understandable from the plan and notebooks alone
- the library foundation is clearly established
- the fingerprint-based matcher can be reasoned about at a high level
- the correct track can be ranked first on a small curated set of examples
- future work is clearly separated from the core prototype

## Assumptions
- The initial library comes from the existing YouTube download workflow.
- The project remains small and notebook-driven at first.
- The matching core should be fingerprint-based, not embedding-first.
- Stage 6 stays non-binding and future-oriented.
