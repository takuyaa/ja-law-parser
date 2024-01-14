from ja_law_parser.model import Subitem1, Subitem2, Table, TableColumn, TableRow


class TestSentence:
    def test_sentence(self) -> None:
        xml = """\
        <Table>
          <TableRow>
            <TableColumn Valign="top">
              <Subitem1 Num="1">
                <Subitem1Title>イ</Subitem1Title>
                <Subitem1Sentence>
                  <Sentence>Subitem1 sentence</Sentence>
                </Subitem1Sentence>
                <Subitem2 Num="1">
                  <Subitem2Title>（１）</Subitem2Title>
                  <Subitem2Sentence>
                    <Sentence>Subitem2 sentence 1</Sentence>
                  </Subitem2Sentence>
                </Subitem2>
                <Subitem2 Num="2">
                  <Subitem2Title>（２）</Subitem2Title>
                  <Subitem2Sentence>
                    <Sentence>Subitem2 sentence 2</Sentence>
                  </Subitem2Sentence>
                </Subitem2>
              </Subitem1>
            </TableColumn>
          </TableRow>
        </Table>
        """
        table: Table = Table.from_xml(xml)
        assert len(table.table_rows) == 1

        table_row: TableRow = table.table_rows[0]
        assert len(table_row.table_columns) == 1

        table_column: TableColumn = table_row.table_columns[0]
        assert len(table_column.subitems1) == 1
        assert table_column.valign == "top"
        assert list(table_column.texts()) == [
            "イ",
            "Subitem1 sentence",
            "（１）",
            "Subitem2 sentence 1",
            "（２）",
            "Subitem2 sentence 2",
        ]

        subitem1: Subitem1 = table_column.subitems1[0]
        assert subitem1.num == "1"
        assert subitem1.subitem1_title.text == "イ"
        assert len(subitem1.subitem1_sentence.sentences) == 1
        assert subitem1.subitem1_sentence.sentences[0].text == "Subitem1 sentence"
        assert len(subitem1.subitems2) == 2
        assert list(subitem1.texts()) == [
            "イ",
            "Subitem1 sentence",
            "（１）",
            "Subitem2 sentence 1",
            "（２）",
            "Subitem2 sentence 2",
        ]

        subitem2_1: Subitem2 = subitem1.subitems2[0]
        assert subitem2_1.num == "1"
        assert subitem2_1.subitem2_title.text == "（１）"
        assert len(subitem2_1.subitem2_sentence.sentences) == 1
        assert subitem2_1.subitem2_sentence.sentences[0].text == "Subitem2 sentence 1"
        assert list(subitem2_1.texts()) == ["（１）", "Subitem2 sentence 1"]

        subitem2_2: Subitem2 = subitem1.subitems2[1]
        assert subitem2_2.num == "2"
        assert subitem2_2.subitem2_title.text == "（２）"
        assert len(subitem2_2.subitem2_sentence.sentences) == 1
        assert subitem2_2.subitem2_sentence.sentences[0].text == "Subitem2 sentence 2"
        assert list(subitem2_2.texts()) == ["（２）", "Subitem2 sentence 2"]
