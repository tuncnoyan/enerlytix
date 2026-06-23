# Contracts for Etainabl Site & Supply Sync

## Purpose

This directory defines the interface contracts for the initial web app feature.
The initial version exposes the following internal API expectations:

- Site list retrieval for the searchable site pane.
- Supply list retrieval for the selected site.
- Site/supply sync trigger endpoint.

## Contract Guidelines

- The app uses JSON for API responses.
- All endpoints are designed for frontend consumption by a Django-backed web UI.
- The contracts here are implementation-agnostic specifications for expected data shapes.
