import duckdb

class ChartQueryEngine:

    def __init__(self, config):
        self.config = config
        self.dataset = config["dataset"]
        self.base_table = f"'{self.dataset}'"
        self.dimensions = config.get("dimensions", [])
        self.metrics = config.get("metrics", [])
        self.filters = config.get("filters", [])
        self.joins = config.get("joins", [])
        self.transform = config.get("transform", {})
        self.order_by = config.get("order_by", [])
        self.limit = config.get("limit")
        self.offset = config.get("offset")
        self.sample = config.get("sample")

    def build_query(self):

        table_sql = self.apply_transforms()

        select_clause, group_clause = self.build_select()

        sql = f"SELECT {select_clause} FROM {table_sql}"

        # joins
        sql += self.apply_joins()

        # filters
        sql += self.apply_filters()

        # group by
        if group_clause:
            sql += f" GROUP BY {group_clause}"

        # order
        sql += self.apply_order()

        # limit
        if self.limit:
            sql += f" LIMIT {self.limit}"

        if self.offset:
            sql += f" OFFSET {self.offset}"

        return sql
    
    def apply_transforms(self):

        table = self.base_table

        # UNPIVOT
        if "unpivot" in self.transform:
            cols = self.transform["unpivot"]

            union_parts = [
                f"SELECT '{col}' AS key, {col} AS value FROM {table}"
                for col in cols
            ]

            table = f"({ ' UNION ALL '.join(union_parts) }) AS t"

        # BINNING
        if "binning" in self.transform:
            col = self.transform["binning"]["field"]
            size = self.transform["binning"]["size"]

            table = f"""
            (
                SELECT
                    FLOOR({col}/{size})*{size} AS {col},
                    *
                FROM {table}
            ) AS t
            """

        # TIME GRAIN
        if "time_grain" in self.transform:
            col = self.transform["time_grain"]["field"]
            grain = self.transform["time_grain"]["type"]

            table = f"""
            (
                SELECT
                    DATE_TRUNC('{grain}', {col}) AS {col},
                    *
                FROM {table}
            ) AS t
            """

        # SAMPLING
        if self.sample:
            table = f"(SELECT * FROM {table} USING SAMPLE {self.sample}) AS t"

        return table

    def build_select(self):

        select_parts = []
        group_parts = []

        for dim in self.dimensions:

            if isinstance(dim, dict):
                field = dim["field"]
                alias = dim.get("alias", field)

                select_parts.append(f"{field} AS \"{alias}\"")

                # IMPORTANT: only field goes to GROUP BY
                group_parts.append(field)

            else:
                select_parts.append(dim)
                group_parts.append(dim)

        for m in self.metrics:
            alias = m.get("alias", m.get("field"))

            if "expression" in m:
                expr = m["expression"]
                agg = m.get("aggregation")

                if agg and agg != "none":
                    select_parts.append(f"{agg.upper()}({expr}) AS {alias}")
                else:
                    select_parts.append(f"{expr} AS {alias}")

            else:
                field = m["field"]
                agg = m["aggregation"]

                if agg == "none":
                    select_parts.append(f"{field} AS {alias}")
                else:
                    select_parts.append(f"{agg.upper()}({field}) AS {alias}")

        has_aggregation = any(
            m.get("aggregation") and m.get("aggregation").lower() != "none"
            for m in self.metrics
        )

        # only apply GROUP BY if aggregation exists
        group_clause = ", ".join(group_parts) if (group_parts and has_aggregation) else None

        return ", ".join(select_parts), group_clause

    # def apply_filters(self):

    #     if not self.filters:
    #         return ""

    #     clauses = []

    #     for f in self.filters:
    #         field = f["field"]
    #         op = f["operator"]
    #         value = f["value"]

    #         if op == "IN":
    #             vals = ",".join([f"'{v}'" for v in value])
    #             clauses.append(f"{field} IN ({vals})")

    #         elif op == "BETWEEN":
    #             clauses.append(f"{field} BETWEEN {value[0]} AND {value[1]}")

    #         else:
    #             clauses.append(f"{field} {op} '{value}'")

    #     return " WHERE " + " AND ".join(clauses)

    def parse_filter(self, f):

        # AND block
        if "and" in f:
            parts = [self.parse_filter(cond) for cond in f["and"]]
            return "(" + " AND ".join(parts) + ")"

        # OR block
        if "or" in f:
            parts = [self.parse_filter(cond) for cond in f["or"]]
            return "(" + " OR ".join(parts) + ")"

        # Normal condition
        field = f["field"]
        op = f["operator"]
        value = f["value"]

        if op == "IN":
            vals = ",".join([f"'{v}'" for v in value])
            return f"{field} IN ({vals})"

        elif op == "BETWEEN":
            return f"{field} BETWEEN '{value[0]}' AND '{value[1]}'"

        else:
            return f"{field} {op} '{value}'"


    def apply_filters(self):

        if not self.filters:
            return ""

        # NEW: support dict-based filters
        if isinstance(self.filters, dict):
            return " WHERE " + self.parse_filter(self.filters)

        # OLD: fallback for list (backward compatibility)
        clauses = [self.parse_filter(f) for f in self.filters]

        return " WHERE " + " AND ".join(clauses)

    def apply_joins(self):

        if not self.joins:
            return ""

        join_sql = ""

        for j in self.joins:
            table = j["table"]
            on = j["on"]
            join_type = j.get("type", "LEFT")

            join_sql += f" {join_type} JOIN {table} ON {on}"

        return join_sql

    def apply_order(self):

        if not self.order_by:
            return ""

        parts = [
            f"{o['field']} {o.get('direction', 'ASC')}"
            for o in self.order_by
        ]

        return " ORDER BY " + ", ".join(parts)

    def execute(self):

        sql = self.build_query()

        df = duckdb.query(sql).to_df()
        print("-"*20)
        print(sql)
        print("-"*20)
        return {
            # "sql": sql,
            "data": df.to_dict(orient="records")
        }