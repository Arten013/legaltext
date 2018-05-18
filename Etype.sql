DROP TYPE IF EXISTS ELEMENTTYPE CASCADE;
CREATE TYPE ELEMENTTYPE AS ENUM (
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
