import unittest

import relations
import relations.unittest
import relations_sql

import test_query
import test_expression


class Source(relations_sql.SOURCE):
    """
    Minimal SQL source using the concrete test SQL classes, for exercising the mixin.
    """

    SELECT = test_query.SELECT
    TABLE_NAME = test_expression.TABLE_NAME
    SQL = relations_sql.SQL
    schema = "test"


class Base(relations.Model):
    SOURCE = "TieTest"

class Sis(Base):
    id = int
    name = str
    bro_id = set

class Bro(Base):
    id = int
    name = str
    sis_id = set

class SisBro(Base):
    ID = None
    bro_id = int
    sis_id = int

relations.ManyToMany(Sis, Bro, SisBro)


class TestSOURCE(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.source = Source()
        relations.unittest.MockSource("TieTest")

    def sql(self, model):

        query = test_query.SELECT("*").FROM("sis")
        self.source.collate_ties_query(model, query)
        query.generate()
        return " ".join(query.sql.split())

    def test_collate_ties(self):

        # no-op: SQL sources resolve ties in the query, not in Python
        self.assertIsNone(self.source.collate_ties(Sis.many()))

    def test_collate_ties_query(self):

        # has / any -> id IN (subquery): the DB does the work, not Python
        self.assertIn(
            "`id` IN (SELECT `sis_id` FROM `test`.`sis_bro` WHERE `bro_id` IN (%s))",
            self.sql(Sis.many(bro_id__has=1))
        )
        self.assertIn(
            "`id` IN (SELECT `sis_id` FROM `test`.`sis_bro` WHERE `bro_id` IN (%s,%s))",
            self.sql(Sis.many(bro_id__any=[1, 2]))
        )

        # all -> GROUP BY / HAVING COUNT(DISTINCT) = N (unquoted, dialect-agnostic)
        self.assertIn(
            "`id` IN (SELECT `sis_id` FROM `test`.`sis_bro` WHERE `bro_id` IN (%s,%s) "
            "GROUP BY `sis_id` HAVING COUNT(DISTINCT bro_id) = 2)",
            self.sql(Sis.many(bro_id__all=[1, 2]))
        )

        # all de-dupes the request (a repeated value can't change the count)
        self.assertIn(
            "WHERE `bro_id` IN (%s) GROUP BY `sis_id` HAVING COUNT(DISTINCT bro_id) = 1)",
            self.sql(Sis.many(bro_id__all=[2, 2]))
        )

        # negation -> id NOT IN (subquery)
        self.assertIn(
            "`id` NOT IN (SELECT `sis_id` FROM `test`.`sis_bro` WHERE `bro_id` IN (%s))",
            self.sql(Sis.many(bro_id__not_has=1))
        )

        # symmetric direction selects bro_id by sis_id
        self.assertIn(
            "`id` IN (SELECT `bro_id` FROM `test`.`sis_bro` WHERE `sis_id` IN (%s))",
            self.sql(Bro.many(sis_id__has=1))
        )

        # no tie criteria -> query untouched
        self.assertNotIn("sis_bro", self.sql(Sis.many(name="x")))
