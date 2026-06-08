import unittest

import relations
import relations.unittest
import relations_sql

import test_query
import test_expression
import test_criteria


class Source(relations_sql.SOURCE):
    """
    Minimal SQL source using the concrete test SQL classes, for exercising the mixin.
    """

    SELECT = test_query.SELECT
    TABLE_NAME = test_expression.TABLE_NAME
    COLUMN_NAME = test_expression.COLUMN_NAME
    OP = test_criteria.OP
    OR = test_criteria.OR
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

        query = test_query.SELECT("*").FROM(getattr(model, "STORE", None) or model.NAME)
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

    def test_collate_attr_query(self):

        # bro__name -> FLAT join: tie + sibling added to FROM, joins + criteria in WHERE, NO subquery
        flat = self.sql(Sis.many(bro__name="Tom"))
        self.assertIn(
            "FROM `sis`,`test`.`sis_bro`,`test`.`bro` "
            "WHERE `sis`.`id`=(`sis_bro`.`sis_id`) AND `sis_bro`.`bro_id`=(`bro`.`id`) AND `bro`.`name` IN (%s)",
            flat
        )
        self.assertNotIn("(SELECT", flat)

        # any -> IN over the requested values, still flat
        self.assertIn(
            "AND `bro`.`name` IN (%s,%s)",
            self.sql(Sis.many(bro__name__any=["Tom", "Dick"]))
        )

        # a sibling field operator (like) is OR'd per value, still flat
        self.assertIn(
            "AND (`bro`.`name` LIKE %s OR `bro`.`name` LIKE %s)",
            self.sql(Sis.many(bro__name__like__any=["ar", "om"]))
        )

        # all -> the exception: id IN subquery with GROUP BY / HAVING COUNT(DISTINCT attr)
        self.assertIn(
            "`id` IN (SELECT `sis_bro`.`sis_id` FROM `test`.`sis_bro`,`test`.`bro` "
            "WHERE `sis_bro`.`bro_id`=(`bro`.`id`) AND `bro`.`name` IN (%s,%s) "
            "GROUP BY `sis_bro`.`sis_id` HAVING COUNT(DISTINCT bro.name) = 2)",
            self.sql(Sis.many(bro__name__all=["Tom", "Dick"]))
        )

        # negation -> the exception: id NOT IN subquery (a flat predicate would be wrong)
        self.assertIn(
            "`id` NOT IN (SELECT `sis_bro`.`sis_id` FROM `test`.`sis_bro`,`test`.`bro` "
            "WHERE `sis_bro`.`bro_id`=(`bro`.`id`) AND `bro`.`name` IN (%s))",
            self.sql(Sis.many(bro__name__not_has="Tom"))
        )

        # symmetric: brothers filtered by a tied sister's attribute (flat)
        self.assertIn(
            "FROM `bro`,`test`.`sis_bro`,`test`.`sis` "
            "WHERE `bro`.`id`=(`sis_bro`.`bro_id`) AND `sis_bro`.`sis_id`=(`sis`.`id`) AND `sis`.`name` IN (%s)",
            self.sql(Bro.many(sis__name="Sue"))
        )

        # a flat join marks the model for DISTINCT (count/retrieve dedupe); a subquery does not
        joined = Sis.many(bro__name="Tom")
        self.sql(joined)
        self.assertTrue(getattr(joined, "_distinct", False))

        aggregate = Sis.many(bro__name__all=["Tom", "Dick"])
        self.sql(aggregate)
        self.assertFalse(getattr(aggregate, "_distinct", False))

        # no attr criteria -> query untouched
        self.assertNotIn("`bro`.`name`", self.sql(Sis.many(bro_id__has=1)))
