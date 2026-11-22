# Security policy

## Reporting a vulnerability

Please don't report security problems in public issues, pull requests or discussions.

Report them privately instead: open the [Security tab](https://github.com/arukavina/algo-art-frames-public/security) of this repository and click **Report a vulnerability**. Describe what you found, how to reproduce it and what impact you think it has.

You'll get a reply as soon as possible. This is a volunteer, passion project, so please allow a few days. Once a fix is ready, the report is credited to you unless you'd rather stay anonymous.

## Scope

This repository contains the poster plugins and the small rendering library they use. Reports are especially welcome about plugin code that gets past the safety checks in `tests/test_contract.py`, for example by importing modules outside the allowlist or reading files.

## Supported versions

Only the latest commit on `main` is supported.
