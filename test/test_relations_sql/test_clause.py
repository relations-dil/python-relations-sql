import unittest
import unittest.mock

import test_expression
import test_criterion
import test_criteria


import relations_sql

class UNKNOWN(relations_sql.CLAUSE):

    ARGS = relations_sql.SQL

class KNOWN(relations_sql.CLAUSE):

    NAME = "CLAUSE"

    ARGS = test_expression.COLUMN_NAME
    KWARG = test_expression.COLUMN_NAME
    KWARGS = test_expression.AS

class TestCLAUSE(unittest.TestCase):

    maxDiff = None

    def test__init__(self):

        clause = UNKNOWN()

        self.assertEqual(clause.expressions, [])

        clause = UNKNOWN("people")

        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], relations_sql.SQL)
        self.assertEqual(clause.expressions[0].sql, """people""")

    def test___call__(self):

        clause = UNKNOWN()

        self.assertEqual(clause("people"), clause)
        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], relations_sql.SQL)
        self.assertEqual(clause.expressions[0].sql, """people""")

        query = unittest.mock.MagicMock()
        clause = KNOWN().bind(query)

        self.assertEqual(clause(stuff="things"), query)
        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.AS)
        self.assertIsInstance(clause.expressions[0].label, test_expression.NAME)
        self.assertIsInstance(clause.expressions[0].expression, test_expression.COLUMN_NAME)
        self.assertEqual(clause.expressions[0].label.name, "stuff")
        self.assertEqual(clause.expressions[0].expression.name, "things")

    def test_bind(self):

        query = unittest.mock.MagicMock()
        clause = KNOWN()

        self.assertEqual(clause.bind(query), clause)
        self.assertEqual(clause.query, query)

    def test_add(self):

        clause = UNKNOWN()

        self.assertEqual(clause.add("people"), clause)
        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], relations_sql.SQL)
        self.assertEqual(clause.expressions[0].sql, """people""")

        query = unittest.mock.MagicMock()
        clause = KNOWN().bind(query)

        self.assertEqual(clause.add(stuff="things"), query)
        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.AS)
        self.assertIsInstance(clause.expressions[0].label, test_expression.NAME)
        self.assertIsInstance(clause.expressions[0].expression, test_expression.COLUMN_NAME)
        self.assertEqual(clause.expressions[0].label.name, "stuff")
        self.assertEqual(clause.expressions[0].expression.name, "things")

        clause = KNOWN()

        self.assertEqual(clause.add({"stuff": "things"}), clause)
        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.AS)
        self.assertIsInstance(clause.expressions[0].label, test_expression.NAME)
        self.assertIsInstance(clause.expressions[0].expression, test_expression.COLUMN_NAME)
        self.assertEqual(clause.expressions[0].label.name, "stuff")
        self.assertEqual(clause.expressions[0].expression.name, "things")

    def test_generate(self):

        clause = UNKNOWN()

        self.assertFalse(clause)

        clause("people", "stuff", "things")
        clause.generate()
        self.assertEqual(clause.sql, """people,stuff,things""")
        self.assertEqual(clause.args, [])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """  people,
  stuff,
  things""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """  people,
    stuff,
    things""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """  people,
      stuff,
      things""")

        clause = KNOWN()

        self.assertFalse(clause)

        clause("people", stuff="things")
        clause.generate()
        self.assertEqual(clause.sql, """CLAUSE `people`,`things` AS `stuff`""")
        self.assertEqual(clause.args, [])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """CLAUSE
  `people`,
  `things` AS `stuff`""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """CLAUSE
    `people`,
    `things` AS `stuff`""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """CLAUSE
      `people`,
      `things` AS `stuff`""")

        clause = KNOWN()
        clause(test_criteria.LOGIC(test_criterion.EQ("totes", "maigoats"), test_criterion.EQ("toast", "myghost", invert=True)))
        clause(test_criteria.LOGIC(test_criterion.EQ("totes", "maigoats"), test_criterion.EQ("toast", "myghost", invert=True)))

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """CLAUSE
  (
    `totes`=%s LOGIC
    `toast`!=%s
  ),
  (
    `totes`=%s LOGIC
    `toast`!=%s
  )""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """CLAUSE
    (
      `totes`=%s LOGIC
      `toast`!=%s
    ),
    (
      `totes`=%s LOGIC
      `toast`!=%s
    )""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """CLAUSE
      (
        `totes`=%s LOGIC
        `toast`!=%s
      ),
      (
        `totes`=%s LOGIC
        `toast`!=%s
      )""")


