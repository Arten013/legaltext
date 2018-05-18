PREF_TABLE = """
CREATE TABLE IF NOT EXISTS prefecture(
code INTEGER PRIMARY KEY,
name TEXT NOT NULL
);
"""

MUNI_TABLE = """
CREATE TABLE IF NOT EXISTS municipality(
code INTEGER PRIMARY KEY,
pref_code INTEGER NOT NULL,
name TEXT NOT NULL,
FOREIGN KEY(pref_code) REFERENCES prefecture(code)
);
CREATE INDEX IF NOT EXISTS pref_code_index ON municipality(pref_code);
"""

ORD_TABLE = """
CREATE TABLE IF NOT EXISTS ordinance(
id INTEGER PRIMARY KEY,
muni_code INTEGER,
file_code INTEGER,
name TEXT NOT NULL,
num TEXT NOT NULL,
FOREIGN KEY(muni_code) REFERENCES municipality(code),
UNIQUE(muni_code, num)
);
CREATE INDEX IF NOT EXISTS muni_code_index ON ordinance(muni_code);
"""

ARTICLE_TABLE = """
CREATE TABLE IF NOT EXISTS article(
id INTEGER PRIMARY KEY,
ord_id INTEGER,
num INTEGER,
caption TEXT,
FOREIGN KEY(ord_id) REFERENCES ordinance(id),
UNIQUE(ord_id, num)
);
CREATE INDEX IF NOT EXISTS ord_id_index ON article(ord_id);
"""

PARAGRAPH_TABLE = """
CREATE TABLE IF NOT EXISTS paragraph(
id INTEGER PRIMARY KEY,
article_id INTEGER,
num INTEGER,
sentence TEXT,
FOREIGN KEY(article_id) REFERENCES article(id),
UNIQUE(article_id, num)
);
CREATE INDEX IF NOT EXISTS article_id_index ON paragraph(article_id);
"""

DATASET_TABLE = """
CREATE TABLE IF NOT EXISTS dataset(
id INTEGER PRIMARY KEY,
name TEXT NOT NULL UNIQUE,
root_type TEXT CHECK(root_type IN ("all", "prefecture", "municipality", "ordinance", "article")),
root_id INTEGER NOT NULL,
unit_type TEXT CHECK(unit_type IN ("prefecture", "municipality", "ordinance", "article", "paragraph")),
UNIQUE(root_type, root_id, unit_type)
);
"""

_MODEL_TABLE_BASE = """
CREATE TABLE IF NOT EXISTS {0}(
id INTEGER PRIMARY KEY,
name TEXT NOT NULL UNIQUE,
dataset_id INTEGER NOT NULL,
param_id INTEGER NOT NULL,
FOREIGN KEY(param_id) REFERENCES {0}_params(id),
FOREIGN KEY(dataset_id) REFERENCES dataset_table(id)
UNIQUE(dataset_id, param_id)
);
"""
DOC2VEC_TABLE = _MODEL_TABLE_BASE.format("doc2vec")
TFIDF_TABLE = _MODEL_TABLE_BASE.format("tfidf")
TFIDFSPM_TABLE = _MODEL_TABLE_BASE.format("tfidfspm")
SIMSTRING_TABLE = _MODEL_TABLE_BASE.format("simstring")
LDA_TABLE = _MODEL_TABLE_BASE.format("lda")
SPM_TABLE = _MODEL_TABLE_BASE.format("spm")
DOC2VECSPM_TABLE = _MODEL_TABLE_BASE.format("doc2vec_spm")

DOC2VEC_PARAMS_TABLE = """
CREATE TABLE IF NOT EXISTS doc2vec_params(
id INTEGER PRIMARY KEY,
epochs INTEGER DEFAULT 2,
alpha REAL DEFAULT 0.025,
min_alpha REAL DEFAULT 0.0001,
size INTEGER DEFAULT 100,
window INTEGER DEFAULT 5,
min_count INTEGER DEFAULT 5,
max_vocab_size INTEGER,
sample REAL DEFAULT 0.001,
seed INTEGER DEFAULT 1,
sg INTEGER DEFAULT 0,
hs INTEGER DEFAULT 0,
negative INTEGER DEFAULT 5,
cbow_mean INTEGER DEFAULT 1,
iter INTEGER DEFAULT 5,
null_word INTEGER DEFAULT 0,
sorted_vocab INTEGER DEFAULT 1,
batch_words INTEGER DEFAULT 10000,
dm_mean INTEGER DEFAULT 0,
dm INTEGER DEFAULT 1,
dbow_words INTEGER DEFAULT 0,
dm_concat INTEGER DEFAULT 0,
dm_tag_count INTEGER DEFAULT 1,
UNIQUE(
	epochs, alpha, min_alpha,
	size, window, min_count,
	max_vocab_size, sample, seed,
	sg, hs, negative, cbow_mean,
	iter, null_word, sorted_vocab,
	batch_words, dm_mean, dm,
	dbow_words, dm_concat, dm_tag_count
));
"""

