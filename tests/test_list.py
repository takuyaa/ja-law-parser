from ja_law_parser.model import List, Sublist1, Sublist2, Sublist3


class TestList:
    def test_list_with_sublists(self) -> None:
        xml = """\
        <List>
          <ListSentence>
            <Sentence>List sentence</Sentence>
          </ListSentence>
          <Sublist1>
            <Sublist1Sentence>
              <Column Num="1">
                <Sentence>Sublist1Sentence 1</Sentence>
              </Column>
            </Sublist1Sentence>
            <Sublist2>
              <Sublist2Sentence>
                <Sentence>Sublist2Sentence 1</Sentence>
              </Sublist2Sentence>
              <Sublist3>
                <Sublist3Sentence>
                  <Sentence>Sublist3Sentence 1</Sentence>
                </Sublist3Sentence>
              </Sublist3>
            </Sublist2>
          </Sublist1>
          <Sublist1>
            <Sublist1Sentence>
              <Column Num="1">
                <Sentence>Sublist1Sentence 2</Sentence>
              </Column>
            </Sublist1Sentence>
            <Sublist2>
              <Sublist2Sentence>
                <Sentence>Sentence2Sentence 2</Sentence>
              </Sublist2Sentence>
              <Sublist3>
                <Sublist3Sentence>
                  <Sentence>Sublist3Sentence 2</Sentence>
                </Sublist3Sentence>
              </Sublist3>
            </Sublist2>
            <Sublist2>
              <Sublist2Sentence>
                <Sentence>Sublist2Sentence 3</Sentence>
              </Sublist2Sentence>
              <Sublist3>
                <Sublist3Sentence>
                  <Column Num="1">
                    <Sentence>Sublist3Sentence 3</Sentence>
                  </Column>
                </Sublist3Sentence>
              </Sublist3>
              <Sublist3>
                <Sublist3Sentence>
                  <Column Num="1">
                    <Sentence>Sublist3Sentence 4</Sentence>
                  </Column>
                </Sublist3Sentence>
              </Sublist3>
            </Sublist2>
          </Sublist1>
          <Sublist1>
            <Sublist1Sentence>
              <Column Num="1">
                <Sentence>Sublist1Sentence 3</Sentence>
              </Column>
            </Sublist1Sentence>
          </Sublist1>
        </List>
        """
        list_: List = List.from_xml(xml)
        assert len(list_.list_sentence.sentences) == 1
        assert list_.list_sentence.sentences[0].text == "List sentence"
        assert len(list_.sublists1) == 3

        # Sublist1[0]
        sublist1_1: Sublist1 = list_.sublists1[0]
        assert len(sublist1_1.sublist1_sentence.columns) == 1
        assert len(sublist1_1.sublist1_sentence.columns[0].sentences) == 1
        assert sublist1_1.sublist1_sentence.columns[0].sentences[0].text == "Sublist1Sentence 1"
        assert len(sublist1_1.sublists2) == 1

        # Sublist1[0].Sublist2[0]
        sublist2_1: Sublist2 = sublist1_1.sublists2[0]
        assert len(sublist2_1.sublist2_sentence.sentences) == 1
        assert sublist2_1.sublist2_sentence.sentences[0].text == "Sublist2Sentence 1"
        assert len(sublist2_1.sublists3) == 1

        # Sublist1[0].Sublist2[0].Sublist3
        sublist3_1: Sublist3 = sublist2_1.sublists3[0]
        assert len(sublist3_1.sublist3_sentence.sentences) == 1
        assert sublist3_1.sublist3_sentence.sentences[0].text == "Sublist3Sentence 1"

        # Sublist1[1]
        sublist1_2: Sublist1 = list_.sublists1[1]
        assert len(sublist1_2.sublist1_sentence.columns) == 1
        assert len(sublist1_2.sublist1_sentence.columns[0].sentences) == 1
        assert len(sublist1_2.sublists2) == 2

        # Sublist1[1].Sublist2[0]
        sublist2_2: Sublist2 = sublist1_2.sublists2[0]
        assert len(sublist2_2.sublists3) == 1

        # Sublist1[1].Sublist2[0].Sublist3[0]
        sublist3_2: Sublist3 = sublist2_2.sublists3[0]
        assert len(sublist3_2.sublist3_sentence.sentences) == 1
        assert sublist3_2.sublist3_sentence.sentences[0].text == "Sublist3Sentence 2"
