# Contributing to Charli3 Dendrite

If you would like to support this project, have an idea to improve it, or if you found some errors – fork the repository, add your fixes, and open a pull request to the **main branch**.

## Reporting Issues and Requesting Features

To help us improve, please use the appropriate issue template when reporting a bug or requesting a feature.

- **[Report a Bug](https://github.com/Charli3-Official/charli3-dendrite/blob/main/.github/ISSUE_TEMPLATE/bug_report.md)** – Use this template to provide detailed information on bugs.
- **[Request a Feature](https://github.com/Charli3-Official/charli3-dendrite/blob/main/.github/ISSUE_TEMPLATE/feature_request.md)** – Use this template to suggest new features or improvements.

Please follow the prompts in each template to ensure all necessary information is provided.

### Guidelines for Issue Discussions

The [GitHub issues](https://github.com/Charli3-Official/charli3-dendrite/issues) page is the preferred channel for bug reports, feature requests, and submitting pull requests. Please keep discussions focused and constructive:

- **Stay on topic** and avoid derailing or trolling in discussions.
- Respect the opinions of others and keep conversations constructive.

## Pull Requests

When submitting a pull request, please follow these guidelines:

- Base your code on the latest main branch to avoid conflicts.
- Ensure your pull request is concise and focused on a single issue or feature.
- Clearly explain the problem and your proposed solution in the PR description.
- Optional, adding tests is appreciated

## Code Quality and Linting

To maintain code quality, this project uses **pre-commit** hooks for linting and formatting. Run `pre-commit` locally before pushing your changes:


```bash
pre-commit install && pre-commit run --all-files
```
This will apply all configured checks locally. GitHub Actions will also automatically run these checks on pull requests, but running them locally helps catch issues earlier.


## License

By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE.md).

## Building Documentation

This project uses **MkDocs** with **mkdocs-material** and **mkdocstrings** for documentation.
```bash
poetry install && poetry run mkdocs serve
```
To view the documentation locally, start the MkDocs and open [http://127.0.0.1:8000/charli3-dendrite/](http://127.0.0.1:8000/charli3-dendrite/). Any changes to the source code will auto-update in your browser.
