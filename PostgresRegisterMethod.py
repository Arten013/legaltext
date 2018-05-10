class PostgresRegisterMethods(object):
    async def search_oid(self, conn):
        return await conn.fetchval(
            "SELECT id FROM ordinances WHERE num=$1::num AND muni_id=$2::municipality_code;",
            self
            )

    async def register_law(self, conn):
        await conn.execute("""
            INSERT INTO ordinances(muni_id, file_id, name, num)
            VALUES($1::municipality_code, $1::file_code, $1::name, $1::num);""",
            self,
        )

    async def search_elements(self, conn, elem):
        return await conn.fetchval(
            "SELECT id FROM elements WHERE parent_id=$1 AND etype=$2 AND num=$3;",
            elem.parent.id, elem.etype, str(elem.num.num)
            )

    async def register_elements(self, conn, elem):
        await conn.execute("""
            INSERT INTO elements(parent_id, ord_id, etype, num, content)
            VALUES($1, :$2, :$3, :$4, :$5);
            """,
            elem.parent.id, elem.etype, str(elem.num.num), self.oid, "".join(elem.texts)
            )

    async def search_string(self, conn, s):
        return await conn.fetchval("SELECT id FROM strings WHERE string=$1;", s)

    async def register_strings(self, conn, s):
        await conn.execute("""INSERT INTO strings(string) VALUES($1);""", s)

    async def register_string_edge(self, conn, elem, sid, snum):
        await conn.fetchval("INSERT INTO string_edges(elem_id, sentence_num, string_id) VALUES($1, $2, $3)",
                        (elem.id, snum, sid))
