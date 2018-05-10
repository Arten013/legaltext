PREF_TABLE = """
CREATE TABLE IF NOT EXISTS prefectures(
id INTEGER PRIMARY KEY,
name TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS pref_id_index ON prefectures(id);
"""

MUNI_TABLE = """
CREATE TABLE IF NOT EXISTS municipalities(
id INTEGER PRIMARY KEY,
pref_id INTEGER NOT NULL,
name TEXT NOT NULL,
FOREIGN KEY(pref_id) REFERENCES prefectures(id)
);
CREATE INDEX IF NOT EXISTS muni_id_index ON municipalities(id);
"""

ORD_TABLE = """
CREATE TABLE IF NOT EXISTS ordinances(
id INTEGER PRIMARY KEY,
muni_id INTEGER,
file_id INTEGER,
name TEXT NOT NULL,
num TEXT NOT NULL,
FOREIGN KEY(muni_id) REFERENCES municipalities(id),
UNIQUE(muni_id, num)
);
CREATE INDEX IF NOT EXISTS ord_id_index ON ordinances(id);
CREATE INDEX IF NOT EXISTS file_id_index ON ordinances(file_id);
"""

ELEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS elements(
id INTEGER PRIMARY KEY,
parent_id INTEGER,
ord_id INTEGER,
etype TEXT,
num TEXT,
content TEXT,
FOREIGN KEY(ord_id) REFERENCES ordinances(id),
UNIQUE(parent_id, num, etype)
);
CREATE INDEX IF NOT EXISTS elem_id_index ON elements(id);
"""

STRINGS_TABLE = """
CREATE TABLE IF NOT EXISTS strings(
id INTEGER PRIMARY KEY,
string TEXT UNIQUE,
);
CREATE INDEX IF NOT EXISTS string_id_index ON strings(id);
CREATE INDEX IF NOT EXISTS string_index ON strings(string);
"""

STRING_EDGES_TABLE = """
CREATE TABLE IF NOT EXISTS string_edges(
id INTEGER PRIMARY KEY,
elem_id INTEGER,
sentence_num INTEGER,
string_id TEXT,
UNIQUE(elem_id, sentence_num),
FOREIGN KEY(string_id) REFERENCES strings(id)
);
CREATE INDEX IF NOT EXISTS string_edges_id_index ON string_edges(id);
"""