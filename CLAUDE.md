# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

This repository is in its initial, pre-implementation state. As of the last update it contains only `README.md` and this file — there is **no application code, build tooling, tests, or dependency manifests yet**.

Stated goal (from `README.md`):

> Deploy a model as an API and build a dashboard for real-time interaction.

Because no stack has been chosen, this file does **not** document build/lint/test commands or a code architecture yet — doing so would be fiction. The sections below are placeholders to be filled in as the project takes shape. **Update this file as soon as real code, tooling, or conventions are introduced**, and remove the TODO markers once each section reflects reality.

## Intended scope (from the goal)

The project is expected to have two parts:

1. **Model-serving API** — exposes a model for inference over HTTP.
2. **Real-time dashboard** — a frontend that interacts with the API live.

The technology stack for both is **not yet decided**. Do not assume a stack; confirm the choice before scaffolding, then record it here.

## Commands

_TODO: No build, lint, run, or test commands exist yet. Document them here once tooling is added (including how to run a single test)._

## Architecture

_TODO: No architecture exists yet. Once code is added, document the big-picture structure here — how the API and dashboard are organized, how they communicate, where the model is loaded/served, and any cross-cutting concerns that require reading multiple files to understand._

## Conventions

_TODO: No project-specific conventions exist yet (no linter config, style guide, Cursor rules, or Copilot instructions found). Record them here as they are established._

## Git workflow

- Default branch: `main`.
- Open a pull request only when explicitly requested.
