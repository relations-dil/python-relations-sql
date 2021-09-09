"""
Module for all Relations SQL relations_sql.CRITERIAs, pieces of Queries
"""

import relations_sql


class CLAUSE(relations_sql.CRITERIA):
    """
    Base class for clauses
    """

    KWARG = None
    KWARGS = None

    DELIMITTER = ","

    PARENTHESES = False
    NAME = None

    statement = None

    def __init__(self, *args, **kwargs):

        self.expressions = []
        self(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        """
        Shorthand for add
        """
        return self.add(*args, **kwargs)

    def add(self, *args, **kwargs):
        """
        Add expressiona
        """

        super().add(*args)

        for key in sorted(kwargs.keys()):
            if self.KWARG is None or isinstance(kwargs[key], relations_sql.SQL):
                expression = kwargs[key]
            else:
                expression = self.KWARG(kwargs[key])
            self.expressions.append(self.KWARGS(key, expression))

        return self.statement or self

    def bind(self, statement):
        """
        Bind this statment to this clause for adding
        """

        self.statement = statement
        return self

    def generate(self, indent=0, count=0, pad=" ", **kwargs):
        """
        Concats the values
        """

        super().generate(indent=indent, count=count, pad=pad, **kwargs)

        if self.sql:

            one = pad * indent
            current = pad * (count * indent)
            next = current + one
            line = "\n" if indent else ' '

            self.sql = f"{self.NAME}{line}{next}{self.sql}" if self.NAME else f"{one}{self.sql}"


class ARGS(CLAUSE):
    """
    Clauses that never have keyword arguments
    """

    def __call__(self, *args):
        """
        Shorthand for add
        """
        return super().add(*args)


class OPTIONS(ARGS):
    """
    Beginning of a SELECT statement
    """

    ARGS = relations_sql.SQL

    DELIMITTER = ' '


class RESULTS(CLAUSE):
    """
    RESULTS part of SELECT statement
    """

    ARGS = relations_sql.FIELD
    KWARG = relations_sql.FIELD
    KWARGS = relations_sql.AS


class FROM(CLAUSE):
    """
    Clause for FROM
    """

    NAME = "FROM"

    ARGS = relations_sql.TABLE
    KWARG = relations_sql.TABLE
    KWARGS = relations_sql.AS


class WHERE(CLAUSE):
    """
    Clause for WHERE
    """

    NAME = "WHERE"

    ARGS = relations_sql.VALUE
    KWARGS = relations_sql.OP

    DELIMITTER = " AND "


class GROUP_BY(ARGS):
    """
    Clasuse for GROUP BY
    """

    NAME = "GROUP BY"

    ARGS = relations_sql.FIELD


class HAVING(CLAUSE):
    """
    Clause for HAVING
    """

    NAME = "HAVING"

    ARGS = relations_sql.VALUE
    KWARGS = relations_sql.OP

    DELIMITTER = " AND "


class ORDER_BY(CLAUSE):
    """
    Clause for the bORDER
    """

    NAME = "ORDER BY"

    ARGS = relations_sql.ORDER
    KWARGS = relations_sql.ORDER


class LIMIT(CLAUSE):
    """
    Base class for clauses
    """

    NAME = "LIMIT"

    ARGS = relations_sql.VALUE

    def add(self, *args, total=None, offset=None):
        """
        Add total and offset
        """

        if len(args) > 2 - len(self.expressions):
            raise relations_sql.SQLError(self, "cannot add when LIMIT set")

        args = list(args)

        if args and len(self.expressions) == 0 and total is None:
            total = args.pop(0)

        if args and offset is None:
            offset = args.pop(0)

        if total is not None and not isinstance(total, int):
            raise relations_sql.SQLError(self, "LIMIT total must be int")

        if offset is not None and not isinstance(offset, int):
            raise relations_sql.SQLError(self, "LIMIT offset must be int")

        if total is not None:
            self.expressions.append(self.ARGS(total))

        if offset is not None:
            self.expressions.append(self.ARGS(offset))

        return self.statement or self


class SET(CLAUSE):
    """
    relations_sql.CRITERIA for SET
    """

    NAME = "SET"

    KWARGS = relations_sql.ASSIGN


class VALUES(CLAUSE):
    """
    relations_sql.CRITERIA for VALUES
    """

    NAME = "VALUES"

    ARGS = relations_sql.LIST

    DELIMITTER = None

    fields = None

    def field(self, fields):
        """
        Field the fields
        """

        if self.fields:
            return

        self.fields = fields
        if self.statement:
            self.statement.field(self.fields)

    def add(self, *args, **kwargs):
        """
        Add a row to VALUES
        """

        if kwargs.get("FIELDS"):
            self.field(kwargs.pop("FIELDS"))

        if args and kwargs:
            raise relations_sql.SQLError(self, "add list or dict but not both")

        if kwargs:

            self.field(sorted(kwargs.keys()))

            args = []

            for field in self.fields:
                if field not in kwargs:
                    raise relations_sql.SQLError(self, f"missing field {field} in {kwargs}")
                args.append(kwargs[field])

        if args:
            if self.fields is not None and len(args) != len(self.fields):
                raise relations_sql.SQLError(self, f"wrong values {args} for fields {self.fields}")

            self.expressions.append(self.ARGS(args))

        return self.statement or self

    def generate(self, indent=0, count=0, pad=" ", **kwargs):
        """
        Concats the values
        """

        sql = []
        self.args = []

        count += 1
        current = pad * (count * indent)
        next = current + (indent * pad)
        line = "\n" if indent else ' '
        left, right = (f"(\n{next}", f"\n{current})") if indent else ('(', ')')
        delimitter = f"{right},{left}"

        self.express(self.expressions, sql, indent=indent, count=count+1, pad=pad, **kwargs)
        self.sql = f"{self.NAME}{line}{current}{left}{delimitter.join(sql)}{right}"
