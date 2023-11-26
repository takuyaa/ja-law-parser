import os
from pathlib import Path

from ja_law_parser.model import (
    TOC,
    Article,
    ArticleCaption,
    ArticleTitle,
    Law,
    LawBody,
    LawTitle,
    MainProvision,
    Paragraph,
    ParagraphNum,
    Ruby,
    Sentence,
    SupplProvision,
    SupplProvisionLabel,
    Text,
    TOCSupplProvision,
)
from ja_law_parser.parser import LawParser


class TestParser:
    xml_dir = Path(os.path.dirname(__file__)) / "xml"

    def test_parse_simple_law(self) -> None:
        parser = LawParser()
        file = self.xml_dir / "simple_law.xml"

        law: Law = parser.parse(path=file)

        # Law
        assert law.era == "Reiwa"
        assert law.year == 1
        assert law.num == 1
        assert law.law_type == "Act"
        assert law.lang == "ja"
        assert law.promulgate_month == 1
        assert law.promulgate_day == 31
        assert law.law_num == "令和一年テスト一号"

        # LawBody
        law_body: LawBody = law.law_body
        assert law_body.subject is None
        assert type(law_body.law_title) == LawTitle

        # LawBody.LawTitle
        law_title: LawTitle = law_body.law_title
        assert law_title.kana == "たいとるのてすとでーた"
        assert law_title.abbrev == ""
        assert law_title.abbrev_kana is None
        assert law_title.text == "タイトルのテストデータ"

        # LawBody.LawTitle.tagged_text
        tagged_text = law_title.tagged_text
        assert tagged_text is not None
        assert len(tagged_text) == 5
        assert type(tagged_text[0]) == Text
        assert tagged_text[0].text == "タイトルの"
        assert type(tagged_text[1]) == Ruby
        assert tagged_text[1].text == "テ"
        assert tagged_text[1].rt is not None
        assert tagged_text[1].rt[0] == "て"
        assert type(tagged_text[4]) == Text
        assert tagged_text[4].text == "データ"

        # LawBody.MainProvision
        main_provision: MainProvision = law_body.main_provision
        assert main_provision.extract is None
        main_articles: list[Article] = main_provision.articles
        assert len(main_articles) == 3
        assert main_provision.parts is None
        assert main_provision.chapters is None
        assert main_provision.sections is None
        assert main_provision.paragraphs is None

        # LawBody.MainProvision.Article
        article1: Article = main_provision.articles[0]
        assert type(article1.article_caption) == ArticleCaption
        article1_caption: ArticleCaption = article1.article_caption
        assert article1_caption.text == "（目的）"
        assert type(article1.article_title) == ArticleTitle
        article1_title: ArticleTitle = article1.article_title
        assert article1_title.text == "第一条"
        assert len(article1.paragraphs) == 1

        # LawBody.MainProvision.Article.Paragraph
        paragraph1_1: Paragraph = article1.paragraphs[0]
        assert type(paragraph1_1) == Paragraph
        assert paragraph1_1.num == 1
        assert type(paragraph1_1.paragraph_num) == ParagraphNum
        paragraph_num: ParagraphNum = paragraph1_1.paragraph_num
        assert paragraph_num.text == ""

        # LawBody.MainProvision.Article.Paragraph.ParagraphSentence
        sentences1_1: list[Sentence] = paragraph1_1.paragraph_sentence.sentences
        assert len(sentences1_1) == 1

        # LawBody.MainProvision.Article.Paragraph.ParagraphSentence.Sentence
        sentence1_1_1: Sentence = sentences1_1[0]
        assert type(sentence1_1_1) == Sentence
        assert sentence1_1_1.text == "このテストデータはパーサーをテストすることを目的とする。"

        # LawBody.SupplProvision
        suppl_provisions: list[SupplProvision] = law_body.suppl_provisions
        assert len(suppl_provisions) == 1
        suppl_provision1: SupplProvision = suppl_provisions[0]
        assert suppl_provision1.extract is True
        assert type(suppl_provision1.suppl_provision_label) == SupplProvisionLabel
        suppl_provision_label: SupplProvisionLabel = suppl_provision1.suppl_provision_label
        assert suppl_provision_label.text == "附　則"
        assert suppl_provision1.articles is not None
        assert len(suppl_provision1.articles) == 2
        assert suppl_provision1.chapters is None
        assert suppl_provision1.paragraphs is None

        # LawBody.SupplProvision.Article
        suppl_article1: Article = suppl_provision1.articles[0]
        assert type(suppl_article1) == Article
        assert suppl_article1.num == "1"
        suppl_article1_caption: ArticleCaption = suppl_article1.article_caption
        assert suppl_article1_caption.text == "（施行期日）"
        suppl_article1_title: ArticleTitle = suppl_article1.article_title
        assert suppl_article1_title.text == "第一条"
        assert len(suppl_article1.paragraphs) == 1

        # LawBody.SupplProvision.Article.Paragraph
        suppl_paragraph1_1: Paragraph = suppl_article1.paragraphs[0]
        assert type(suppl_paragraph1_1) == Paragraph
        assert suppl_paragraph1_1.num == 1
        suppl_paragraph1_1_num: ParagraphNum = suppl_paragraph1_1.paragraph_num
        assert suppl_paragraph1_1_num.text == ""

        # LawBody.SupplProvision.Article.Paragraph.ParagraphSentence
        suppl_sentences1_1: list[Sentence] = suppl_paragraph1_1.paragraph_sentence.sentences
        assert len(suppl_sentences1_1) == 1

        # LawBody.SupplProvision.Article.Paragraph.ParagraphSentence.Sentence
        suppl_sentence1_1_1: Sentence = suppl_sentences1_1[0]
        assert type(suppl_sentence1_1_1) == Sentence
        assert suppl_sentence1_1_1.text == "このテストは、公布の日から施行する。"

    def test_parse_law_with_toc(self) -> None:
        parser = LawParser()
        file = self.xml_dir / "law_with_toc.xml"

        law: Law = parser.parse(path=file)

        # Law
        assert law.era == "Heisei"
        assert law.year == 23
        assert law.num == 1
        assert law.law_type == "Act"
        assert law.lang == "ja"
        assert law.promulgate_month == 1
        assert law.promulgate_day == 1
        assert law.law_num == "平成二十三年法律第一号"

        # LawBody
        law_body: LawBody = law.law_body
        assert law_body.toc is not None

        # TOC
        toc: TOC = law_body.toc
        assert toc.toc_label == "目次"
        assert toc.toc_preamble_label is None
        assert toc.toc_parts is None
        assert toc.toc_sections is None
        assert toc.toc_articles is None
        assert toc.toc_chapters is not None
        assert len(toc.toc_chapters) == 2
        assert type(toc.toc_suppl_provision) == TOCSupplProvision
        assert toc.toc_suppl_provision.suppl_provision_label is not None
        assert toc.toc_suppl_provision.suppl_provision_label.text == "附則"
        assert toc.toc_suppl_provision.toc_articles is None
        assert toc.toc_suppl_provision.toc_chapters is None
