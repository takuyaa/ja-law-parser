from ja_law_parser.model import TOC


class TestTOC:
    def test_toc(self):
        xml = """\
        <TOC>
          <TOCLabel>目次</TOCLabel>
          <TOCPreambleLabel>前文</TOCPreambleLabel>
          <TOCChapter Num="1">
            <ChapterTitle>Chapter 1</ChapterTitle>
            <ArticleRange>（第一条・第二条）</ArticleRange>
          </TOCChapter>
          <TOCChapter Num="2">
            <ChapterTitle>Chapter 2</ChapterTitle>
            <ArticleRange>（第三条―第五条）</ArticleRange>
          </TOCChapter>
          <TOCSupplProvision>
            <SupplProvisionLabel>附則</SupplProvisionLabel>
          </TOCSupplProvision>
        </TOC>
        """
        toc: TOC = TOC.from_xml(xml)
        assert toc is not None
        assert toc.toc_label == "目次"
        assert toc.toc_preamble_label == "前文"
        assert len(toc.toc_chapters) == 2
        assert toc.toc_chapters[0].num == "1"
        assert toc.toc_chapters[0].chapter_title.text == "Chapter 1"
        assert toc.toc_chapters[0].article_range.text == "（第一条・第二条）"
        assert toc.toc_chapters[1].num == "2"
        assert toc.toc_chapters[1].chapter_title.text == "Chapter 2"
        assert toc.toc_chapters[1].article_range.text == "（第三条―第五条）"
        assert toc.toc_suppl_provision.suppl_provision_label.text == "附則"
