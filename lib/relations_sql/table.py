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
    STORE = None
    PRIMARY = None

    def name(self, state="migration"):
        """
        Generate a quoted name, with table as the default
        """

        if isinstance(state, str):
            state = {
                "name": state,
                "schema": state
            }

        definition_store = (self.definition or {}).get("store")
        definition_schema = (self.definition or {}).get("schema")

        migration_store = (self.migration or {}).get("store")
        migration_schema = (self.migration or {}).get("schema")

        if state["name"] == "migration":
            store = migration_store or definition_store
        else:
            store = definition_store or migration_store

        if state["schema"] == "migration":
            schema = migration_schema or definition_schema
        else:
            schema = definition_schema or migration_schema

        table = self.NAME(store, schema=schema)

        table.generate()

        return table.sql

    def create(self, indent=0, count=0, pad=' ', **kwargs): # pylint: disable=too-many-locals
        """
        CREATE DLL
        """

        inside = []

        columns = []
        indexes = []

        for migration in self.migration["fields"]:
            if "inject" in migration or not migration["store"]:
                continue
            columns.append(self.COLUMN(migration=migration))
            if "extract" in migration:
                for extract in sorted(migration["extract"]):
                    store = migration["store"]
                    columns.append(self.COLUMN(store=f"{store}__{extract}", kind=migration["extract"][extract]))

        table = {} if self.INDEXES else {"table": self.migration["store"], "schema": self.migration.get("schema")}

        if self.migration.get('id') is not None and self.PRIMARY:
            columns.append(relations_sql.SQL(self.PRIMARY % self.quote(self.migration['id'])))

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

            if "inject" in migration or not migration["store"]:
                continue

            columns.append(self.COLUMN(migration=migration, added=True))

            if "extract" in migration:
                for extract in sorted(migration["extract"]):
                    store = migration.get("store", migration["name"])
                    columns.append(self.COLUMN(store=f"{store}__{extract}", kind=migration["extract"][extract], added=True))

    def fields_change(self, columns):
        """
        Process changed fields into columns
        """

        for field in self.migration.get("fields", {}).get("change", {}):

            migration = self.migration["fields"]["change"][field]
            definition = self.field(field)

            if "inject" in definition or not definition["store"]:
                continue

            if any(attr in migration for attr in ["name", "store", "kind", "default", "none"]):
                columns.append(self.COLUMN(migration=migration, definition=definition))

            if "extract" in migration:

                for extract in sorted(migration["extract"]):
                    if extract not in definition.get("extract"):
                        columns.append(self.COLUMN(
                            migration={
                                "store": f"{migration.get('store', field)}__{extract}",
                                "kind": migration["extract"][extract]
                            },
                            added=True
                        ))
                    elif migration["extract"][extract] != definition["extract"][extract]:
                        columns.append(self.COLUMN(
                            migration={
                                "store": f"{migration.get('store', field)}__{extract}",
                                "kind": migration["extract"][extract]
                            },
                            definition={
                                "store": f"{definition['store']}__{extract}",
                                "kind": definition["extract"][extract]
                            }
                        ))

                for extract in sorted(definition.get("extract", {})):
                    if extract not in migration["extract"]:
                        columns.append(self.COLUMN(
                            definition={
                                "store": f"{definition['store']}__{extract}",
                                "kind": definition["extract"][extract]
                            }
                        ))

            elif "extract" in definition and migration.get('store', field) != definition['store']:

                for extract in sorted(definition["extract"]):
                    columns.append(self.COLUMN(
                        migration={
                            "store": f"{migration.get('store', field)}__{extract}",
                            "kind": definition["extract"][extract]
                        },
                        definition={
                            "store": f"{definition['store']}__{extract}",
                            "kind": definition["extract"][extract]
                        }
                    ))

    def fields_remove(self, columns):
        """
        Process removed fields into columns
        """

        for field in self.migration.get("fields", {}).get("remove", []):

            definition = self.field(field)

            if "inject" in definition or not definition["store"]:
                continue

            columns.append(self.COLUMN(definition=definition))

            if "extract" in definition:
                for extract in sorted(definition["extract"]):
                    columns.append(self.COLUMN(
                        definition={
                            "store": f"{definition['store']}__{extract}",
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

    def schema(self, sql):
        """
        Change the schema
        """

        if self.SCHEMA:
            sql.append(self.SCHEMA % (self.name(state="definition"), self.quote(self.migration["schema"])))
        else:
            raise relations_sql.SQLError(self, "schema change not supported")

    def store(self, sql):
        """
        Change the schema
        """

        if self.STORE:
            sql.append(self.STORE % (self.name(state={"name": "definition", "schema": "migration"}), self.name()))
        else:
            raise relations_sql.SQLError(self, "store change not supported")

    def modify(self, indent=0, count=0, pad=' ', **kwargs):
        """
        MODIFY DLL
        """

        sql = []

        if "schema" in self.migration:
            self.schema(sql)

        if "store" in self.migration:
            self.store(sql)

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

        self.sql = f"DROP TABLE IF EXISTS {self.name(state='definition')};\n"
