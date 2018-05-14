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
            "SELECT id FROM ordinances WHERE num=$1 AND muni_id=$2;",
            self.num, int(self.municipality_code)
            )

    async def register_law(self, conn):
        await conn.execute("""
            INSERT INTO ordinances(muni_id, file_id, name, num)
            VALUES($1, $2, $3, $4);""",
            int(self.municipality_code), int(self.file_code), self.name, self.num,
        )

    async def search_elements(self, conn, elem):
        return await conn.fetchval(
            "SELECT id FROM elements WHERE parent_id=$1 AND etype=$2 AND num=$3;",
            elem.parent.id, elem.etype, elem.num.num
            )

    async def register_elements(self, conn, elem):
        await conn.execute("""
            INSERT INTO elements(parent_id, ord_id, etype, num, content)
            VALUES($1, $2, $3, $4, $5);
            """,
            elem.parent.id, self.oid, elem.etype, elem.num.num, "".join(elem.texts)
            )

    async def search_string(self, conn, s):
        return await conn.fetchval("SELECT id FROM strings WHERE string=$1;", s)

    async def register_string(self, conn, s):
        await conn.execute("""INSERT INTO strings(string) VALUES($1);""", s)

    async def register_string_edge(self, conn, elem, sid, snum):
        await conn.fetchval("INSERT INTO string_edges(elem_id, sentence_num, string_id) VALUES($1, $2, $3)",
                    elem.id, snum, sid)
