# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.1] - 11.06.2026

### Added
- Add "terminal trove tool of the week" message by @antoniorodr

### Changed
- Update version
- Create new file for `CronAutoComplete`
- Merge branch 'include-missing-logging-scripts' into release/v0.7.1
- Update interface overview gif by @antoniorodr
- Update `UV` installation explanation by @antoniorodr
- Update installation methods by @antoniorodr
- Update cron installation check on the docs by @antoniorodr
- Update cron installation check by @antoniorodr
- Update `UV` installation method by @antoniorodr
- Update release workflow by @antoniorodr
- Update publish pypi workflow by @antoniorodr
- Update release workflow by @antoniorodr
- Create pypi workflow by @antoniorodr
- Update `UV` installation method by @antoniorodr
- Update installation methods by @antoniorodr
- Update flake workflow by @antoniorodr
- Update `CHANGELOG.md` by @antoniorodr

### Fixed
- Fix a bug where a not standard expression was parsed
- Include missing logging scripts
- Fix the size of the `CronCreator` screen

### Removed
- Delete unused exception variable
- Delete uneccesary `if` statments by @antoniorodr

## [0.7.0] - 04.06.2026

### Added
- Add miniwi font by @antoniorodr
- Add toast when text is copied by @antoniorodr
- Add link to Textual by @antoniorodr

### Changed
- Update `uv.lock` by @antoniorodr
- Change order of the links by @antoniorodr
- Create donation button for the header by @antoniorodr
- Refactor `tests/` folder with better structure by @antoniorodr
- Update `pyproject.toml` version by @antoniorodr
- Change docstring by @antoniorodr
- Merge branch 'feat/logs-own-folder' into release/v0.7.0 by @antoniorodr
- Change the `log_dir` path to the new one with identificator by @antoniorodr
- Change the `LOG_DIR` to use the `JOB_NAME` on the path by @antoniorodr
- Update readme with link to the documentation by @antoniorodr
- Change `Shortcuts` with `Keybinds` by @antoniorodr
- Change word `shortcuts` for `keybinds` by @antoniorodr
- Update `zensical.toml` by @antoniorodr
- Update website by @antoniorodr
- Update `zensical.toml` by @antoniorodr
- Create new `index.md` as the home of the page by @antoniorodr
- Create `home.html` to override the default one by @antoniorodr
- Create .css to override the default themes by @antoniorodr
- Create JS files for the install section and docs link by @antoniorodr
- Move sprites to `sprites.svg` and change interface gif by @antoniorodr
- Update `README.md` demo by @antoniorodr
- Update flake workflow by @antoniorodr

### Fixed
- Fix bug with installation section on mobile by @antoniorodr
- Fix logo display with custom font by @antoniorodr
- Fix style and size by @antoniorodr
- Fix ascii display problem by @antoniorodr
- Update favicon by @antoniorodr
- Fix showing wrong title on home by @antoniorodr
- Fix favicon showing zensical default by @antoniorodr
- Fix a bug where the hamburger menu was empty by @antoniorodr
- Fix toast color text in light mode by @antoniorodr

### Removed
- Delete `paths` variable by @antoniorodr
- Delete on ssh using the new logs path by @antoniorodr

## [0.6.2] - 27.05.2026

### Added
- Add write permissions to update-flake-lock job by @antoniorodr

### Changed
- Update `CHANGELOG.md` by @antoniorodr
- Create ascii title by @antoniorodr
- Update version by @antoniorodr
- Merge branch 'feat/log-crono-order' into release/v0.6.2 by @antoniorodr
- Order logs chronologically by @antoniorodr
- Update update flake workflow by @antoniorodr
- Update release workflow by @antoniorodr
- Update `CHANGELOG.md` by @antoniorodr

## [0.6.1] - 26.05.2026

### Changed
- Merge branch 'release/v0.6.1' by @antoniorodr
- Update `README.md` by @antoniorodr
- Move css to `cronboard.tcss` by @antoniorodr
- Create wrapper and log constants by @antoniorodr
- Move path constants to `config.py` by @antoniorodr
- Update contants path by @antoniorodr
- Move `LOG_DIR` constant to config.py by @antoniorodr
- Update version by @antoniorodr
- Create config.py to store path variables by @antoniorodr
- Move path attributes to config file as constant by @antoniorodr
- Update readme by @antoniorodr
- Update keybinds by @antoniorodr

