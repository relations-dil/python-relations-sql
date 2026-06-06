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
