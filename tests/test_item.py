from ja_law_parser.model import Item, Sentence, Subitem1, TableRow, TableStruct


class TestItem:
    def test_simple_item(self) -> None:
        xml = """\
        <Item Num="1">
          <ItemTitle>Item title</ItemTitle>
          <ItemSentence>
            <Sentence Num="1">Item sentence</Sentence>
          </ItemSentence>
        </Item>
        """
        item: Item = Item.from_xml(xml)
        assert item is not None
        assert list(item.texts()) == ["Item title", "Item sentence"]

        assert item.item_title.text == "Item title"

        assert len(item.item_sentence.sentences) == 1
        sentence: Sentence = item.item_sentence.sentences[0]
        assert sentence.text == "Item sentence"

    def test_item_with_subitem(self) -> None:
        xml = """\
        <Item Num="1">
          <ItemTitle>Item 1</ItemTitle>
          <ItemSentence>
            <Column Num="1">
              <Sentence Num="1">Sentence 1</Sentence>
            </Column>
          </ItemSentence>
          <Subitem1 Num="1">
            <Subitem1Title>Subitem 1</Subitem1Title>
            <Subitem1Sentence>
              <Sentence Num="1">Sentence 2</Sentence>
            </Subitem1Sentence>
          </Subitem1>
          <Subitem1 Num="2">
            <Subitem1Title>Subitem 2</Subitem1Title>
            <Subitem1Sentence>
              <Sentence Num="1">Sentence 3</Sentence>
            </Subitem1Sentence>
          </Subitem1>
        </Item>
        """
        # Item
        item: Item = Item.from_xml(xml)
        assert item is not None
        assert item.item_title.text == "Item 1"
        assert len(item.item_sentence.columns) == 1
        assert len(item.subitems) == 2
        assert list(item.texts()) == ["Item 1", "Sentence 1", "Subitem 1", "Sentence 2", "Subitem 2", "Sentence 3"]

        # Subitem1
        subitem1_1: Subitem1 = item.subitems[0]
        assert subitem1_1.subitem1_title.text == "Subitem 1"
        assert len(subitem1_1.subitem1_sentence.sentences) == 1
        assert subitem1_1.subitem1_sentence.sentences[0].text == "Sentence 2"
        assert list(subitem1_1.texts()) == ["Subitem 1", "Sentence 2"]
        subitem1_2: Subitem1 = item.subitems[1]
        assert subitem1_2.subitem1_title.text == "Subitem 2"
        assert len(subitem1_2.subitem1_sentence.sentences) == 1
        assert subitem1_2.subitem1_sentence.sentences[0].text == "Sentence 3"
        assert list(subitem1_2.texts()) == ["Subitem 2", "Sentence 3"]

    def test_item_with_table_struct(self) -> None:
        xml = """\
        <Item Num="1">
          <ItemTitle>Item 1</ItemTitle>
          <ItemSentence>
            <Sentence Num="1">Sentence 1</Sentence>
          </ItemSentence>
          <TableStruct>
            <Table WritingMode="vertical">
              <TableRow>
                <TableColumn BorderBottom="solid" BorderLeft="solid" BorderRight="solid" BorderTop="solid">
                  <Sentence Num="1">Sentence 2</Sentence>
                </TableColumn>
                <TableColumn BorderBottom="solid" BorderLeft="solid" BorderRight="solid" BorderTop="solid">
                  <Sentence Num="1">Sentence 3</Sentence>
                </TableColumn>
              </TableRow>
            </Table>
          </TableStruct>
        </Item>
        """
        # Item
        item: Item = Item.from_xml(xml)
        assert item is not None
        assert item.item_title.text == "Item 1"
        assert len(item.item_sentence.sentences) == 1
        assert len(item.table_structs) == 1
        # TODO assert list(item.texts()) ==

        # TableStruct
        table_struct: TableStruct = item.table_structs[0]
        assert len(table_struct.table.table_rows) == 1
        table_row: TableRow = table_struct.table.table_rows[0]
        assert len(table_row.table_columns) == 2
        assert len(table_row.table_columns[0].sentences) == 1
        assert len(table_row.table_columns[1].sentences) == 1
        # TODO assert list(table_struct.texts()) ==
