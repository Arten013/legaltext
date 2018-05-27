
DROP TABLE IF EXISTS models;
DROP TABLE IF EXISTS datasets;
CREATE TABLE datasets(
id SERIAL PRIMARY KEY,
name VARCHAR(50) NOT NULL UNIQUE,
unit_type ELEMENTTYPE,
ordinance_id_list BIGINT[] NOT NULL
);

DROP TABLE IF EXISTS models;
CREATE TABLE models(
id SERIAL PRIMARY KEY,
name VARCHAR(50) NOT NULL,
model_type VARCHAR(50),
dataset_id INTEGER NOT NULL,
FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
UNIQUE(name, model_type, dataset_id)
);
CREATE INDEX models_dataset_id_idx ON models(dataset_id);