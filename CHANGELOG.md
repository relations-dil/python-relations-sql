# Changelog

All notable changes to python-relations-sql are recorded here, newest first. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

## [0.6.9] - 2026-06-08

- Added `collate_attr_query` to `SOURCE`, which turns sibling-attribute criteria on many-to-many ties into joins on the tie and sibling tables in the outer query.
- Queries with such joins set `_distinct` on the model so counts and retrieves de-duplicate results.
- Pinned `relations-dil` to the 0.6.15 release.

## [0.6.8] - 2026-06-06

- Added a `SOURCE` mixin in `relations_sql.source` with `collate_ties` and `collate_ties_query`, which resolve many-to-many `has`, `any` and `all` criteria (and `not_` variants) as `IN` subqueries so the database does the work.
- Table DDL now skips fields with no `store` (such as many-to-many tie fields) when creating, adding, modifying and dropping columns.
- Updated the Dockerfile, requirements and setup so Docker can install from git.

## [0.6.7] - 2022-11-25

- Replaced the `relations` dependency with `overscore`, using `overscore.parse` to split column paths.
- Pinned `overscore==0.1.1` as the install requirement.

## [0.6.6] - 2022-08-05

- Added PyPI publishing: `PYPI.md` long description with usage examples, `LICENSE.txt`, and `testpypi` and `pypi` Make targets.
- Dropped the git install of `relations` from the Dockerfile and setup step.

## [0.6.5] - 2022-03-14

- Simplified how `TABLE` DDL picks the store and schema from the migration and definition, so a missing migration or definition no longer causes errors.
- Bumped the `relations` requirement to 0.6.9.

## [0.6.4] - 2022-03-13

- Bumped the `relations` requirement to 0.6.8; no library code changed.

## [0.6.3] - 2022-02-18

- Renamed `QUERY.labels` to `QUERY.titles`, matching the `titles` method on the model.
- Bumped the `relations` requirement to 0.6.7.

## [0.6.2] - 2021-11-21

- Renamed the package to `python-relations-sql` and moved the repository to the `relations-dil` organization in preparation for PyPI.
- Pointed the `relations` requirement at the new repository, version 0.6.6.

## [0.6.1] - 2021-11-13

- Bumped the `relations` dependency to 0.6.5 in the Makefile and requirements.

## [0.6.0] - 2021-11-12

- Extended DDL with auto-increment (`AUTO`) columns, primary keys, `DROP ... IF EXISTS`, and schema and store renames, with `store` used as the base column name.
- Added extracted JSON-path columns in DDL, `JSONNULL`, a `jsonify` option on criterions, and a reverse option; `split` and `walk` moved onto `SQL`.
- Clauses `FIELDS`, `FROM`, `WHERE`, `LIMIT` and `VALUES` now accept a dict, `LIMIT` generates `OFFSET` properly, and `VALUES` columns are bound to the `INSERT` query columns.
- Renamed `COLUMNNAME` and `TABLENAME` to `COLUMN_NAME` and `TABLE_NAME` and the clause `statement` attribute to `query`; `DELETE` takes a `TABLE_NAME`.

## [0.5.3] - 2021-09-14

- Added DDL support with new `DDL`, `COLUMN`, `INDEX` and `TABLE` classes for generating create, add, modify and drop statements from migration definitions.
- Renamed `FIELD` and `TABLE` expressions to `COLUMNNAME` and `TABLENAME` and renamed the results clause back to `FIELDS`; `VALUES` uses `COLUMNS` instead of `FIELDS`.

## [0.5.2] - 2021-09-09

- Added indented SQL output: `generate()` on clauses, criteria, criterions and queries now takes `indent`, `count` and `pad` arguments to produce multi-line SQL.
- Renamed the `FIELDS` clause to `RESULTS` for this release.
- `VALUES` now generates one parenthesized row per expression using the new indentation.

## [0.5.1] - 2021-09-06

- `INSERT` and related queries now accept an already-built `TABLE` or `FIELDS` clause object instead of always rebuilding it, so cloned queries keep the classes passed in.

## [0.5.0] - 2021-09-05

- Started depending on the `relations` package, and `FIELD` path parsing now uses `relations.Field.split` instead of its own parser.
- Updated the Dockerfile, Makefile and requirements to install `relations` from git.

## [0.4.0] - 2021-09-04

- Made `LIKE` match anywhere in the value by default, which removed the `MID` criterion and the `mid` operand.
- `START` and `END` now override the default wildcards of `LIKE`.

## [0.3.3] - 2021-09-04

- Added `START`, `MID` and `END` criterions for prefix, contains and suffix `LIKE` matching, usable as the `start`, `mid` and `end` operands.
- Criterion operands became format strings such as `%s=%s`, and `SETS` now derives from `CRITERION`.

## [0.3.2] - 2021-09-04

- Replaced the separate negated classes (`NOTHAS`, `NOTANY`, `NOTALL`, `NE`, `NOTLIKE`, `NOTIN`) with a general `invert` option on criterions and a `not_` operand prefix such as `field__not_in`.
- Criterions without an inverse form raise `SQLError` when inverted, or are wrapped in `NOT`.

## [0.3.1] - 2021-09-04

- Added `set()` and call syntax on `NAME`, `TABLE` and `FIELD` expressions so a name, schema, table or other setting can be changed after creation.

## [0.3.0] - 2021-09-04

- Reworked criterions and criteria: keyword-argument handling (`KWARG`/`KWARGS`) moved from `CRITERIA` to `CLAUSE`.
- Added set-comparison criteria `HAS`, `NOTHAS`, `ANY`, `NOTANY`, `ALL` and `NOTALL`, selectable through the `OP` operand lookup.

## [0.2.0] - 2021-09-01

- Renamed the `statement` module and `STATEMENT` classes to `query` and `QUERY`, with `SELECT` and `INSERT` as `QUERY` subclasses.
- Expanded the README.

## [0.1.0] - 2021-08-31

- Initial release of the abstract SQL builder: `SQL`, `EXPRESSION`, `CRITERION` and `CRITERIA` building blocks plus statement classes.
- Included query clauses `OPTIONS`, `FIELDS`, `FROM`, `WHERE`, `GROUP_BY`, `HAVING`, `ORDER_BY`, `LIMIT`, `SET` and `VALUES`, with `LIMIT` accepting a total and offset.
- Packaged with a Makefile, Dockerfile, Jenkinsfile, README and unit tests.
