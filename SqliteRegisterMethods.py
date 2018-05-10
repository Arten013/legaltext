class SqliteRegisterInstruction(object):
    async def search_oid(self, conn):
        res = await conn.exec_in_transaction(
                "SELECT id FROM ordinances WHERE num=? AND muni_id=?;",
                (self.num, self.municipality_code)
            ).fetchone()
        return None if res is None else res[0]

    async def register_law(self, conn):
        await conn.exec_in_transaction("""
            INSERT INTO ordinances(muni_id, file_id, name, num) VALUES(:mc, :fc, :name, :num);
            """,
            {"mc":self.municipality_code, "fc":self.file_code, "name":self.name, "num":self.num}
        )

    async def search_elements(self, conn, elem):
        res = await conn.exec_in_transaction("""
            SELECT id FROM elements WHERE parent_id=:pid AND etype=:etype AND num=:num;"
            """,
            {"pid":elem.parent.id, "etype":elem.etype, "num":str(elem.num.num), "orid":self.oid, "content":"".join(elem.texts)}
            ).fetchone()
        return None if res is None else res[0]

    async def register_elements(self, conn, elem):
        await conn.exec_in_transaction("""
            INSERT INTO elements(parent_id, ord_id, etype, num, content) VALUES(:pid, :orid, :etype, :num, :content);
            """,
            {"pid":elem.parent.id, "etype":elem.etype, "num":str(elem.num.num), "orid":self.oid, "content":"".join(elem.texts)}
            )

    async def search_string(self, conn, s):
        res = await conn.exec_in_transaction("SELECT id FROM strings WHERE string=?;", (s,)).fetchone()
        return None if res is None else res[0]

    async def register_strings(self, conn, s):
        await conn.exec_in_transaction("""INSERT INTO strings(string) VALUES(?);""", (s,))

    async def register_string_edge(self, conn, elem, sid, snum):
        await conn.exec_in_transaction("INSERT INTO string_edges(elem_id, sentence_num, string_id) VALUES(?, ?, ?)",
                        (elem.id, snum, sid))