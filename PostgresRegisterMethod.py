from itertools import chain

class PostgresRegisterMethod(object):
    async def transaction_begin(self, conn):
        self.transaction = conn.transaction()
        await self.transaction.start()

    async def transaction_end(self, rollback=False):
        if rollback:
            await self.transaction.rollback()
        else:
            await self.transaction.commit()

    async def search_oid(self, conn):
        return await conn.fetchval(
            "SELECT id FROM ordinances WHERE num=$1 AND municipality_id=$2;",
            self.num, int(self.municipality_code)
            )

    async def register_law(self, conn):
        return await conn.fetchval("""
            INSERT INTO ordinances(municipality_id, file_id, name, num)
            VALUES($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            RETURNING id;""",
            int(self.municipality_code), int(self.file_code), self.name, self.num,
        )

    async def delete_law(self, conn):
        await conn.execute("""
            DELETE FROM ordinances WHERE id = $1;""",
            self.oid
        )

    async def search_elements(self, conn, elem):
        return await conn.fetchval(
            "SELECT id FROM elements WHERE parent_id=$1 AND etype=$2 AND num=$3;",
            elem.parent.id, elem.etype, elem.num.num
            )

    async def register_elements(self, conn, elem):
        return await conn.fetchval("""
            INSERT INTO elements(parent_id, ordinance_id, etype, num, content)
            VALUES($1, $2, $3, $4, $5)
            ON CONFLICT DO NOTHING
            RETURNING id;
            """,
            elem.parent.id, self.oid, elem.etype, elem.num.num, "".join(elem.texts)
            )

    async def register_elements_many(self, conn, elems):
        args_strs = [None] * len(elems)
        args = []
        for i, e in enumerate(elems):
            args_strs[i] = "(${0}, ${1}, ${2}, ${3}, ${4})".format(
                i*5+1,
                i*5+2,
                i*5+3,
                i*5+4,
                i*5+5
                )
            args.extend([e.parent.id, self.oid, e.etype, e.num.num, "".join(e.texts)])

        await conn.execute("""
            INSERT INTO elements(parent_id, ordinance_id, etype, num, content)
            VALUES {};
            """.format(", ".join(args_strs)),
            *args
            )

    async def search_string(self, conn, s):
        return await conn.fetchval("SELECT id FROM strings WHERE string=$1;", s)

    async def upsert_string(self, conn, s):
        return await conn.fetchval(
            """INSERT INTO strings (
                  string, 
                  count
                ) VALUES (
                  $1,
                  1
                ) ON CONFLICT ON CONSTRAINT string_unique DO UPDATE SET
                  count = strings.count + 1
                RETURNING id;
            """, s)

    async def register_string_edge(self, conn, elem, sid, snum):
        await conn.fetchval("INSERT INTO element_strings(element_id, sentence_num, string_id) VALUES($1, $2, $3)",
                    elem.id, snum, sid)

    async def register_element_string_many(self, conn, edges):
        args = list(chain.from_iterable(edges))
        arg_str = ", ".join( "(${0}, ${1}, ${2})".format(i*3+1, i*3+2, i*3+3) for i in range(len(edges)) )

        await conn.execute("""
            INSERT INTO element_strings(element_id, string_id, sentence_num) VALUES {};
            """.format(arg_str),
            *args
            )
