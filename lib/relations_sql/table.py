"""–
Module for Column DDL
"""

# pylint: disable=unused-argument

import relations_sql


class TABLE(relations_sql.DDL):
    """
    TABLE DDL
    """

    NAME = None
    COLUMN = None
    INDEX = None
    UNIQUE = None

    INDEXES = None

    SCHEMA = None
    RENAME = None

    def name(self, definition=False):
        """
        Generate a quoted name, with store as the default
        """

        state = self.definition if definition or "store" not in self.migration else self.migration
        name = state['store']

        table = self.NAME(name, schema=state.get("schema"))

        table.generate()

        return table.sql

    def create(self, indent=0, count=0, pad=' ', **kwarg): # pylint: disable=too-many-locals
        """
        CREATE DLL
        """

        inside = []

        columns = []
        indexes = []

        for migration in self.migration["fields"]:
            if "inject" in migration:
                continue
            columns.append(self.COLUMN(migration=migration))
            if "extract" in migration:
                for extract in sorted(migration["extract"]):
                    store = migration.get("store", migration["name"])
                    columns.append(self.COLUMN(store=f"{store}_{extract}", kind=migration["extract"][extract]))

        table = {} if self.INDEXES else {"table": self.migration["name"], "schema": self.migration.get("schema")}

        for index in sorted(self.migration.get("index", {})):
            indexes.append(self.INDEX(name=index, columns=self.migration["index"][index], **table))

        for index in sorted(self.migration.get("unique", {})):
            indexes.append(self.UNIQUE(name=index, columns=self.migration["unique"][index], **table))

        self.express(columns, inside, indent=indent, count=count+1, pad=pad)

        if self.INDEXES:
            self.express(indexes, inside, indent=indent, count=count+1, pad=pad)

        one = pad * indent
        migration = pad * (count * indent)
        next = migration + one
        line = "\n" if indent else ""
        delimitter = f",{line}{next}"

        sql = [f"CREATE TABLE IF NOT EXISTS {self.name()} ({line}{next}{delimitter.join(inside)}{line})"]

        if not self.INDEXES:
            self.express(indexes, sql, indent=indent, count=count, pad=pad)

        delimitter = f";\n\n{migration}"

        self.sql = f"{delimitter.join(sql)};\n"

    def add(self, **kwargs):
        """
        ADD DLL
        """

        self.create(**kwargs)

    def field(self, name):
        """
        Looks up a field definition
        """

        for field in self.definition["fields"]:
            if field["name"] == name:
                return field

        raise relations_sql.SQLError(self, f"field {name} not found")

    def fields_add(self, columns):
        """
        Process added fields into columns
        """

        for migration in self.migration.get("fields", {}).get("add", {}):

            if "inject" in migration:
                continue

            columns.append(self.COLUMN(migration=migration, added=True))

            if "extract" in migration:
                for extract in sorted(migration["extract"]):
                    store = migration.get("store", migration["name"])
                    columns.append(self.COLUMN(store=f"{store}_{extract}", kind=migration["extract"][extract], added=True))

    def fields_change(self, columns):
        """
        Process changed fields into columns
        """

        for field in self.migration.get("fields", {}).get("change", {}):

            migration = self.migration["fields"]["change"][field]
            definition = self.field(field)

            if "inject" in definition:
                continue

            if any(attr in migration for attr in ["name", "store", "kind", "default", "none"]):
                columns.append(self.COLUMN(migration=migration, definition=definition))

            if "extract" in migration:

                for extract in sorted(migration["extract"]):
                    if extract not in definition.get("extract"):
                        columns.append(self.COLUMN(
                            migration={
                                "store": f"{migration.get('store', field)}_{extract}",
                                "kind": migration["extract"][extract]
                            },
                            added=True
                        ))
                    elif migration["extract"][extract] != definition["extract"][extract]:
                        columns.append(self.COLUMN(
                            migration={
                                "store": f"{migration.get('store', field)}_{extract}",
                                "kind": migration["extract"][extract]
                            },
                            definition={
                                "store": f"{definition['store']}_{extract}",
                                "kind": definition["extract"][extract]
                            }
                        ))

                for extract in sorted(definition.get("extract", {})):
                    if extract not in migration["extract"]:
                        columns.append(self.COLUMN(
                            definition={
                                "store": f"{definition['store']}_{extract}",
                                "kind": definition["extract"][extract]
                            }
                        ))

            elif "extract" in definition and migration.get('store', field) != definition['store']:

                for extract in sorted(definition["extract"]):
                    columns.append(self.COLUMN(
                        migration={
                            "store": f"{migration.get('store', field)}_{extract}",
                            "kind": definition["extract"][extract]
                        },
                        definition={
                            "store": f"{definition['store']}_{extract}",
                            "kind": definition["extract"][extract]
                        }
                    ))

    def fields_remove(self, columns):
        """
        Process removed fields into columns
        """

        for field in self.migration.get("fields", {}).get("remove", []):

            definition = self.field(field)

            if "inject" in definition:
                continue

            columns.append(self.COLUMN(definition=definition))

            if "extract" in definition:
                for extract in sorted(definition["extract"]):
                    columns.append(self.COLUMN(
                        definition={
                            "store": f"{definition['store']}_{extract}",
                            "kind": definition["extract"][extract]
                        }
                    ))

    def indexes_modify(self, indexes, table, unique=False):
        """
        Process modified indexes
        """

        index, INDEX = ("unique", self.UNIQUE) if unique else ("index", self.INDEX)

        for name in self.migration.get(index, {}).get("add", {}):
            indexes.append(INDEX(
                migration={
                    "name": name,
                    "columns": self.migration[index]["add"][name],
                    "table": table
                }
            ))

        for name in self.migration.get(index, {}).get("rename", {}):
            indexes.append(INDEX(
                migration={
                    "name": self.migration[index]["rename"][name],
                    "table": table
                },
                definition={
                    "name": name,
                    "table": table
                }
            ))

        for name in self.migration.get(index, {}).get("remove", {}):
            indexes.append(INDEX(
                definition={
                    "name": name,
                    "table": table
                }
            ))

    def modify(self, indent=0, count=0, pad=' ', **kwargs):
        """
        MODIFY DLL
        """

        sql = []

        if "schema" in self.migration and self.SCHEMA:
            sql.append(self.SCHEMA % (self.name(definition=True), self.quote(self.definition.get("schema"))))

        if "name" in self.migration and self.RENAME:
            sql.append(self.RENAME % (self.name(definition=True), self.quote(self.name())))

        inside = []

        columns = []
        indexes = []

        self.fields_add(columns)
        self.fields_change(columns)
        self.fields_remove(columns)

        table = {} if self.INDEXES else {
            "name": self.migration.get("name", self.definition["name"]),
            "schema": self.migration.get("schema", self.definition.get("schema"))
        }

        self.indexes_modify(indexes, table)
        self.indexes_modify(indexes, table, unique=True)

        one = pad * indent
        current = pad * (count * indent)
        next = current + one
        line = "\n" if indent else ""
        delimitter = f",{line}{next}"

        self.express(columns, inside, indent=indent, count=count+1, pad=pad)

        if self.INDEXES:
            self.express(indexes, inside, indent=indent, count=count+1, pad=pad)

        if inside:
            sql.append(f"ALTER TABLE {self.name()}{line or ' '}{next}{delimitter.join(inside)}")

        if not self.INDEXES:
            self.express(indexes, sql, indent=indent, count=count, pad=pad)

        delimitter = f";\n\n{current}"

        self.sql = f"{delimitter.join(sql)};\n"

    def drop(self, **kwargs):
        """
        DROP DLL
        """

        self.sql = f"DROP TABLE {self.name(definition=True)};\n"