DOC2VECSPM_PARAMS_TABLE = """
CREATE TABLE IF NOT EXISTS doc2vec_spm_params(
id INTEGER PRIMARY KEY,
epochs INTEGER DEFAULT 2,
alpha REAL DEFAULT 0.025,
min_alpha REAL DEFAULT 0.0001,
size INTEGER DEFAULT 100,
window INTEGER DEFAULT 5,
min_count INTEGER DEFAULT 5,
max_vocab_size INTEGER,
sample REAL DEFAULT 0.001,
seed INTEGER DEFAULT 1,
sg INTEGER DEFAULT 0,
hs INTEGER DEFAULT 0,
negative INTEGER DEFAULT 5,
cbow_mean INTEGER DEFAULT 1,
iter INTEGER DEFAULT 5,
null_word INTEGER DEFAULT 0,
sorted_vocab INTEGER DEFAULT 1,
batch_words INTEGER DEFAULT 10000,
dm_mean INTEGER DEFAULT 0,
dm INTEGER DEFAULT 1,
dbow_words INTEGER DEFAULT 0,
dm_concat INTEGER DEFAULT 0,
dm_tag_count INTEGER DEFAULT 1,
spm_id INTEGER DEFAULT 0,
UNIQUE(
	epochs, alpha, min_alpha,
	size, window, min_count,
	max_vocab_size, sample, seed,
	sg, hs, negative, cbow_mean,
	iter, null_word, sorted_vocab,
	batch_words, dm_mean, dm,
	dbow_words, dm_concat, dm_tag_count,
	spm_id
)
FOREIGN KEY(spm_id) REFERENCES spm(id)
);
"""

TFIDF_PARAMS_TABLE = """
CREATE TABLE IF NOT EXISTS tfidf_params(
id INTEGER PRIMARY KEY,
max_df FLOAT DEFAULT 1.0,
min_df INTEGER DEFAULT 1,
max_features INTEGER,
norm TEXT CHECK(norm IN (NULL, "l1", "l2")),
use_idf INTEGER DEFAULT 0,
UNIQUE(max_df, min_df, max_features, norm, use_idf)
);
"""

TFIDFSPM_PARAMS_TABLE = """
CREATE TABLE IF NOT EXISTS tfidfspm_params(
id INTEGER PRIMARY KEY,
max_df FLOAT DEFAULT 1.0,
min_df INTEGER DEFAULT 1,
max_features INTEGER DEFAULT 16000,
norm TEXT DEFAULT "l1" CHECK(norm IN (NULL, "l1", "l2")),
spm_id INTEGER DEFAULT 0,
UNIQUE(max_df, min_df, max_features, norm),
FOREIGN KEY(spm_id) REFERENCES spm(id)
);
"""

SIMSTRING_PARAMS_TABLE = """
CREATE TABLE IF NOT EXISTS simstring_params(
id INTEGER PRIMARY KEY,
ngram_size INTEGER DEFAULT 3,
UNIQUE(ngram_size)
);
"""

LDA_PARAMS_TABLE = """
CREATE TABLE IF NOT EXISTS lda_params(
id INTEGER PRIMARY KEY,
max_df FLOAT DEFAULT 1.0,
min_df INTEGER DEFAULT 1,
max_features INTEGER,
n_components INTEGER DEFAULT 2,
max_iter INTEGER DEFAULT 10,
UNIQUE(max_df, min_df, max_features, n_components, max_iter)
);
"""

SPM_PARAMS_TABLE = """
CREATE TABLE IF NOT EXISTS spm_params(
id INTEGER PRIMARY KEY,
vocab_size INTEGER DEFAULT 8000,
model_type TEXT CHECK(model_type IN ("unigram", "bpe", "char", "word")),
hide_num INTEGER DEFAULT 0 CHECK(hide_num IN (0, 1)),
UNIQUE(vocab_size, model_type, hide_num)
);
"""