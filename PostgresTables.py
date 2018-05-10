from EType import ETYPES

PREF_TABLE = """
CREATE TABLE IF NOT EXISTS prefectures(
id SMALLINT PRIMARY KEY,
name VARCHAR(50) NOT NULL
);
CREATE INDEX IF NOT EXISTS pref_id_index ON prefectures(id);
"""

MUNI_TABLE = """
CREATE TABLE IF NOT EXISTS municipalities(
id SMALLINT PRIMARY KEY,
pref_id SMALLINT NOT NULL REFERENCES prefectures(id),
name VARCHAR(50) NOT NULL
);
CREATE INDEX IF NOT EXISTS muni_id_index ON municipalities(id);
"""

ORD_TABLE = """
CREATE TABLE IF NOT EXISTS ordinances(
id INTEGER PRIMARY KEY,
muni_id INTEGER REFERENCES municipalities(id),
file_id INTEGER,
name VARCHAR(500) NOT NULL,
num VARCHAR(50) NOT NULL,
UNIQUE(muni_id, num)
);
CREATE INDEX IF NOT EXISTS ord_id_index ON ordinances(id);
CREATE INDEX IF NOT EXISTS file_id_index ON ordinances(file_id);
"""

ELEMENTS_TABLE = """
CREATE TYPE IF NOT EXISTS ETYPE AS ENUM ({etypes});
CREATE TABLE IF NOT EXISTS elements(
id INTEGER PRIMARY KEY,
parent_id INTEGER,
ord_id INTEGER,
etype ETYPE,
num VARCHAR(50),
content TEXT,
FOREIGN KEY(ord_id) REFERENCES ordinances(id),
UNIQUE(parent_id, num, etype)
);
CREATE INDEX IF NOT EXISTS elem_id_index ON elements(id);
""".format(etypes=", ".join(map(lambda x: "'{}'".format(x), ETYPES)))

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
string_id INTEGER REFERENCES strings(id)
UNIQUE(elem_id, sentence_num),
);
CREATE INDEX IF NOT EXISTS string_edges_id_index ON string_edges(id);
"""