from ja_law_parser.model import Article, ArticleCaption, Line, TaggedText, Text


class TestArticle:
    def test_article_caption(self) -> None:
        xml = """
        <Article Num="132">
          <ArticleCaption>テスト<Line><ArithFormula><Fig src="./pict/2JH00000021313.jpg"/></ArithFormula></Line>の見出し</ArticleCaption>
          <ArticleTitle>テストの条名</ArticleTitle>
          <Paragraph Num="1"><ParagraphNum/><ParagraphSentence><Sentence Num="1" WritingMode="vertical">テストの項文</Sentence></ParagraphSentence></Paragraph>
        </Article>
        """  # noqa: E501

        article_caption: ArticleCaption = Article.from_xml(xml).article_caption
        assert article_caption is not None
        assert article_caption.text == "テストの見出し"
        tagged_text: TaggedText = article_caption.tagged_text
        assert len(tagged_text) == 3
        e0: Text = tagged_text[0]
        assert type(e0) == Text
        assert e0.text == "テスト"
        e1: Line = tagged_text[1]
        assert type(e1) == Line
        assert e1.contents