### Fixed
- Update test to use the new `config.py` file constants by @antoniorodr
- Fix logs path by @antoniorodr

### Removed
- Delete unreachable code by @antoniorodr

## [0.6.0] - 22.05.2026

### Added
- Add __init__.py files to new folders by @antoniorodr

### Changed
- Update keyboard shortcuts for the documentation by @antoniorodr
- Update changelog by @antoniorodr
- Merge branch 'release/v0.6.0' by @antoniorodr
- Update imports after moving files by @antoniorodr
- Update cov pyproject by @antoniorodr
- Move file to new location for better structure by @antoniorodr
- Update imports after moving files by @antoniorodr
- Move files to new location for better structure by @antoniorodr
- Update imports after moving files by @antoniorodr
- Move files to new location for better structure by @antoniorodr
- Update imports after moving files by @antoniorodr
- Update imports after the file move by @antoniorodr
- Move CronEncrypt to cronboard/services/encryption by @antoniorodr
- Merge branch 'feat/cronjob-logging' into release/v0.6.0 by @antoniorodr
- Change formatting by @antoniorodr
- Update gitignore by @antoniorodr
- Toggle tab enablement by @bcExpt1123
- Change visibility of the error message in cron creator form by @bcExpt1123
- Change initial visibility of the error message in cron creator form by @bcExpt1123
- Improve radioset of croncreator with jk by @bcExpt1123
- Improve log view's performance by @bcExpt1123
- Fix feedbacks - change log viewer modal size by @bcExpt1123
- Fix feedbacks - add hjkl into log viewer by @bcExpt1123
- Fix feedbacks - pause functionality in cron table by @bcExpt1123
- Fix feedbacks - improve tests with helpers by @bcExpt1123
- Fix feedbacks - change config folder by @bcExpt1123
- Fix feedbacks by @bcExpt1123
- Update cron-wrapper by @bcExpt1123
- Update cron-wrapper.sh to improve logs by @bcExpt1123
- Add cron log functionality into servers section by @bcExpt1123
- Add tests for logger service by @bcExpt1123
- Add log viewer for local by @bcExpt1123
- Add logging functionality on local by @bcExpt1123
- Merge branch 'fix/disconnect' into release/v0.6.0 by @antoniorodr
- Bump version to 0.6.0 by @antoniorodr
- Change code styling for better readability by @antoniorodr
- Merge branch 'feat/list-not-intuitive' into release/v0.6.0 by @antoniorodr in [#49](https://github.com/antoniorodr/cronboard/pull/49)
- Make list behavior more intuitive by @bcExpt1123
- Merge branch 'fix(cronjob)/duplicatedId-in-cronjob-dialog' into release/v0.6.0 by @antoniorodr in [#48](https://github.com/antoniorodr/cronboard/pull/48)
- Update changelog by @antoniorodr

### Fixed
- Fix import which was making tests fail by @antoniorodr
- Fix bash_path bug on macOS by @antoniorodr in [#50](https://github.com/antoniorodr/cronboard/pull/50)
- Update test assert by @antoniorodr
- Fix deleting cronjob in Servers tab by @bcExpt1123
- Clear code by @bcExpt1123
- RadioButton's default value by @bcExpt1123
- Fix visual bug on CronCreator by @antoniorodr
- Fix logview - no logs found by @bcExpt1123
- Fix cron wrapper to enable special letters like quote in command by @bcExpt1123
- Fix VimKeysRadioSet default value by @bcExpt1123
- Resolve feedbacks by @bcExpt1123
- Fix a bug when disconnecting if no conextion exist by @antoniorodr
- Handle duplicated id error in cron creator by @bcExpt1123

### Removed
- Delete repeated imports by @antoniorodr
- Delete logs when deleting cron job by @bcExpt1123
- Delete unnecessary code by @bcExpt1123

### New Contributors
* @bcExpt1123 made their first contribution

## [0.5.4] - 30.04.2026

### Fixed
- Fix error with the release package by @antoniorodr

## [0.5.3] - 29.04.2026

### Changed
- Update mirror workflow by @antoniorodr
- Update docs and tests workflows by @antoniorodr
- Update cliff config by @antoniorodr
- Update release and tests workflows by @antoniorodr

### Fixed
- Notify once when disconnecting server by @DragunovX16

### Removed
- Delete project explanation file by @antoniorodr
- Remove unreachable line by @DragunovX16

### New Contributors
* @DragunovX16 made their first contribution

## [0.5.2] - 19.04.2026

### Added
- Add typing to tests by @antoniorodr
- Add more test on CronDeleteConfirmation by @RunningKuma
- Add more test about CronSSHModal by @RunningKuma
- Add terminal trove badge local by @antoniorodr
- Add README for recording real GIFs in docs/images by @bitloi
- Add favicon to zensical docs by @antoniorodr
- Add nix flake by @antoniorodr

### Changed
- Merge branch 'release/workflows' by @antoniorodr
- Change release workflow action by @antoniorodr
- Update changelog using git-cliff by @antoniorodr
- Merge branch 'release/workflows' by @antoniorodr
- Update uploade-release version by @antoniorodr
- Merge branch 'release/workflows' by @antoniorodr
- Merge branch 'release/workflows' by @antoniorodr
- Update write permissions by @antoniorodr
- Update dependencies to the last version by @antoniorodr
- Update release workflow to include git-cliff by @antoniorodr
- Update gitignore with scripts by @antoniorodr
- Create cliff config to use with git-cliff by @antoniorodr
- Update changelog with git-cliff by @antoniorodr
- Merge pull request #38 from RunningKuma/feat/test_complement by @antoniorodr in [#38](https://github.com/antoniorodr/cronboard/pull/38)
- Consolidate test setup by moving helper functions to conftest.py by @RunningKuma
- Merge branch 'main' into feat/test_complement by @RunningKuma
- Move `create_event` to `confetst` to reduce duplidcation in test. by @RunningKuma
- Reduce repeated setup in modal tests by @RunningKuma
- Fix the test to keep it DRY by @RunningKuma
- Update terminal trove badge from readme by @antoniorodr
- Delete unused assets (logo and terminal trove) by @antoniorodr
- Delete logo from readme by @antoniorodr
- Delete back to top from readme by @antoniorodr
- Update readme by @antoniorodr
- Update logo size by @antoniorodr
- Delete extra readme.html by @antoniorodr
- Update readme by @antoniorodr
- Update readme with icons by @antoniorodr
- Update license on pyproject by @antoniorodr
- Update readme by @antoniorodr
- Update release and tests workflow by @antoniorodr
- Update readme by @antoniorodr
- Update license by @antoniorodr
- Update release workflow by @antoniorodr
- Update notify job on PR workflow by @antoniorodr
- Merge branch 'docs/issue-32-improve-documentation' by @antoniorodr
- Replace gif placeholders for good ones by @antoniorodr in [#34](https://github.com/antoniorodr/cronboard/pull/34)
- Improve documentation with detailed explanations and GIF examples by @bitloi
- Create the necessary files and workflows for the no autopilot action by @antoniorodr
- Edit docs workflow by @antoniorodr
- Update docs workflow by @antoniorodr
- Update readme by @antoniorodr
- Update pyproject and uv.lock by @antoniorodr
- Move project_explanation to root by @antoniorodr
- Create zensical documentation by @antoniorodr
- Create workflow to publish the documentation to Zensical by @antoniorodr
- Fix typo on readme file by @antoniorodr
- Update readme with nix installation by @antoniorodr
- Update flake and pyproject by @antoniorodr
- Update nix flake and create nix workflow by @antoniorodr
- Update release workflow by @antoniorodr
- Update changelog links by @antoniorodr

### Fixed
- Fix wrong year for Terminal Trove Tool of the week by @antoniorodr
- Fix a typo by @antoniorodr

### Removed
- Delete changelog commit by @antoniorodr

### New Contributors
* @RunningKuma made their first contribution
* @bitloi made their first contribution

## [0.5.1] - 06.03.2026

### Added
- Add release workflow by @antoniorodr
- Add pytest-mock to the uv.lock file and contributing by @antoniorodr

### Changed
- Update changelog and pyproject by @antoniorodr
- Update workflows to add telegram notification by @antoniorodr
- Move stale.yml into workflows by @antoniorodr
- Update app fixture to mock cronboard app by @antoniorodr
- Create github actions for testing PR and merge by @antoniorodr
- Update uv.lock by @antoniorodr
- Move the tests to the root by @antoniorodr
- Refactor the test file into multiple files by module by @antoniorodr
- Move dev dependencies to "dev" dependency-groups by @antoniorodr
- Update readme and contributing by @antoniorodr
- Update pyproject for coverage by @antoniorodr

## [0.5.0] - 04.03.2026

### Added
- Add q as an additional way to close app by @Zaloog
- Add clear search binding by @antoniorodr
- Add next and prev match on check_action by @antoniorodr

### Changed
- Update changelog and pyproject by @antoniorodr
- Merge branch 'lg/fix-app-closing-on-modal' by @antoniorodr in [#27](https://github.com/antoniorodr/cronboard/pull/27)
- Fix closing not working on modal screens by @Zaloog
- Merge branch 'feat/search' by @antoniorodr
- Delete unused imports by @antoniorodr
- Modify tests to use the parameter app by @antoniorodr
- Create conftest with pytest configuration by @antoniorodr
- Merge branch 'feat/search' by @antoniorodr
- Update readme with search function by @antoniorodr
- Merge branch 'feat/search' by @antoniorodr
- Update CronTable to fetch the search term from CronInputSearch by @antoniorodr
- Create new modal CronInputSearch to search cronjobs by @antoniorodr
- Update tcss to style the new CronInputSearch modal by @antoniorodr

## [0.4.3] - 23.02.2026

### Added
- Add escape binding also to ModalDeleteScreen by @Zaloog
- Added escape binding to close ModalScreen by @Zaloog
- Add workflow for mirroring by @antoniorodr

### Changed
- Update changelog and pyproject for the new version by @antoniorodr
- Fix format after merge by @antoniorodr
- Merge branch 'lg/fix-error-on-empty-edit' by @antoniorodr in [#23](https://github.com/antoniorodr/cronboard/pull/23)
- Adjusted Binding visibility by @Zaloog
- Fix format after merging by @antoniorodr
- Merge branch 'lg/close-modal-on-escape' by @antoniorodr in [#22](https://github.com/antoniorodr/cronboard/pull/22)
- Undo license change. Back to MIT. by @antoniorodr
- Update LICENSE to Apache 2.0 non AI by @antoniorodr
- Delete aur workflow by @antoniorodr

## [0.4.2] - 17.02.2026

### Added
- Add editorconfig file to the project by @antoniorodr
- Add new info to CONTRIBUTING.md by @antoniorodr

### Changed
- Update version pyproject by @antoniorodr
- Merge pull request #19 from antoniorodr/upt/dependencies by @antoniorodr in [#19](https://github.com/antoniorodr/cronboard/pull/19)
- Update dependencies by @antoniorodr
- Merge pull request #18 from antoniorodr/feat/editorconfig by @antoniorodr in [#18](https://github.com/antoniorodr/cronboard/pull/18)
- Update PKGBUILD and SRCINFO by @antoniorodr
- Update Changelog by @antoniorodr

## [0.4.1] - 09.02.2026

### Added
- Add stale.yml to automate closing and stale status by @antoniorodr

### Changed
- Change changelog and pyproject by @antoniorodr
- Update readme with the new bottle/formula by @antoniorodr
- Update readme to correctly show project size by @antoniorodr

### Fixed
- Validate host input in Add Server by @it-education-md in [#17](https://github.com/antoniorodr/cronboard/pull/17)

### New Contributors
* @it-education-md made their first contribution in [#17](https://github.com/antoniorodr/cronboard/pull/17)

## [0.4.0] - 11.11.2025

### Added
- Add autocompletion when creating cron jobs by @antoniorodr
- Add completion for three parts by @Zaloog
- Add initial autocompleter for command input by @Zaloog

### Changed
- Merge branch 'lg/create-command-autocompleter' by @antoniorodr in [#14](https://github.com/antoniorodr/cronboard/pull/14)
- Update gitignore by @antoniorodr
- Change banner and demo folder path by @antoniorodr
- Change link on Terminal Trove badge by @antoniorodr
- Update README: Terminal Trove tool of the week by @antoniorodr

### Fixed
- Fixing license metadata in pyproject.toml and add .gitignore file by @micisse in [#13](https://github.com/antoniorodr/cronboard/pull/13)

### Removed
- Remove unused dependencies and cleaned gitignore by @Zaloog

### New Contributors
* @Zaloog made their first contribution
* @micisse made their first contribution in [#13](https://github.com/antoniorodr/cronboard/pull/13)

## [0.3.1] - 24.10.2025

### Added
- Add documentation file in markdown by @antoniorodr

### Changed
- Update PKGBUILD and pyproject by @antoniorodr
- Change colors, identificator label and pause/delete/edit algorithm by @antoniorodr
- Update CONTRIBUTING file by @antoniorodr
- Update CONTRIBUTING.md file by @antoniorodr

## [0.3.0] - 22.10.2025

### Added
- Added possibility to choose crontab user by @antoniorodr
- Add sponsorship badget on README by @antoniorodr

### Changed
- Update PKGBUILD by @antoniorodr
- Update README file by @antoniorodr
- Create test file by @antoniorodr
- Merge pull request #9 from antoniorodr/antoniorodr-patch-1 by @antoniorodr in [#9](https://github.com/antoniorodr/cronboard/pull/9)
- Set GitHub Sponsors username to 'antoniorodr' by @antoniorodr
- Update README by @antoniorodr

## [0.2.2] - 17.10.2025

### Changed
- Change to behold the special expressions as it is when saving the cronjob by @antoniorodr
- Update README with new logo by @antoniorodr
- Update readme by @antoniorodr

## [0.2.1] - 17.10.2025

### Changed
- Update README for SSH by @antoniorodr
- Update PKGBUILD by @antoniorodr
- Update gif on README by @antoniorodr
- Update PKGBUILD and SRCINFO by @antoniorodr

### Fixed
- Fix tomlkit dependency and add support for special strings (@weekly etc) by @antoniorodr

## [0.2.0] - 15.10.2025

### Added
- Add .SRCINFO file to AUR by @antoniorodr

### Changed
- Merge branch 'servers_bookmarks' by @antoniorodr
- Redesign ssh connections tab by @antoniorodr
- Update README by @antoniorodr
- Create pkgbuild and workflow by @antoniorodr

## [0.1.2] - 13.10.2025

### Added
- Add ssh connection using ssh key by @antoniorodr
- Add bug and feature request templates by @antoniorodr
- Add changelog by @antoniorodr

### Changed
- Update asciinema gif by @antoniorodr
- Update readme with uv installation by @antoniorodr
- Fix CronBoard folder casing to lowercase by @antoniorodr
- Update readme with demo by @antoniorodr
- Change version function by @antoniorodr
- Small fix in version by @antoniorodr
- Update readme by @antoniorodr

## [0.1.1] - 11.10.2025

### Changed
- V0.1.1 release by @antoniorodr
- Update pyproject by @antoniorodr
- Update readme by @antoniorodr
- Update pyproject by @antoniorodr
- Update readme by @antoniorodr
- Change dependencies by @antoniorodr
- Update pyproject by @antoniorodr
- Project structure update by @antoniorodr
- Change email in code of conduct by @antoniorodr

## [0.1.0] - 10.10.2025

### Added
- Add SSH connection by @antoniorodr
- Add refresh after creation, edit and deletion of cronjobs by @antoniorodr
- Add different markdown files by @antoniorodr

### Changed
- Update readme by @antoniorodr
- Refactor by @antoniorodr
- Refactor cron parsing by @antoniorodr
- Create edit option and update readme by @antoniorodr
- Create dynamic tabs, deletion, creation and deactivation for cronjobs by @antoniorodr
- Initial commit by @antoniorodr

### Fixed
- Fix bug with error labels in ssh connection by @antoniorodr
- Fix cronjobs deletion on ssh by @antoniorodr
- Fix persistance creation in ssh by @antoniorodr

### New Contributors
* @antoniorodr made their first contribution

[0.7.1]: https://github.com/antoniorodr/cronboard/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/antoniorodr/cronboard/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/antoniorodr/cronboard/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/antoniorodr/cronboard/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/antoniorodr/cronboard/compare/v0.5.4...v0.6.0
[0.5.4]: https://github.com/antoniorodr/cronboard/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/antoniorodr/cronboard/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/antoniorodr/cronboard/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/antoniorodr/cronboard/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/antoniorodr/cronboard/compare/v0.4.3...v0.5.0
[0.4.3]: https://github.com/antoniorodr/cronboard/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/antoniorodr/cronboard/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/antoniorodr/cronboard/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/antoniorodr/cronboard/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/antoniorodr/cronboard/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/antoniorodr/cronboard/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/antoniorodr/cronboard/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/antoniorodr/cronboard/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/antoniorodr/cronboard/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/antoniorodr/cronboard/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/antoniorodr/cronboard/compare/v0.1.0...v0.1.1

<!-- generated by git-cliff -->
