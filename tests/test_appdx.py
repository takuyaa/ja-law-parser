from ja_law_parser.model import AppdxNote, AppdxNoteTitle, Note, NoteStruct, Sentence


class TestAppdx:
    def test_appdx_note(self) -> None:
        xml = """\
        <AppdxNote Num="1">
          <AppdxNoteTitle />
          <NoteStruct>
            <Note>
              <Sentence>Sentence 1</Sentence>
            </Note>
          </NoteStruct>
        </AppdxNote>
        """
        appdx_note: AppdxNote = AppdxNote.from_xml(xml)
        assert appdx_note.num == "1"
        assert type(appdx_note.appdx_note_title) == AppdxNoteTitle
        appdx_note_title: AppdxNoteTitle = appdx_note.appdx_note_title
        assert appdx_note_title.text == ""

        assert len(appdx_note.note_structs) == 1

        assert type(appdx_note.note_structs[0]) == NoteStruct
        note_struct: NoteStruct = appdx_note.note_structs[0]
        sentences: list[Sentence] = note_struct.note.sentences
        assert len(sentences) == 1

        note: Note = appdx_note.note_structs[0].note
        assert note.sentences[0].text == "Sentence 1"
