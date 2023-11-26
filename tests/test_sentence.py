from ja_law_parser.model import Column, Line, Sentence


class TestSentence:
    def test_sentence(self) -> None:
        xml = """\
        <Column Num="1">
          <Sentence Num="1" Function="proviso" Indent="Item" WritingMode="vertical"><Line>段<Ruby>の<Rt>ノ</Rt></Ruby>テスト</Line></Sentence>
        </Column>
        """  # noqa: E501
        sentences: list[Sentence] = Column.from_xml(xml).sentences
        assert len(sentences) == 1

        sentence: Sentence = sentences[0]
        assert sentence.text == "段のテスト"

        assert sentence.num == 1
        assert sentence.function == "proviso"
        assert sentence.indent == "Item"
        assert sentence.writing_mode == "vertical"

        assert len(sentence.contents) == 1
        assert type(sentence.contents[0]) == Line