class ARGS(relations_sql.ARGS):

    ARGS = test_expression.VALUE

class TestARGS(unittest.TestCase):

    maxDiff = None

    def test___call__(self):

        clause = ARGS()

        self.assertEqual(clause(False), clause)
        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.VALUE)
        self.assertFalse(clause.expressions[0].value)

        query = unittest.mock.MagicMock()
        self.assertEqual(clause.bind(query)(False), query)

        self.assertRaises(TypeError, clause.add, nope=False)

    def test_add(self):

        clause = ARGS()

        self.assertEqual(clause.add(False), clause)
        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.VALUE)
        self.assertFalse(clause.expressions[0].value)

        query = unittest.mock.MagicMock()
        self.assertEqual(clause.bind(query).add(False), query)

        self.assertRaises(TypeError, clause.add, nope=False)


class OPTIONS(relations_sql.OPTIONS):

    pass

class TestOPTIONS(unittest.TestCase):

    maxDiff = None

    def test_generate(self):

        clause = OPTIONS()
        self.assertFalse(clause)

        clause("people", "stuff", "things")
        clause.generate()
        self.assertEqual(clause.sql, """people stuff things""")
        self.assertEqual(clause.args, [])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """  people
  stuff
  things""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """  people
    stuff
    things""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """  people
      stuff
      things""")


class FIELDS(relations_sql.FIELDS):

    ARGS = test_expression.COLUMN_NAME
    KWARG = test_expression.COLUMN_NAME
    KWARGS = test_expression.AS

class TestFIELDS(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        clause = FIELDS("*")

        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.COLUMN_NAME)
        self.assertEqual(clause.expressions[0].name, "*")

        clause = FIELDS("people.stuff.things")

        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.COLUMN_NAME)
        self.assertEqual(clause.expressions[0].name, "things")

        clause = FIELDS(stuff="things")

        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.AS)
        self.assertIsInstance(clause.expressions[0].label, test_expression.NAME)
        self.assertIsInstance(clause.expressions[0].expression, test_expression.COLUMN_NAME)
        self.assertEqual(clause.expressions[0].label.name, "stuff")
        self.assertEqual(clause.expressions[0].expression.name, "things")

        clause = FIELDS({"stuff": "things"})

        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.AS)
        self.assertIsInstance(clause.expressions[0].label, test_expression.NAME)
        self.assertIsInstance(clause.expressions[0].expression, test_expression.COLUMN_NAME)
        self.assertEqual(clause.expressions[0].label.name, "stuff")
        self.assertEqual(clause.expressions[0].expression.name, "things")

    def test_generate(self):

        clause = FIELDS()

        self.assertFalse(clause)

        clause("*")
        clause.generate()
        self.assertEqual(clause.sql, """*""")
        self.assertEqual(clause.args, [])

        clause(stuff="things")
        clause.generate()
        self.assertEqual(clause.sql, """*,`things` AS `stuff`""")
        self.assertEqual(clause.args, [])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """  *,
  `things` AS `stuff`""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """  *,
    `things` AS `stuff`""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """  *,
      `things` AS `stuff`""")


class FROM(relations_sql.FROM):

    ARGS = test_expression.TABLE_NAME
    KWARG = test_expression.TABLE_NAME
    KWARGS = test_expression.AS

