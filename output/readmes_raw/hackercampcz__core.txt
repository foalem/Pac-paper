# Hacker Camp

[![CircleCI](https://circleci.com/gh/hackercampcz/core/tree/trunk.svg?style=shield)](https://circleci.com/gh/hackercampcz/core/tree/trunk)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://renovatebot.com)
[![CodeFactor](https://www.codefactor.io/repository/github/hackercampcz/core/badge)](https://www.codefactor.io/repository/github/hackercampcz/core)
[![CodeScene Code Health](https://codescene.io/projects/28604/status-badges/code-health)](https://codescene.io/projects/28604)
[![CodeScene System Mastery](https://codescene.io/projects/28604/status-badges/system-mastery)](https://codescene.io/projects/28604)

This is a repository with https://www.hackercamp.cz/ website and https://donut.hackercamp.cz/ companion application
for registered hackers.

Hacker Camp Donut is an application that requires Slack integration for user Sign In and other functionality.

## Development

Secrets are stored in 1password vault. Ask @rarous for access to the vault.

When you run something, use [1password CLI](https://developer.1password.com/docs/cli/get-started/) to get secrets.

For example, to run website locally, you have to use:

```bash
op run --env-file=.env --no-masking -- yarn start:www.hackercamp.cz
```

To run Donut locally:

```bash
op run --env-file=.env --no-masking -- yarn start:donut.hackercamp.cz
```

## Infrastructure

Infrastructure is provisioned with Pulumi

<img src="https://www.pulumi.com/images/pricing/team-oss.svg" width="300">
