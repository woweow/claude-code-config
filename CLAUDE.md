# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This repository contains Claude Code configurations and scripts for various development workflows. All scripts prioritize highest level of portability with minimal dependency installations.

## Development Commands

- **Install dependencies**: `./install.sh` (when available - contains all required installation commands for the repository)
- **AWS profile**: Use "dev" profile with SSO when writing AWS-related scripts

## Architecture

This is a configuration repository structured to support:
- Portable shell scripts with minimal external dependencies  
- Claude Code configuration files and templates
- AWS development workflows using SSO authentication

## Script Development Guidelines

- Aim for maximum portability across different systems
- Minimize external dependency requirements
- When adding new dependencies, update `install.sh` script in repository root
- Use AWS profile "dev" with SSO for any AWS-related operations