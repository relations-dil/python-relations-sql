import unittest
import unittest.mock

import test_ddl
import test_expression
import test_column
import test_index

import relations
import relations_sql


class Simple(relations.Model):
    id = int
    name = str

class Meta(relations.Model):
    id = int
    name = str
    flag = bool
    spend = float
    people = set
    stuff = list
    things = dict, {"extract": "for__0____1"}
    push = str, {"inject": "stuff___1__relations.io____1"},
    tied = str, {"store": False}

    INDEX = "spend"


class TABLE(test_ddl.DDL, relations_sql.TABLE):

    NAME = test_expression.TABLE_NAME
    COLUMN = test_column.COLUMN
    INDEX = test_index.INDEX
    UNIQUE = test_index.UNIQUE

    SCHEMA = "SCHEMA %s TO %s"
    STORE = "STORE %s TO %s"
    PRIMARY = "PRIMARY (%s)"

class INSIDE(TABLE):

    INDEXES = True

class OUTSIDE(TABLE):

    INDEXES = False

class LOCKED(TABLE):

    SCHEMA = None
    STORE = None

class TestTABLE(unittest.TestCase):

    maxDiff = None

    def test_name(self):

        ddl = TABLE(schema="people", name="stuff", definition={"schema": "persons", "name": "things"})

        self.assertEqual(ddl.name(), """`people`.`stuff`""")
        self.assertEqual(ddl.name(state="definition"), """`persons`.`things`""")
        self.assertEqual(ddl.name(state={"name": "definition", "schema": "migration"}), """`people`.`things`""")

    def test_create(self):

        ddl = INSIDE(Simple.thy().define())
        ddl.args = []

        ddl.create()
        self.assertEqual(ddl.sql, """CREATE TABLE IF NOT EXISTS `simple` (`id` INT,`name` STR NOT NULL,PRIMARY (`id`),UNIQUE `name` (`name`));\n""")

        ddl = OUTSIDE(**Meta.thy().define())
        ddl.args = []

        ddl.create(indent=2)
        self.assertEqual(ddl.sql, """CREATE TABLE IF NOT EXISTS `meta` (
  `id` INT,
  `name` STR NOT NULL,
  `flag` BOOL,
  `spend` FLOAT,
  `people` JSON NOT NULL,
  `stuff` JSON NOT NULL,
  `things` JSON NOT NULL,
  `things__for__0____1` STR AS `things`#>>'$."for"[0]."1"',
  PRIMARY (`id`)
);

CREATE INDEX `meta_spend` ON `meta` (`spend`);

CREATE UNIQUE `meta_name` ON `meta` (`name`);
""")

    def test_add(self):

        ddl = INSIDE(Simple.thy().define())
        ddl.args = []

        ddl.add()
        self.assertEqual(ddl.sql, """CREATE TABLE IF NOT EXISTS `simple` (`id` INT,`name` STR NOT NULL,PRIMARY (`id`),UNIQUE `name` (`name`));\n""")

        ddl = OUTSIDE(**Meta.thy().define())
        ddl.args = []

        ddl.add(indent=2)
        self.assertEqual(ddl.sql, """CREATE TABLE IF NOT EXISTS `meta` (
  `id` INT,
  `name` STR NOT NULL,
  `flag` BOOL,
  `spend` FLOAT,
  `people` JSON NOT NULL,
  `stuff` JSON NOT NULL,
  `things` JSON NOT NULL,
  `things__for__0____1` STR AS `things`#>>'$."for"[0]."1"',
  PRIMARY (`id`)
);

CREATE INDEX `meta_spend` ON `meta` (`spend`);

CREATE UNIQUE `meta_name` ON `meta` (`name`);
""")

    def test_field(self):

        ddl = TABLE(definition={
            "name": "yep",
            "fields": [
                {
                    "name": "yep"
                }
            ]
        })

        self.assertEqual(ddl.field("yep"), {"name": "yep"})

        self.assertRaisesRegex(relations_sql.SQLError, "field nope not found", ddl.field, "nope")

    def test_fields_add(self):

        ddl = TABLE(migration={
            "name": "yep",
            "fields": {
                "add": Meta.thy().define()["fields"][-3:]
            }
        })

        columns = []

        ddl.fields_add(columns)

        self.assertEqual(len(columns), 2)
        self.assertEqual(columns[0].migration["name"], "things")
        self.assertEqual(columns[0].migration["kind"], "dict")
        self.assertTrue(columns[0].added)
        self.assertEqual(columns[1].migration["store"], "things__for__0____1")
        self.assertEqual(columns[1].migration["kind"], "str")
        self.assertTrue(columns[1].added)

    def test_fields_change(self):

        ddl = TABLE(
            migration={
                "fields": {
                    "change": {
                        "push": {
                            "name": "push",
                            "store": "pull"
                        },
                        "spend": {
                            "default": 1.25
                        },
                        "things": {
                            "store": "thingies"
                        },
                        "tied": {
                            "name": "ties"
                        }
                    }
                }
            },
            definition={
                "name": "yep",
                "fields": Meta.thy().define()["fields"]
            }
        )

        columns = []

        ddl.fields_change(columns)
        self.assertEqual(len(columns), 3)
        self.assertEqual(columns[0].migration["default"], 1.25)
        self.assertEqual(columns[1].migration["store"], "thingies")
        self.assertEqual(columns[1].definition["store"], "things")
        self.assertEqual(columns[2].migration["store"], "thingies__for__0____1")
        self.assertEqual(columns[2].definition["store"], "things__for__0____1")

        ddl = TABLE(
            migration={
                "fields": {
                    "change": {
                        "things": {
                            "extract": {
                                "for__1____0": "str"
                            }
                        }
                    }
                }
            },
            definition={
                "name": "yep",
                "fields": Meta.thy().define()["fields"]
            }
        )

        columns = []

        ddl.fields_change(columns)
        self.assertEqual(len(columns), 2)
        self.assertEqual(columns[0].migration["store"], "things__for__1____0")
        self.assertTrue(columns[0].added)
        self.assertIsNone(columns[0].definition)
        self.assertEqual(columns[1].definition["store"], "things__for__0____1")
        self.assertIsNone(columns[1].migration)

        ddl = TABLE(
            migration={
                "fields": {
                    "change": {
                        "things": {
                            "extract": {
                                "for__0____1": "float"
                            }
                        }
                    }
                }
            },
            definition={
                "name": "yep",
                "fields": Meta.thy().define()["fields"]
            }
        )

        columns = []

        ddl.fields_change(columns)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].migration["store"], "things__for__0____1")
        self.assertEqual(columns[0].migration["kind"], "float")
        self.assertEqual(columns[0].definition["store"], "things__for__0____1")
        self.assertEqual(columns[0].definition["kind"], "str")

    def test_fields_remove(self):

        ddl = TABLE(
            migration={
                "fields": {
                    "remove": [
                        "things",
                        "push",
                        "tied"
                    ]
                }
            },
            definition={
                "name": "yep",
                "fields": Meta.thy().define()["fields"]
            }
        )

        columns = []

        ddl.fields_remove(columns)
        self.assertEqual(len(columns), 2)
        self.assertIsNone(columns[0].migration)
        self.assertEqual(columns[0].definition["store"], "things")
        self.assertIsNone(columns[1].migration)
        self.assertEqual(columns[1 ].definition["store"], "things__for__0____1")

    def test_indexes_modify(self):

        ddl = TABLE(
            migration={
                "index": {
                    "add": {
                        "flag": ["flag"]
                    },
                    "remove": [
                        "price"
                    ]
                }
            },
            definition={
                "name": "yep",
                "index": Meta.thy().define()["index"]
            }
        )

        table = {"name": "space"}
        indexes = []

        ddl.indexes_modify(indexes, table)
        self.assertEqual(len(indexes), 2)
        self.assertIsInstance(indexes[0], test_index.INDEX)
        self.assertIsInstance(indexes[1], test_index.INDEX)
        self.assertIsNone(indexes[0].definition)
        self.assertEqual(indexes[0].migration["name"], "flag")
        self.assertEqual(indexes[0].migration["columns"], ["flag"])
        self.assertEqual(indexes[0].migration["table"]["name"], "space")
        self.assertIsNone(indexes[1].migration)
        self.assertEqual(indexes[1].definition["name"], "price")
        self.assertEqual(indexes[1].definition["table"]["name"], "space")

        ddl = TABLE(
            migration={
                "index": {
                    "rename": {
                        "price": "right"
                    }
                }
            },
            definition={
                "name": "yep",
                "index": Meta.thy().define()["index"]
            }
        )

        table = {"name": "space"}
        indexes = []

        ddl.indexes_modify(indexes, table)
        self.assertEqual(len(indexes), 1)
        self.assertIsInstance(indexes[0], test_index.INDEX)
        self.assertEqual(indexes[0].definition["name"], "price")
        self.assertEqual(indexes[0].migration["name"], "right")

        ddl = TABLE(
            migration={
                "unique": {
                    "add": {
                        "flag": ["flag"]
                    },
                    "remove": [
                        "name"
                    ]
                }
            },
            definition={
                "name": "yep",
                "unique": Meta.thy().define()["unique"]
            }
        )

        table = {"name": "space"}
        indexes = []

        ddl.indexes_modify(indexes, table, unique=True)
        self.assertEqual(len(indexes), 2)
        self.assertIsInstance(indexes[0], test_index.UNIQUE)
        self.assertIsInstance(indexes[1], test_index.UNIQUE)
        self.assertIsNone(indexes[0].definition)
        self.assertEqual(indexes[0].migration["name"], "flag")
        self.assertEqual(indexes[0].migration["columns"], ["flag"])
        self.assertEqual(indexes[0].migration["table"]["name"], "space")
        self.assertIsNone(indexes[1].migration)
        self.assertEqual(indexes[1].definition["name"], "name")
        self.assertEqual(indexes[1].definition["table"]["name"], "space")

        ddl = TABLE(
            migration={
                "unique": {
                    "rename": {
                        "name": "label"
                    }
                }
            },
            definition={
                "name": "yep",
                "unique": Meta.thy().define()["index"]
            }
        )

        table = {"name": "space"}
        indexes = []

        ddl.indexes_modify(indexes, table, unique=True)
        self.assertEqual(len(indexes), 1)
        self.assertIsInstance(indexes[0], test_index.UNIQUE)
        self.assertEqual(indexes[0].definition["name"], "name")
        self.assertEqual(indexes[0].migration["name"], "label")

    def test_schema(self):

        sql = []

        ddl = TABLE(
            migration={
                "name": "good",
                "schema": "dreaming"
            },
            definition={
                "name": "evil",
                "schema": "scheming"
            }
        )

        ddl.schema(sql)
        self.assertEqual(sql, ["""SCHEMA `scheming`.`evil` TO `dreaming`"""])

        ddl = LOCKED(
            migration={
                "name": "good",
                "schema": "dreaming"
            },
            definition={
                "name": "evil",
                "schema": "scheming"
            }
        )

        self.assertRaisesRegex(relations_sql.SQLError, "schema change not supported", ddl.schema, sql)

    def test_store(self):

        sql = []

        ddl = TABLE(
            migration={
                "name": "good",
                "schema": "dreaming"
            },
            definition={
                "name": "evil",
                "schema": "scheming"
            }
        )

        ddl.store(sql)
        self.assertEqual(sql, ["""STORE `dreaming`.`evil` TO `dreaming`.`good`"""])

        ddl = LOCKED(
            migration={
                "name": "good",
                "schema": "dreaming"
            },
            definition={
                "name": "evil",
                "schema": "scheming"
            }
        )

        self.assertRaisesRegex(relations_sql.SQLError, "store change not supported", ddl.store, sql)

    def test_modify(self):

        ddl = TABLE(
            migration={
                "name": "good",
                "schema": "dreaming"
            },
            definition={
                "name": "evil",
                "schema": "scheming"
            }
        )

        ddl.generate()
        self.assertEqual(ddl.sql, """SCHEMA `scheming`.`evil` TO `dreaming`;

STORE `dreaming`.`evil` TO `dreaming`.`good`;
""")
        self.assertEqual(ddl.args, [])

        ddl = TABLE(
            migration={
                "fields": {
                    "add": Meta.thy().define()["fields"][-3:]
                }
            },
            definition=Simple.thy().define()
        )

        ddl.generate()
        self.assertEqual(ddl.sql,
            """ALTER TABLE `simple` """
            """ADD `things` JSON NOT NULL,"""
            """ADD `things__for__0____1` STR AS `things`#>>'$."for"[0]."1"';\n""")
        self.assertEqual(ddl.args, [])

        ddl.generate(indent=2)
        self.assertEqual(ddl.sql, """ALTER TABLE `simple`
  ADD `things` JSON NOT NULL,
  ADD `things__for__0____1` STR AS `things`#>>'$."for"[0]."1"';
""")
        self.assertEqual(ddl.args, [])

        ddl = TABLE(
            migration={
                "fields": {
                    "change": {
                        "push": {
                            "name": "push",
                            "store": "pull"
                        },
                        "spend": {
                            "default": 1.25
                        },
                        "things": {
                            "store": "thingies"
                        }
                    }
                }
            },
            definition={
                "name": "yep",
                "fields": Meta.thy().define()["fields"]
            }
        )

        ddl.generate()
        self.assertEqual(ddl.sql,
            """ALTER TABLE `yep` """
            """SET DEFAULT `spend` AS 1.25,"""
            """STORE `things` AS `thingies`,"""
            """STORE `things__for__0____1` AS `thingies__for__0____1`,"""
            """KIND `thingies__for__0____1` AS STR;\n""")
        self.assertEqual(ddl.args, [])

        ddl = TABLE(
            migration={
                "fields": {
                    "change": {
                        "push": {
                            "name": "push",
                            "store": "pull"
                        },
                        "spend": {
                            "default": 1.25
                        },
                        "things": {
                            "store": "thingies"
                        }
                    }
                }
            },
            definition={
                "name": "yep",
                "fields": Meta.thy().define()["fields"]
            }
        )

        ddl.generate(indent=2)
        self.assertEqual(ddl.sql, """ALTER TABLE `yep`
  SET DEFAULT `spend` AS 1.25,
  STORE `things` AS `thingies`,
  STORE `things__for__0____1` AS `thingies__for__0____1`,
  KIND `thingies__for__0____1` AS STR;
""")
        self.assertEqual(ddl.args, [])

        ddl = TABLE(
            migration={
                "fields": {
                    "remove": [
                        "things",
                        "push"
                    ]
                }
            },
            definition={
                "name": "yep",
                "fields": Meta.thy().define()["fields"]
            }
        )

        ddl.generate()
        self.assertEqual(ddl.sql, """ALTER TABLE `yep` DROP `things`,DROP `things__for__0____1`;\n""")
        self.assertEqual(ddl.args, [])

        ddl = TABLE(
            migration={
                "fields": {
                    "remove": [
                        "things",
                        "push"
                    ]
                }
            },
            definition={
                "name": "yep",
                "fields": Meta.thy().define()["fields"]
            }
        )

        ddl.generate(indent=2)
        self.assertEqual(ddl.sql, """ALTER TABLE `yep`
  DROP `things`,
  DROP `things__for__0____1`;
""")
        self.assertEqual(ddl.args, [])

        ddl = INSIDE(
            migration={
                "index": {
                    "add": {
                        "flag": ["flag"]
                    },
                    "remove": [
                        "price"
                    ]
                },
                "unique": {
                    "add": {
                        "flag": ["flag"]
                    },
                    "remove": [
                        "name"
                    ]
                }
            },
            definition={
                "name": "yep",
                "index": Meta.thy().define()["index"],
                "unique": Meta.thy().define()["unique"]
            }
        )

        ddl.generate()
        self.assertEqual(ddl.sql,
            """ALTER TABLE `yep` """
            """CREATE INDEX `flag` (`flag`),"""
            """DROP INDEX `price`,"""
            """CREATE UNIQUE `flag` (`flag`),"""
            """DROP INDEX `name`;\n""")
        self.assertEqual(ddl.args, [])

        ddl.generate(indent=2)
        self.assertEqual(ddl.sql, """ALTER TABLE `yep`
  CREATE INDEX `flag` (`flag`),
  DROP INDEX `price`,
  CREATE UNIQUE `flag` (`flag`),
  DROP INDEX `name`;
""")
        self.assertEqual(ddl.args, [])

        ddl = OUTSIDE(
            migration={
                "index": {
                    "add": {
                        "flag": ["flag"]
                    },
                    "remove": [
                        "price"
                    ]
                },
                "unique": {
                    "add": {
                        "flag": ["flag"]
                    },
                    "remove": [
                        "name"
                    ]
                }
            },
            definition={
                "name": "yep",
                "index": Meta.thy().define()["index"],
                "unique": Meta.thy().define()["unique"]
            }
        )

        ddl.generate(indent=2)
        self.assertEqual(ddl.sql, """CREATE INDEX `yep_flag` ON `yep` (`flag`);

DROP INDEX `yep_price`;

CREATE UNIQUE `yep_flag` ON `yep` (`flag`);

DROP INDEX `yep_name`;
""")
        self.assertEqual(ddl.args, [])

    def test_drop(self):

        ddl = TABLE(
            definition={
                "name": "yep"
            }
        )

        ddl.generate()
        self.assertEqual(ddl.sql, """DROP TABLE IF EXISTS `yep`;\n""")
        self.assertEqual(ddl.args, [])