class TestFROM(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        clause = FROM("people", stuff="things")

        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[0], test_expression.TABLE_NAME)
        self.assertEqual(clause.expressions[0].name, "people")

        self.assertIsInstance(clause.expressions[1], test_expression.AS)
        self.assertIsInstance(clause.expressions[1].label, test_expression.NAME)
        self.assertIsInstance(clause.expressions[1].expression, test_expression.TABLE_NAME)
        self.assertEqual(clause.expressions[1].label.name, "stuff")
        self.assertEqual(clause.expressions[1].expression.name, "things")

        clause = FROM({"stuff": "things"})

        self.assertIsInstance(clause.expressions[0], test_expression.AS)
        self.assertIsInstance(clause.expressions[0].label, test_expression.NAME)
        self.assertIsInstance(clause.expressions[0].expression, test_expression.TABLE_NAME)
        self.assertEqual(clause.expressions[0].label.name, "stuff")
        self.assertEqual(clause.expressions[0].expression.name, "things")

    def test_generate(self):

        clause = FROM()

        self.assertFalse(clause)

        clause("people", stuff="things")
        clause.generate()
        self.assertEqual(clause.sql, """FROM `people`,`things` AS `stuff`""")
        self.assertEqual(clause.args, [])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """FROM
  `people`,
  `things` AS `stuff`""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """FROM
    `people`,
    `things` AS `stuff`""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """FROM
      `people`,
      `things` AS `stuff`""")


class WHERE(relations_sql.WHERE):

    ARGS = test_expression.VALUE
    KWARGS = test_criteria.OP

class TestWHERE(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        clause = WHERE("people", stuff="things")

        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[0], test_expression.VALUE)
        self.assertEqual(clause.expressions[0].value, "people")

        self.assertIsInstance(clause.expressions[1], test_criterion.EQ)
        self.assertIsInstance(clause.expressions[1].left, test_expression.COLUMN_NAME)
        self.assertIsInstance(clause.expressions[1].right, test_expression.VALUE)
        self.assertEqual(clause.expressions[1].left.name, "stuff")
        self.assertEqual(clause.expressions[1].right.value, "things")

        clause = WHERE({"stuff": "things"})

        self.assertIsInstance(clause.expressions[0], test_criterion.EQ)
        self.assertIsInstance(clause.expressions[0].left, test_expression.COLUMN_NAME)
        self.assertIsInstance(clause.expressions[0].right, test_expression.VALUE)
        self.assertEqual(clause.expressions[0].left.name, "stuff")
        self.assertEqual(clause.expressions[0].right.value, "things")

    def test_generate(self):

        clause = WHERE()

        self.assertFalse(clause)

        clause("people", stuff="things")
        clause.generate()
        self.assertEqual(clause.sql, """WHERE %s AND `stuff`=%s""")
        self.assertEqual(clause.args, ["people", "things"])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """WHERE
  %s AND
  `stuff`=%s""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """WHERE
    %s AND
    `stuff`=%s""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """WHERE
      %s AND
      `stuff`=%s""")


class GROUP_BY(relations_sql.GROUP_BY):

    ARGS = test_expression.NAME

class TestGROUP_BY(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        clause = GROUP_BY("people", "stuff", "things")

        self.assertEqual(len(clause.expressions), 3)
        self.assertIsInstance(clause.expressions[0], test_expression.NAME)
        self.assertIsInstance(clause.expressions[1], test_expression.NAME)
        self.assertIsInstance(clause.expressions[2], test_expression.NAME)
        self.assertEqual(clause.expressions[0].name, "people")
        self.assertEqual(clause.expressions[1].name, "stuff")
        self.assertEqual(clause.expressions[2].name, "things")

    def test_generate(self):

        clause = GROUP_BY()

        self.assertFalse(clause)

        clause("people", "stuff", "things")
        clause.generate()
        self.assertEqual(clause.sql, """GROUP BY `people`,`stuff`,`things`""")
        self.assertEqual(clause.args, [])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """GROUP BY
  `people`,
  `stuff`,
  `things`""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """GROUP BY
    `people`,
    `stuff`,
    `things`""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """GROUP BY
      `people`,
      `stuff`,
      `things`""")


class HAVING(relations_sql.HAVING):

    ARGS = test_expression.VALUE
    KWARGS = test_criteria.OP

