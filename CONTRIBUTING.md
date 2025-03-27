# Contributing

Thank you for considering contributing to Secure-AI-Toolset! 
We welcome contributions to improve this project. For general contributions and community guidelines, please see the repo.

## Legal
Any submission of work, including any modification of, or addition to, an existing work (“Contribution”) to [complete project name] shall be governed by and subject to the terms of the Apache License 2.0 (the “License”) and to the following complementary terms. In case of any conflict or inconsistency between the provision of the License and the complementary terms, the complementary terms shall prevail.
By submitting the Contribution, you represent and warrant that the Contribution is your original creation and you own all right, title and interest in the Contribution. You represent that you are legally entitled to grant the rights set out in the License and herein, without violation of, or conflict with, the rights of any other party. You represent that your Contribution includes complete details of any third-party license or other restriction associated with any part of your Contribution of which you are personally aware.

## Table of Contents

- [Legal](#legal)
- [Contributing](#contributing)
- [Development](#development)
- [Testing](#testing)
- [Releases](#releases)

## General Steps for Contributing

1. [Fork the project](https://help.github.com/en/github/getting-started-with-github/fork-a-repo)
2. [Clone your fork](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository)
3. Make local changes to your fork by editing files
3. [Commit your changes](https://help.github.com/en/github/managing-files-in-a-repository/adding-a-file-to-a-repository-using-the-command-line)
4. [Push your local changes to the remote server](https://help.github.com/en/github/using-git/pushing-commits-to-a-remote-repository)
5. [Create new Pull Request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork)

From here your pull request will be reviewed and once you've responded to all
feedback it will be merged into the project. Congratulations, you're a
contributor!

## Development

To start developing and testing using our development scripts, the following tools need to be installed:
* Python = 3.10
* Poetry = 2.1.1

## Testing

1. Commit and push your changes to your repository.
2. Clone the repository 
3. Install the dependencies 

```bash 
poetry install
```
4. Run the unit tests

The working directory is the project root
```bash 
pytest -v ./tests/unit
```
5. Run the integration test
Follow the guidelines in the [README.md](tests/integration/README.md) file inside the `tests/integration` folder.

6. Make sure that your code is clean, by running the `code_clean.bash` script:  
   First run:
   ```shell
   poetry env activate
   ```
   Then run the command it has outputted. Should look as follows:
   ```shell
   source <your current working folder>/secure-ai-toolset/.venv/bin/activate
   ```
   Run this command above. This should activate the virtual environment.  
   Finally, run the following command:
   ```shell
   ./scripts/code_clean.bash
   ```

## Releases

Maintainers only should create releases. Follow these steps to prepare for a release:

### Pre-requisites
Review recent commits and ensure the changelog includes all relevant changes, with references to GitHub issues or PRs when applicable.
Verify that any updated dependencies are accurately reflected in the NOTICES.
Confirm that the required documentation is complete and has been approved.\
