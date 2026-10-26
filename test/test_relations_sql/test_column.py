import unittest
import unittest.mock

import test_ddl
import test_expression

import relations
import relations_sql


class COLUMN(test_ddl.DDL, relations_sql.COLUMN):

    KINDS = {
        "bool": "BOOL",
        "int": "INT",
        "float": "FLOAT",
        "str": "STR",
        "json": "JSON"
    }

    COLUMN_NAME = test_expression.COLUMN_NAME

    STORE = "STORE %s AS %s"
    KIND = "KIND %s AS %s"
    AUTO = "AUTO"
    EXTRACT = "AS %s"
    SET_DEFAULT = "SET DEFAULT %s AS %s"
    UNSET_DEFAULT = "UNSET DEFAULT %s"
    SET_NONE = "SET NOT NONE %s"
    UNSET_NONE = "UNSET NOT NONE %s"

class TestCOLUMN(unittest.TestCase):

    maxDiff = None

    def test_name(self):

        field = relations.Field(bool, name="flag", store="_flag")
        ddl = COLUMN(field.define(), definition={"name": "football"})

        self.assertEqual(ddl.name(), """`_flag`""")
        self.assertEqual(ddl.name(definition=True), """`football`""")

    def test_extract(self):

        ddl = COLUMN(store="data__a__0___1____2_____3", kind="str")

        sql = []

        ddl.extract("str", sql)
        self.assertEqual(sql, ["""STR""", """AS `data`#>>'$."a"[0][-1]."2"."-3"'"""])

    def test_create(self):

        field = relations.Field(bool, name="flag")
        ddl = COLUMN(field.define())

        ddl.create()
        self.assertEqual(ddl.sql, """`flag` BOOL""")

        field = relations.Field(int, name="id", auto=True)
        ddl = COLUMN(field.define())

        ddl.create()
        self.assertEqual(ddl.sql, """`id` AUTO""")

        field = relations.Field(float, "price", store="_price", default=1.25, none=False)
        ddl = COLUMN(field.define())

        ddl.create()
        self.assertEqual(ddl.sql, """`_price` FLOAT NOT NULL DEFAULT 1.25""")

        field = relations.Field(str, "name", store="_name", default="Willy", none=False)
        ddl = COLUMN(field.define())

        ddl.create()
        self.assertEqual(ddl.sql, """`_name` STR NOT NULL DEFAULT 'Willy'""")

        field = relations.Field(dict, "data", store="_data", default={"a": 1}, none=False)
        ddl = COLUMN(field.define())

        ddl.create()
        self.assertEqual(ddl.sql, """`_data` JSON NOT NULL DEFAULT '{"a": 1}'""")

        ddl = COLUMN(store="data__a__0___1____2_____3", kind="str")

        ddl.create()
        self.assertEqual(ddl.sql, """`data__a__0___1____2_____3` STR AS `data`#>>'$."a"[0][-1]."2"."-3"'""")

    def test_add(self):

        field = relations.Field(bool, name="flag")
        ddl = COLUMN(field.define(), added=True)

        ddl.add()
        self.assertEqual(ddl.sql, """ADD `flag` BOOL""")

        field = relations.Field(int, name="id")
        ddl = COLUMN(field.define(), added=True)

        ddl.add()
        self.assertEqual(ddl.sql, """ADD `id` INT""")

        field = relations.Field(float, "price", store="_price", default=1.25, none=False)
        ddl = COLUMN(field.define(), added=True)

        ddl.add()
        self.assertEqual(ddl.sql, """ADD `_price` FLOAT NOT NULL DEFAULT 1.25""")

        field = relations.Field(str, "name", store="_name", default="Willy", none=False)
        ddl = COLUMN(field.define(), added=True)

        ddl.add()
        self.assertEqual(ddl.sql, """ADD `_name` STR NOT NULL DEFAULT 'Willy'""")

        field = relations.Field(dict, "data", store="_data", default={"a": 1}, none=False)
        ddl = COLUMN(field.define(), added=True)

        ddl.add()
        self.assertEqual(ddl.sql, """ADD `_data` JSON NOT NULL DEFAULT '{"a": 1}'""")

        ddl = COLUMN(store="data__a__0___1____2_____3", kind="str", added=True)

        ddl.add()
        self.assertEqual(ddl.sql, """ADD `data__a__0___1____2_____3` STR AS `data`#>>'$."a"[0][-1]."2"."-3"'""")

    def test_store(self):

        field = relations.Field(int, store="_id")

        definition = {
            "store": "id"
        }
        ddl = COLUMN(field.define(), definition)
        sql = []
        ddl.store(sql)
        self.assertEqual(sql, ["""STORE `id` AS `_id`"""])

    def test_kind(self):

        field = relations.Field(float, store="id")

        definition = {
            "name": "id",
            "kind": "int"
        }
        ddl = COLUMN(field.define(), definition)
        sql = []
        ddl.kind(sql)
        self.assertEqual(sql, ["""KIND `id` AS FLOAT"""])

        # only the length changing keeps the kind it has

        field = relations.Field(str, store="id", length=32)

        definition = {
            "name": "id",
            "kind": "str",
            "length": 64
        }
        ddl = COLUMN(field.define(), definition)
        sql = []
        ddl.kind(sql)
        self.assertEqual(sql, ["""KIND `id` AS STR"""])

    def test_default(self):

        field = relations.Field(float, store="price", default=1.25)

        definition = {}
        ddl = COLUMN(field.define(), definition)
        sql = []
        ddl.default(sql)
        self.assertEqual(sql, ["""SET DEFAULT `price` AS 1.25"""])

        field = relations.Field(str, store="name", default='Willy')

        definition = {}
        ddl = COLUMN(field.define(), definition)
        sql = []
        ddl.default(sql)
        self.assertEqual(sql, ["""SET DEFAULT `name` AS 'Willy'"""])

        field = relations.Field(dict, store="meta", default={"a": 1})

        definition = {}
        ddl = COLUMN(field.define(), definition)
        sql = []
        ddl.default(sql)
        self.assertEqual(sql, ["""SET DEFAULT `meta` AS '{"a": 1}'"""])

        field = relations.Field(str, store="name")

        definition = {
            "name": "name",
            "default": "Willy"
        }
        ddl = COLUMN(field.define(), definition)
        sql = []
        ddl.default(sql)
        self.assertEqual(sql, ["""UNSET DEFAULT `name`"""])

    def test_none(self):

        field = relations.Field(int, store="id", none=False)

        definition = {}
        ddl = COLUMN(field.define(), definition)
        sql = []
        ddl.none(sql)
        self.assertEqual(sql, ["""SET NOT NONE `id`"""])

        definition = {
            "none": False
        }
        ddl = COLUMN(field.define(), store="id", none=True)
        sql = []
        ddl.none(sql)
        self.assertEqual(sql, ["""UNSET NOT NONE `id`"""])

    def test_modify(self):

        field = relations.Field(int, store="id", default=1, none=False)
        definition = {
            "store": "_id",
            "kind": "float",
            "default": 1.25,
            "none": True
        }
        ddl = COLUMN(field.define(), definition)

        ddl.generate()
        self.assertEqual(ddl.sql, """STORE `_id` AS `id`,KIND `id` AS INT,SET DEFAULT `id` AS 1,SET NOT NONE `id`""")
        self.assertEqual(ddl.args, [])

        ddl.generate(indent=2)
        self.assertEqual(ddl.sql, """STORE `_id` AS `id`,
KIND `id` AS INT,
SET DEFAULT `id` AS 1,
SET NOT NONE `id`""")

        ddl.generate(indent=2, count=1)
        self.assertEqual(ddl.sql, """STORE `_id` AS `id`,
  KIND `id` AS INT,
  SET DEFAULT `id` AS 1,
  SET NOT NONE `id`""")

        ddl.generate(indent=2, count=2)
        self.assertEqual(ddl.sql, """STORE `_id` AS `id`,
    KIND `id` AS INT,
    SET DEFAULT `id` AS 1,
    SET NOT NONE `id`""")

    def test_modify_length(self):

        # a str changing only its length is a change of kind

        definition = relations.Field(str, name="id", length=64).define()
        ddl = COLUMN(migration={"length": 32}, definition=definition)

        ddl.generate()
        self.assertEqual(ddl.sql, """KIND `id` AS STR""")

        # a length that isn't a str's isn't

        definition = relations.Field(int, name="id").define()
        ddl = COLUMN(migration={"length": 32}, definition=definition)

        ddl.generate()
        self.assertEqual(ddl.sql, """""")

    def test_drop(self):

        field = relations.Field(bool, name="flag")
        ddl = COLUMN(definition=field.define())

        ddl.generate()
        self.assertEqual(ddl.sql, """DROP `flag`""")
        self.assertEqual(ddl.args, [])