class TestHAVING(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        clause = HAVING("people", stuff="things")

        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[0], test_expression.VALUE)
        self.assertEqual(clause.expressions[0].value, "people")

        self.assertIsInstance(clause.expressions[1], test_criterion.EQ)
        self.assertIsInstance(clause.expressions[1].left, test_expression.COLUMN_NAME)
        self.assertIsInstance(clause.expressions[1].right, test_expression.VALUE)
        self.assertEqual(clause.expressions[1].left.name, "stuff")
        self.assertEqual(clause.expressions[1].right.value, "things")

        clause = HAVING({"stuff": "things"})

        self.assertIsInstance(clause.expressions[0], test_criterion.EQ)
        self.assertIsInstance(clause.expressions[0].left, test_expression.COLUMN_NAME)
        self.assertIsInstance(clause.expressions[0].right, test_expression.VALUE)
        self.assertEqual(clause.expressions[0].left.name, "stuff")
        self.assertEqual(clause.expressions[0].right.value, "things")

    def test_generate(self):

        clause = HAVING()

        self.assertFalse(clause)

        clause("people", stuff="things")
        clause.generate()
        self.assertEqual(clause.sql, """HAVING %s AND `stuff`=%s""")
        self.assertEqual(clause.args, ["people", "things"])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """HAVING
  %s AND
  `stuff`=%s""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """HAVING
    %s AND
    `stuff`=%s""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """HAVING
      %s AND
      `stuff`=%s""")


ASC = test_expression.ASC
DESC = test_expression.DESC

class ORDER_BY(relations_sql.ORDER_BY):

    ARGS = test_expression.ORDER
    KWARGS = test_expression.ORDER

class TestORDER_BY(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        clause = ORDER_BY("people", stuff=ASC, things=DESC)

        self.assertEqual(len(clause.expressions), 3)
        self.assertIsInstance(clause.expressions[0], test_expression.ORDER)
        self.assertIsInstance(clause.expressions[1], test_expression.ORDER)
        self.assertIsInstance(clause.expressions[2], test_expression.ORDER)
        self.assertEqual(clause.expressions[0].expression.name, "people")
        self.assertEqual(clause.expressions[1].expression.name, "stuff")
        self.assertEqual(clause.expressions[2].expression.name, "things")
        self.assertEqual(clause.expressions[0].order, None)
        self.assertEqual(clause.expressions[1].order, ASC)
        self.assertEqual(clause.expressions[2].order, DESC)

        clause = ORDER_BY({"stuff": ASC, "things": DESC})

        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[0], test_expression.ORDER)
        self.assertIsInstance(clause.expressions[1], test_expression.ORDER)
        self.assertEqual(clause.expressions[0].expression.name, "stuff")
        self.assertEqual(clause.expressions[1].expression.name, "things")
        self.assertEqual(clause.expressions[0].order, ASC)
        self.assertEqual(clause.expressions[1].order, DESC)

    def test_generate(self):

        clause = ORDER_BY()

        self.assertFalse(clause)

        clause("people", stuff=ASC, things=DESC)
        clause.generate()
        self.assertEqual(clause.sql, """ORDER BY `people`,`stuff` ASC,`things` DESC""")
        self.assertEqual(clause.args, [])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """ORDER BY
  `people`,
  `stuff` ASC,
  `things` DESC""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """ORDER BY
    `people`,
    `stuff` ASC,
    `things` DESC""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """ORDER BY
      `people`,
      `stuff` ASC,
      `things` DESC""")


class LIMIT(relations_sql.LIMIT):

    ARGS = test_expression.VALUE

