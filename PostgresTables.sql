
DROP TYPE IF EXISTS ELEMENTTYPE CASCADE;
CREATE TYPE ELEMENTTYPE AS ENUM (
'ROOT',
'Law',
'LawNum',
'PromulgateStatement',
'PromulgateBody',
'ImperialSignature',
'PromulgateDate',
'Signature',
'MinisterialTitle',
'Name',
'LawBody',
'LawTitle',
'EnactStatement',
'TOC',
'TOCLabel',
'TOCPreambleLabel',
'TOCPart',
'TOCChapter',
'TOCSection',
'TOCSubsection',
'TOCDivision',
'TOCArticle',
'TOCSupplProvision',
'TOCAppdxTableLabel',
'ArticleRange',
'Preamble',
'MainProvision',
'Part',
'PartTitle',
'Chapter',
'ChapterTitle',
'Section',
'SectionTitle',
'Subsection',
'SubsectionTitle',
'Division',
'DivisionTitle',
'Article',
'ArticleTitle',
'ArticleCaption',
'Paragraph',
'ParagraphCaption',
'ParagraphNum',
'ParagraphSentence',
'SupplNote',
'AmendProvision',
'AmendProvisionSentence',
'NewProvision',
'Class',
'ClassTitle',
'ClassSentence',
'Item',
'ItemTitle',
'ItemSentence',
'Subitem1',
'Subitem1Title',
'Subitem1Sentence',
'Subitem2',
'Subitem2Title',
'Subitem2Sentence',
'Subitem3',
'Subitem3Title',
'Subitem3Sentence',
'Sentence',
'Column',
'SupplProvision',
'SupplProvisionLabel',
'SupplProvisionAppdxTable',
'SupplProvisionAppdxTableTitle',
'AppdxTable',
'AppdxTableTitle',
'AppdxNote',
'AppdxNoteTitle',
'AppdxStyle',
'AppdxStyleTitle',
'AppdxFormat',
'AppdxFormatTitle',
'Appdx',
'ArithFormulaNum',
'ArithFormula',
'AppdxFig',
'AppdxFigTitle',
'TableStruct',
'TableStructTitle',
'Table',
'TableRow',
'TableHeaderRow',
'TableHeaderColumn',
'TableColumn',
'FigStruct',
'FigStructTitle',
'Fig',
'NoteStruct',
'NoteStructTitle',
'Note',
'StyleStruct',
'StyleStructTitle',
'Style',
'FormatStruct',
'FormatStructTitle',
'Format',
'RelatedArticleNum',
'Remarks',
'RemarksLabel'
);

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
FOREIGN KEY(prefecture_id) REFERENCES prefectures(id) ON DELETE RESTRICT
);

CREATE TABLE ordinances(
id SERIAL PRIMARY KEY,
municipality_id INTEGER,
file_id INTEGER,
name VARCHAR(500) NOT NULL,
num VARCHAR(500) NOT NULL,
UNIQUE(municipality_id, num),
FOREIGN KEY(municipality_id) REFERENCES municipalities(id) ON DELETE RESTRICT
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
FOREIGN KEY(ordinance_id) REFERENCES ordinances(id) ON DELETE RESTRICT
);
CREATE INDEX elements_ordinance_id_idx ON elements(ordinance_id);
CREATE INDEX elements_parent_id_idx ON elements(parent_id);

CREATE TABLE strings(
id SERIAL PRIMARY KEY,
string TEXT UNIQUE,
count INTEGER
);
CREATE INDEX strings_string_idx ON strings(string);

CREATE TABLE element_strings(
id SERIAL PRIMARY KEY,
element_id INTEGER,
sentence_num INTEGER,
string_id INTEGER,
UNIQUE(element_id, sentence_num),
FOREIGN KEY(element_id) REFERENCES elements(id) ON DELETE RESTRICT,
FOREIGN KEY(string_id) REFERENCES strings(id) ON DELETE RESTRICT
);
CREATE INDEX element_strings_element_id_idx ON element_strings(element_id);
CREATE INDEX element_strings_string_id_idx ON element_strings(string_id);
