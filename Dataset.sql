DROP TABLE IF EXISTS dataset;
CREATE TABLE datasets(
id SERIAL PRIMARY KEY,
name VARCHAR(50),
);

CREATE TABLE dataset_elements(
dataset_id INTEGER REFERENCES datasets(id) ON DELETE RESTRICT,
element_id INTEGER REFERENCES elements(id) ON DELETE RESTRICT,
)
CREATE INDEX dataset_elements_dataset_id_idx ON dataset_elements(dataset_id)
CREATE INDEX dataset_elements_element_id_idx ON dataset_elements(element_id)

CREATE TABLE IF NOT EXISTS models(
id SERIAL PRIMARY KEY,
name VARCHAR(50) NOT NULL,
model_type VARCHAR(50)
dataset_id INTEGER NOT NULL,
FOREIGN KEY(dataset_id) REFERENCES datasets(id)
UNIQUE(name, model_type)
);