class TestLIMIT(unittest.TestCase):

    maxDiff = None

    def test_add(self):

        clause = LIMIT()

        self.assertEqual(clause.add(10), clause)
        self.assertEqual(len(clause.expressions), 1)
        self.assertIsInstance(clause.expressions[0], test_expression.VALUE)
        self.assertEqual(clause.expressions[0].value, 10)

        self.assertEqual(clause.add(5), clause)
        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[1], test_expression.VALUE)
        self.assertEqual(clause.expressions[1].value, 5)

        query = unittest.mock.MagicMock()
        clause = LIMIT().bind(query)

        self.assertEqual(clause.add(10, 5), query)
        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[0], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[1], test_expression.VALUE)
        self.assertEqual(clause.expressions[0].value, 10)
        self.assertEqual(clause.expressions[1].value, 5)

        clause = LIMIT()

        clause.add(total=10, offset=5)
        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[0], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[1], test_expression.VALUE)
        self.assertEqual(clause.expressions[0].value, 10)
        self.assertEqual(clause.expressions[1].value, 5)

        clause = LIMIT()

        clause.add({"total": 10, "offset": 5})
        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[0], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[1], test_expression.VALUE)
        self.assertEqual(clause.expressions[0].value, 10)
        self.assertEqual(clause.expressions[1].value, 5)

        self.assertRaisesRegex(relations_sql.SQLError, "cannot add when LIMIT set", clause.add, 25)

        clause = LIMIT()

        self.assertRaisesRegex(relations_sql.SQLError, "LIMIT total must be int", clause.add, total="nope")
        self.assertRaisesRegex(relations_sql.SQLError, "LIMIT offset must be int", clause.add, offset="nope")

    def test_generate(self):

        clause = LIMIT()

        self.assertFalse(clause)

        clause(10, 5)
        clause.generate()
        self.assertEqual(clause.sql, """LIMIT %s OFFSET %s""")
        self.assertEqual(clause.args, [10, 5])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """LIMIT %s OFFSET %s""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """LIMIT %s OFFSET %s""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """LIMIT %s OFFSET %s""")


class SET(relations_sql.SET):

    KWARGS = test_expression.ASSIGN

class TestSET(unittest.TestCase):

    maxDiff = None

    def test___init__(self):

        clause = SET(fee="fie", foe="fum")

        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[0], test_expression.ASSIGN)
        self.assertIsInstance(clause.expressions[1], test_expression.ASSIGN)
        self.assertEqual(clause.expressions[0].column.name, "fee")
        self.assertEqual(clause.expressions[1].column.name, "foe")
        self.assertEqual(clause.expressions[0].expression.value, "fie")
        self.assertEqual(clause.expressions[1].expression.value, "fum")

        clause = SET({"fee": "fie", "foe": "fum"})

        self.assertEqual(len(clause.expressions), 2)
        self.assertIsInstance(clause.expressions[0], test_expression.ASSIGN)
        self.assertIsInstance(clause.expressions[1], test_expression.ASSIGN)
        self.assertEqual(clause.expressions[0].column.name, "fee")
        self.assertEqual(clause.expressions[1].column.name, "foe")
        self.assertEqual(clause.expressions[0].expression.value, "fie")
        self.assertEqual(clause.expressions[1].expression.value, "fum")

    def test_generate(self):

        clause = SET()

        self.assertFalse(clause)

        clause(fee="fie", foe="fum")
        clause.generate()
        self.assertEqual(clause.sql, """SET `fee`=%s,`foe`=%s""")
        self.assertEqual(clause.args, ["fie", "fum"])

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """SET
  `fee`=%s,
  `foe`=%s""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """SET
    `fee`=%s,
    `foe`=%s""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """SET
      `fee`=%s,
      `foe`=%s""")


class VALUES(relations_sql.VALUES):

    ARGS = test_expression.LIST

