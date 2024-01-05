from typing import Optional

from ja_law_parser.model import (
    EnactStatement,
    LawBody,
    LawTitle,
    Ruby,
    TaggedText,
    Text,
    WithArticleTitle,
)


class ArticleTitleContainer(WithArticleTitle, tag="ArticleTitleContainer"):
    """
    A virual pydantic-xml model that has the article_title for testing TaggedText.
    """

    pass


class TestLawBody:
    def test_simple_law_body(self) -> None:
        xml = """\
        <LawBody>
          <LawTitle Kana="たいとる" Abbrev="">タイトル</LawTitle>
          <MainProvision>
            <Article Num="1">
              <ArticleCaption>（条見出し）</ArticleCaption>
              <ArticleTitle>条名</ArticleTitle>
              <Paragraph Num="1">
                <ParagraphSentence>
                  <Sentence>条文</Sentence>
                </ParagraphSentence>
              </Paragraph>
            </Article>
          </MainProvision>
          <SupplProvision>
            <SupplProvisionLabel>附　則</SupplProvisionLabel>
            <Paragraph Num="1">
              <ParagraphNum/>
              <ParagraphSentence>
                <Sentence Num="1">附則文</Sentence>
              </ParagraphSentence>
            </Paragraph>
          </SupplProvision>
        </LawBody>
        """  # noqa: E501
        law_body: LawBody = LawBody.from_xml(xml)
        assert list(law_body.texts()) == ["タイトル", "（条見出し）", "条名", "条文", "附　則", "附則文"]

    def test_law_title(self) -> None:
        xml = """\
        <LawBody>
          <LawTitle Kana="たいとるのてすとでーた" Abbrev="">タイトルの<Ruby>テ<Rt>て</Rt></Ruby><Ruby>ス<Rt>す</Rt></Ruby><Ruby>ト<Rt>と</Rt></Ruby>データ</LawTitle>
          <MainProvision><Article Num="1"><Paragraph Num="1"><ParagraphSentence><Sentence></Sentence></ParagraphSentence></Paragraph></Article></MainProvision>
        </LawBody>
        """  # noqa: E501
        law_title: Optional[LawTitle] = LawBody.from_xml(xml).law_title
        assert law_title is not None
        assert law_title.kana == "たいとるのてすとでーた"
        assert law_title.abbrev == ""
        assert law_title.abbrev_kana is None
        assert law_title.text == "タイトルのテストデータ"

        tagged_text: TaggedText = law_title.tagged_text
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

    def test_enact_statement(self) -> None:
        xml = """\
        <LawBody>
          <EnactStatement>覚<Ruby>せ<Rt>ヽ</Rt></Ruby><Ruby>い<Rt>ヽ</Rt></Ruby>剤取締法</EnactStatement>
          <MainProvision><Article Num="1"><Paragraph Num="1"><ParagraphSentence><Sentence></Sentence></ParagraphSentence></Paragraph></Article></MainProvision>
        </LawBody>
        """  # noqa: E501
        enact_statement: Optional[EnactStatement] = LawBody.from_xml(xml).enact_statement
        assert enact_statement is not None
        assert enact_statement.text == "覚せい剤取締法"

        tagged_text: TaggedText = enact_statement.tagged_text
        assert tagged_text is not None
        assert len(tagged_text) == 4

        assert type(tagged_text[0]) == Text
        assert tagged_text[0].text == "覚"

        assert type(tagged_text[1]) == Ruby
        assert tagged_text[1].text == "せ"
        assert tagged_text[1].rt is not None
        assert tagged_text[1].rt[0] == "ヽ"

        assert type(tagged_text[1]) == Ruby
        assert tagged_text[2].text == "い"
        assert tagged_text[2].rt is not None
        assert tagged_text[2].rt[0] == "ヽ"

        assert type(tagged_text[3]) == Text
        assert tagged_text[3].text == "剤取締法"
