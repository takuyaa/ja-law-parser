from typing import Optional

from ja_law_parser.model import (
    ArticleTitle,
    Fig,
    Line,
    QuoteStruct,
    Sentence,
    TaggedText,
    Text,
    WithArticleTitle,
    WithSentences,
)


class ArticleTitleContainer(WithArticleTitle, tag="ArticleTitleContainer"):
    """
    A virual pydantic-xml model that has the article_title for testing.
    """

    pass


class SentenceContainer(WithSentences, tag="SentenceContainer"):
    """
    A virual pydantic-xml model that has the sentences for testing.
    """

    pass


class TestTaggedText:
    def test_tagged_text_with_line(self) -> None:
        xml = """\
        <ArticleTitleContainer>
          <ArticleTitle>タイトルの<Line Style="dotted"><Ruby>テ<Rt>て</Rt></Ruby></Line><Ruby>ス<Rt>す</Rt></Ruby><Line><Ruby>ト<Rt>と</Rt></Ruby>デー</Line>タ</ArticleTitle>
        </ArticleTitleContainer>
        """  # noqa: E501
        article_title: Optional[ArticleTitle] = ArticleTitleContainer.from_xml(xml).article_title
        assert article_title is not None
        assert article_title.text == "タイトルのテストデータ"

        tagged_text = article_title.tagged_text
        assert tagged_text is not None
        assert len(tagged_text) == 5

        assert type(tagged_text[0]) == Text
        assert tagged_text[0].text == "タイトルの"

        assert type(tagged_text[1]) == Line
        assert tagged_text[1].text == "テ"
        assert tagged_text[1].style == "dotted"
        assert len(tagged_text[1].contents) == 1

        assert type(tagged_text[3]) == Line
        assert tagged_text[3].text == "トデー"
        assert tagged_text[3].style is None
        assert len(tagged_text[3].contents) == 2

        assert type(tagged_text[4]) == Text
        assert tagged_text[4].text == "タ"


class TestQuoteStruct:
    def test_quote_struct_in_sentence(self) -> None:
        xml = """\
        <SentenceContainer>
          <Sentence>AAA<QuoteStruct><Sentence><QuoteStruct><Fig src="url" /></QuoteStruct></Sentence></QuoteStruct> BBB</Sentence>
        </SentenceContainer>
        """  # noqa: E501
        sc: SentenceContainer = SentenceContainer.from_xml(xml)
        assert sc.sentences is not None
        sentences: list[Sentence] = sc.sentences
        assert len(sentences) == 1

        sentence: Sentence = sentences[0]
        assert sentence.text == "AAA BBB"

        assert len(sentence.contents) == 3

        assert type(sentence.contents[0]) == Text
        assert sentence.contents[0].text == "AAA"

        assert type(sentence.contents[1]) == QuoteStruct
        assert len(sentence.contents[1].contents) == 1

        assert type(sentence.contents[1].contents[0]) == Sentence
        sentence2: Sentence = sentence.contents[1].contents[0]
        assert type(sentence2) == Sentence
        assert len(sentence2.contents) == 1

        assert type(sentence2.contents[0]) == QuoteStruct
        quote_struct: QuoteStruct = sentence2.contents[0]
        assert type(quote_struct) == QuoteStruct
        assert len(quote_struct.contents) == 1
        assert type(quote_struct.contents[0]) == Fig
        assert quote_struct.contents[0].src == "url"

        assert type(sentence.contents[2]) == Text
        assert sentence.contents[2].text == " BBB"

    def test_quote_struct_in_line(self) -> None:
        xml = """\
        <ArticleTitleContainer>
          <ArticleTitle><Line><QuoteStruct><Fig src="url" /></QuoteStruct></Line></ArticleTitle>
        </ArticleTitleContainer>
        """
        article_title: Optional[ArticleTitle] = ArticleTitleContainer.from_xml(xml).article_title
        assert article_title is not None

        tagged_text: TaggedText = article_title.tagged_text
        assert tagged_text is not None
        assert len(tagged_text) == 1
        assert type(tagged_text[0]) == Line
        assert len(tagged_text[0].contents) == 1

        quote_struct: QuoteStruct = tagged_text[0].contents[0]
        assert type(quote_struct) == QuoteStruct
        assert len(quote_struct.contents) == 1
        assert type(quote_struct.contents[0]) == Fig