class TestVALUES(unittest.TestCase):

    maxDiff = None

    def test_column(self):

        query = unittest.mock.MagicMock()
        clause = VALUES().bind(query)

        query.COLUMNS = None

        def column(columns):

            query.COLUMNS = test_expression.COLUMN_NAMES(columns)

        query.column.side_effect = column

        clause.column(['1', '2', '3'])
        self.assertEqual(clause.columns, ['1', '2', '3'])
        query.column.assert_called_once_with(['1', '2', '3'])

        clause.column(['4', '5', '6'])
        self.assertEqual(clause.columns, ['1', '2', '3'])
        query.column.assert_called_once_with(['1', '2', '3'])

        clause = VALUES()

        clause.column(['4', '5', '6'])
        self.assertEqual(clause.columns, ['4', '5', '6'])

    def test_add(self):

        query = unittest.mock.MagicMock()
        clause = VALUES().bind(query)

        query.COLUMNS = None

        def column(columns):

            query.COLUMNS = test_expression.COLUMN_NAMES(columns)

        query.column.side_effect = column

        clause.add(4, 5, 6, COLUMNS=['1', '2', '3'])
        self.assertEqual(clause.columns, ['1', '2', '3'])
        query.column.assert_called_once_with(['1', '2', '3'])
        self.assertIsInstance(clause.expressions[0], test_expression.LIST)
        self.assertIsInstance(clause.expressions[0].expressions[0], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[0].expressions[1], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[0].expressions[2], test_expression.VALUE)
        self.assertEqual(clause.expressions[0].expressions[0].value, 4)
        self.assertEqual(clause.expressions[0].expressions[1].value, 5)
        self.assertEqual(clause.expressions[0].expressions[2].value, 6)

        clause.add(7, 8, 9, COLUMNS=['10'])
        self.assertEqual(clause.columns, ['1', '2', '3'])
        query.column.assert_called_once_with(['1', '2', '3'])
        self.assertIsInstance(clause.expressions[1], test_expression.LIST)
        self.assertIsInstance(clause.expressions[1].expressions[0], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[1].expressions[1], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[1].expressions[2], test_expression.VALUE)
        self.assertEqual(clause.expressions[1].expressions[0].value, 7)
        self.assertEqual(clause.expressions[1].expressions[1].value, 8)
        self.assertEqual(clause.expressions[1].expressions[2].value, 9)

        query = unittest.mock.MagicMock()
        clause = VALUES().bind(query)

        query.COLUMNS = None

        def column(columns):

            query.COLUMNS = test_expression.COLUMN_NAMES(columns)

        query.column.side_effect = column

        clause.add(**{"1": 4, "2": 5, "3": 6})
        self.assertEqual(clause.columns, ['1', '2', '3'])
        query.column.assert_called_once_with(['1', '2', '3'])
        self.assertIsInstance(clause.expressions[0], test_expression.LIST)
        self.assertIsInstance(clause.expressions[0].expressions[0], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[0].expressions[1], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[0].expressions[2], test_expression.VALUE)
        self.assertEqual(clause.expressions[0].expressions[0].value, 4)
        self.assertEqual(clause.expressions[0].expressions[1].value, 5)
        self.assertEqual(clause.expressions[0].expressions[2].value, 6)

        clause.add({"1": 4, "2": 5, "3": 6})
        self.assertEqual(clause.columns, ['1', '2', '3'])
        query.column.assert_called_once_with(['1', '2', '3'])
        self.assertIsInstance(clause.expressions[0], test_expression.LIST)
        self.assertIsInstance(clause.expressions[0].expressions[0], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[0].expressions[1], test_expression.VALUE)
        self.assertIsInstance(clause.expressions[0].expressions[2], test_expression.VALUE)
        self.assertEqual(clause.expressions[0].expressions[0].value, 4)
        self.assertEqual(clause.expressions[0].expressions[1].value, 5)
        self.assertEqual(clause.expressions[0].expressions[2].value, 6)

        self.assertRaisesRegex(relations_sql.SQLError, "add list or dict but not both", clause.add, "nope", column="nope")
        self.assertRaisesRegex(relations_sql.SQLError, "missing column 1 in \{'column': 'nope'\}", clause.add, column="nope")
        self.assertRaisesRegex(relations_sql.SQLError, "wrong values \('nope',\) for columns \['1', '2', '3'\]", clause.add, "nope")

    def test_generate(self):

        clause = VALUES()

        self.assertFalse(clause)

        clause(fee="fie", foe="fum")
        clause.generate()
        self.assertEqual(clause.sql, """VALUES (%s,%s)""")
        self.assertEqual(clause.args, ["fie", "fum"])

        clause(fee="fie", foe="fum")

        clause.generate(indent=2)
        self.assertEqual(clause.sql, """VALUES
  (
    %s,
    %s
  ),(
    %s,
    %s
  )""")

        clause.generate(indent=2, count=1)
        self.assertEqual(clause.sql, """VALUES
    (
      %s,
      %s
    ),(
      %s,
      %s
    )""")

        clause.generate(indent=2, count=2)
        self.assertEqual(clause.sql, """VALUES
      (
        %s,
        %s
      ),(
        %s,
        %s
      )""")
