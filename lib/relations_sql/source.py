"""
SQL source mixin for Relations.

Provides the SQL-side resolution of many-to-many tie criteria, shared by every
SQL backend (sqlite3, pymysql, psycopg2). A consuming source must provide the
SELECT, TABLE_NAME and SQL expression classes plus a `schema` attribute.
"""

# pylint: disable=too-many-locals


class SOURCE:
    """
    Mixin adding in-database resolution of tie-field set criteria.
    """

    def collate_ties(self, model):
        """
        SQL sources resolve ties inside the query (see collate_ties_query), so the
        base Python resolver is overridden to a no-op here.
        """

    def collate_ties_query(self, model, query):
        """
        Resolves tie-field set criteria (has/any/all and their not_ variants) into
        IN (subquery) clauses, so the database does has/any/all in a single query
        instead of reading the ties into Python.
        """

        sides = [
            (relation, relation.brother_sister_ref, relation.tie_brother_ref, relation.tie_sister_ref)
            for relation in model.SISTERS.values()
        ] + [
            (relation, relation.sister_brother_ref, relation.tie_sister_ref, relation.tie_brother_ref)
            for relation in model.BROTHERS.values()
        ]

        for relation, field_ref, tie_self_ref, tie_sibling_ref in sides:

            field = model._record._names[field_ref]

            if not field.criteria:
                continue

            tie = relation.Tie.thy()
            tie_schema = getattr(tie, "SCHEMA", None) or self.schema
            tie_store = getattr(tie, "STORE", None) or tie.NAME

            for criterion, values in field.criteria.items():

                negate = criterion.startswith("not_")
                operator = criterion.split("not_", 1)[-1] if negate else criterion
                values = sorted(set(values if isinstance(values, (list, set, tuple)) else [values]))

                subquery = self.SELECT(tie_self_ref).FROM(
                    self.TABLE_NAME(tie_store, schema=tie_schema)
                ).WHERE(**{f"{tie_sibling_ref}__in": values})

                if operator == "all":
                    subquery.GROUP_BY(tie_self_ref).HAVING(
                        self.SQL(f"COUNT(DISTINCT {tie_sibling_ref}) = {len(values)}")
                    )

                query.WHERE(**{f"{model._id}__{'not_in' if negate else 'in'}": subquery})

            field.criteria = {}

        self.collate_attr_query(model, query)

    def collate_attr_query(self, model, query):
        """
        Resolves sibling-attribute criteria (bro__name=..., captured on model._ties).

        A positive, non-aggregate filter (bro__name="Tom", bro__name__like, bro__name__in) is a
        flat join: the tie table and the sibling table are added to the outer query's FROM and the
        model->tie + tie->sibling joins plus the sibling predicate to its WHERE. Because a model
        tied to several matching siblings would repeat, the model is marked _distinct (count and
        retrieve honor it with COUNT(DISTINCT id) / SELECT DISTINCT).

        all (every distinct value) and negation (NOT tied to a match) cannot be a flat predicate,
        so they stay an id IN / NOT IN subquery, which keeps the outer query one row per model.
        """

        model_store = getattr(model, "STORE", None) or model.NAME
        model._distinct = False

        for relation, side, field, operator, negate, value in getattr(model, "_ties", []):

            if side == "sister":
                tie_self_ref, tie_sibling_ref = relation.tie_brother_ref, relation.tie_sister_ref
                sibling, sibling_id = relation.Sister.thy(), relation.sister_id
            else:
                tie_self_ref, tie_sibling_ref = relation.tie_sister_ref, relation.tie_brother_ref
                sibling, sibling_id = relation.Brother.thy(), relation.brother_id

            tie = relation.Tie.thy()
            tie_schema = getattr(tie, "SCHEMA", None) or self.schema
            tie_store = getattr(tie, "STORE", None) or tie.NAME
            sib_schema = getattr(sibling, "SCHEMA", None) or self.schema
            sib_store = getattr(sibling, "STORE", None) or sibling.NAME

            values = sorted(set(value if isinstance(value, (list, set, tuple)) else [value]))

            tie_table = self.TABLE_NAME(tie_store, schema=tie_schema)
            sib_table = self.TABLE_NAME(sib_store, schema=sib_schema)

            # join the tie table to the sibling table on the tie's sibling-id column
            sibling_join = self.OP(**{f"{tie_store}.{tie_sibling_ref}": self.COLUMN_NAME(sibling_id, table=sib_store)})

            # the sibling predicate, matching any of the requested values; a field with its own
            # operator (name__like) is OR'd per value, a plain field is a single IN
            if "__" in field:
                match = self.OR(*[self.OP(**{f"{sib_store}.{field}": item}) for item in values])
                attr = field.rsplit("__", 1)[0]
            else:
                match = self.OP(**{f"{sib_store}.{field}__in": values})
                attr = field

            if operator == "all" or negate:

                # aggregate / anti-join: an id IN / NOT IN subquery keeps the outer query one row per model
                self_ref = self.COLUMN_NAME(tie_self_ref, table=tie_store)
                subquery = self.SELECT(self_ref).FROM(tie_table, sib_table).WHERE(sibling_join, match)

                if operator == "all":
                    subquery.GROUP_BY(self_ref).HAVING(
                        self.SQL(f"COUNT(DISTINCT {sib_store}.{attr}) = {len(values)}")
                    )

                query.WHERE(**{f"{model._id}__{'not_in' if negate else 'in'}": subquery})

            else:

                # flat join: tie + sibling tables into FROM, joins + predicate into WHERE
                model_join = self.OP(**{f"{model_store}.{model._id}": self.COLUMN_NAME(tie_self_ref, table=tie_store)})
                query.FROM(tie_table, sib_table).WHERE(model_join, sibling_join, match)
                model._distinct = True

        model._ties = []
