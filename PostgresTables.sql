DROP TABLE IF EXISTS element_strings;
DROP TABLE IF EXISTS strings;
DROP TABLE IF EXISTS elements;
DROP TABLE IF EXISTS ordinances;
DROP TABLE IF EXISTS municipalities;
DROP TABLE IF EXISTS prefectures;

CREATE TABLE prefectures(
id SMALLINT PRIMARY KEY,
name VARCHAR(50) NOT NULL
);

CREATE TABLE municipalities(
id INT PRIMARY KEY,
prefecture_id SMALLINT NOT NULL,
name VARCHAR(50) NOT NULL,
FOREIGN KEY(prefecture_id) REFERENCES prefectures(id) ON DELETE CASCADE
);

CREATE TABLE ordinances(
id SERIAL PRIMARY KEY,
municipality_id INTEGER,
file_id INTEGER,
name VARCHAR(500) NOT NULL,
num VARCHAR(500) NOT NULL,
UNIQUE(municipality_id, num),
FOREIGN KEY(municipality_id) REFERENCES municipalities(id) ON DELETE CASCADE
);
CREATE INDEX ordinances_file_id_idx ON ordinances(file_id);

CREATE TABLE elements(
id SERIAL PRIMARY KEY,
parent_id INTEGER,
ordinance_id INTEGER,
etype ELEMENTTYPE,
num NUMERIC,
content TEXT,
UNIQUE(parent_id, num, etype),
FOREIGN KEY(ordinance_id) REFERENCES ordinances(id) ON DELETE CASCADE
);
CREATE INDEX elements_ordinance_id_idx ON elements(ordinance_id);

CREATE TABLE strings(
id SERIAL PRIMARY KEY,
string TEXT CONSTRAINT string_unique UNIQUE,
count INTEGER
);

CREATE TABLE element_strings(
id SERIAL PRIMARY KEY,
element_id INTEGER,
sentence_num INTEGER,
string_id INTEGER,
UNIQUE(element_id, sentence_num),
FOREIGN KEY(element_id) REFERENCES elements(id) ON DELETE CASCADE,
FOREIGN KEY(string_id) REFERENCES strings(id) ON DELETE CASCADE
);
CREATE INDEX element_strings_element_id_idx ON element_strings(element_id);
CREATE INDEX element_strings_string_id_idx ON element_strings(string_id);
