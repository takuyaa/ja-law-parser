from ja_law_parser.model import (
    AmendProvision,
    AmendProvisionSentence,
    NewProvision,
    ParagraphSentence,
    Sentence,
    Text,
)


class TestParagraph:
    def test_amend_provision(self) -> None:
        xml = """\
        <AmendProvision>
          <AmendProvisionSentence>
            <Sentence>テスト</Sentence>
          </AmendProvisionSentence>
          <NewProvision>
            <LawTitle>タイトル</LawTitle>
          </NewProvision>
          <NewProvision>
            <Preamble>
              <Paragraph Num="1"><ParagraphNum/><ParagraphSentence>
                <Sentence>テストの項文</Sentence>
              </ParagraphSentence></Paragraph>
            </Preamble>
          </NewProvision>
          <NewProvision>
            <Article Num="1">
              <ArticleCaption>テストの条見出し</ArticleCaption>
              <ArticleTitle>テストの条文タイトル</ArticleTitle>
                <Paragraph Num="1">
                  <ParagraphNum />
                  <ParagraphSentence>
                    <Sentence>テストの段</Sentence>
                  </ParagraphSentence>
                </Paragraph>
            </Article>
          </NewProvision>
        </AmendProvision>
        """
        amend_provision: AmendProvision = AmendProvision.from_xml(xml)

        amend_provision_sentence: AmendProvisionSentence = amend_provision.amend_provision_sentence

        sentences: list[Sentence] = amend_provision_sentence.sentences
        assert len(sentences) == 1

        sentence: Sentence = sentences[0]
        assert sentence.text == "テスト"

        assert len(sentence.contents) == 1
        assert type(sentence.contents[0]) == Text
        assert sentence.contents[0].text == "テスト"
        assert amend_provision.new_provisions is not None

        new_provisions: list[NewProvision] = amend_provision.new_provisions
        assert len(new_provisions) == 3

        assert new_provisions[0].law_title is not None
        assert new_provisions[0].law_title.text == "タイトル"

        assert new_provisions[1].preamble is not None
        assert len(new_provisions[1].preamble.paragraphs) == 1
        assert type(new_provisions[1].preamble.paragraphs[0].paragraph_sentence) == ParagraphSentence
