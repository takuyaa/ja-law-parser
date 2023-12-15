import inspect
import sys
from functools import cached_property
from typing import Generator, Literal, Optional, Union

from lxml import etree
from pydantic import Field, NonNegativeInt, PositiveInt, computed_field
from pydantic_xml import BaseXmlModel, attr, computed_attr, computed_element, element


class Ruby(BaseXmlModel, tag="Ruby"):
    """
    ルビ構造

    Attributes:
        rt: ルビ
        text: テキスト
    """

    rt: Optional[list[str]] = element(tag="Rt")
    text: str


class Sup(BaseXmlModel, tag="Sup"):
    """
    上付き文字

    Attributes:
        text: テキスト
    """

    text: str


class Sub(BaseXmlModel, tag="Sub"):
    """
    下付き文字

    Attributes:
        text: テキスト
    """

    text: str


class Text(BaseXmlModel, tag="Text"):
    """
    テキスト

    Attributes:
        text: テキスト
    """

    text: str


class Fig(BaseXmlModel, tag="Fig"):
    """
    図

    Attributes:
        src: URI
    """

    src: str = attr(name="src")


class ArithFormula(BaseXmlModel, tag="ArithFormula"):
    """
    算式

    Attributes:
        num: 番号

        figs: 図
    """

    num: Optional[NonNegativeInt] = attr(name="Num", default=None)

    figs: Optional[list[Fig]] = None

    @computed_field  # type: ignore[misc]
    @cached_property
    def text(self) -> str:
        # At this moment, the contents don't have any text.
        return ""


QuoteStructT = Union["Sentence", Fig, "TableStruct", Text]


class QuoteStruct(BaseXmlModel, arbitrary_types_allowed=True):
    """
    構造引用

    Attributes:
        contents: テキスト、段、図
    """

    @computed_field  # type: ignore[misc]
    @cached_property
    def contents(self) -> list[QuoteStructT]:
        element = self.raw_element
        contents: list[QuoteStructT] = []

        # Head text
        if element.text is not None:
            contents.append(Text(text=element.text))

        elm: etree._Element
        for elm in element.iterchildren():
            if elm.tag == "Sentence":
                contents.append(Sentence(raw_element=elm))
            elif elm.tag == "List":
                contents.append(List.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Fig":
                contents.append(Fig.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "FigStruct":
                contents.append(FigStruct.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Table":
                contents.append(Table.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "TableStruct":
                contents.append(TableStruct.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "ArithFormula":
                contents.append(ArithFormula.from_xml_tree(root=elm))  # type: ignore[arg-type]
            else:
                raise NotImplementedError(f"{elm.tag} is not implemented yet")

            # Tail text
            if elm.tail is not None:
                contents.append(Text(text=elm.tail))

        return contents

    @computed_field  # type: ignore[misc]
    @cached_property
    def text(self) -> str:
        text = ""
        for content in self.contents:
            if hasattr(content, "text"):
                text += content.text
        return text

    raw_element: etree._Element = Field(exclude=True)


LineContentT = Union[Text, QuoteStruct, ArithFormula, Ruby, Sup, Sub]


class Line(BaseXmlModel, tag="Line", arbitrary_types_allowed=True):
    """
    傍線

    Attributes:
        style: 線種（"solid"：実線、"dotted"：点線、"double"：二重線、"none"：無）

        contents: テキスト、構造引用、算式、ルビ構造、上付き文字、下付き文字
        text: テキスト
    """

    @computed_attr(name="Style")  # type: ignore[arg-type]
    def style(self) -> Optional[Literal["solid", "dotted", "double", "none"]]:
        style: Optional[str] = get_attr(element=self.raw_element, tag="Style")
        if style is None:
            return None
        elif style == "solid":
            return "solid"
        elif style == "dotted":
            return "dotted"
        elif style == "double":
            return "double"
        elif style == "none":
            return "none"
        else:
            raise NotImplementedError

    @computed_field  # type: ignore[misc]
    @cached_property
    def contents(self) -> list[LineContentT]:
        element = self.raw_element
        contents: list[LineContentT] = []

        # Head text
        if element.text is not None:
            contents.append(Text(text=element.text))

        elm: etree._Element
        for elm in element.iterchildren():
            if elm.tag == "QuoteStruct":
                contents.append(QuoteStruct(raw_element=elm))
            elif elm.tag == "ArithFormula":
                contents.append(ArithFormula.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Ruby":
                contents.append(Ruby.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Sup":
                contents.append(Sup.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Sub":
                contents.append(Sub.from_xml_tree(root=elm))  # type: ignore[arg-type]
            else:
                raise NotImplementedError

            # Tail text
            if elm.tail is not None:
                contents.append(Text(text=elm.tail))

        return contents

    @computed_field  # type: ignore[misc]
    @cached_property
    def text(self) -> str:
        text = ""
        for content in self.contents:
            # element of contents should have the `text` attribute.
            text += content.text
        return text

    raw_element: etree._Element = Field(exclude=True)


class TaggedText(BaseXmlModel, arbitrary_types_allowed=True):
    """
    タグ付きテキスト

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """

    @computed_field  # type: ignore[misc]
    @cached_property
    def tagged_text(self) -> list[Union[Text, Line, Ruby, Sup, Sub]]:
        element = self.raw_element
        tags: list[Union[Text, Line, Ruby, Sup, Sub]] = []

        # Head text
        if element.text is not None:
            tags.append(Text(text=element.text))

        elm: etree._Element
        for elm in element.iterchildren():
            if elm.tag == "Line":
                tags.append(Line(raw_element=elm))
            elif elm.tag == "Ruby":
                tags.append(Ruby.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Sup":
                tags.append(Sup.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Sub":
                tags.append(Sub.from_xml_tree(root=elm))  # type: ignore[arg-type]
            else:
                raise NotImplementedError

            # Tail text
            if elm.tail is not None:
                tags.append(Text(text=elm.tail))

        return tags

    @computed_field  # type: ignore[misc]
    @cached_property
    def text(self) -> str:
        element = self.raw_element
        text = ""

        # Head text
        if element.text is not None:
            text += element.text

        elm: etree._Element
        for elm in element.iterchildren():
            if elm.tag == "Ruby":
                text += Ruby.from_xml_tree(root=elm).text  # type: ignore[arg-type]
            elif elm.tag == "Line":
                text += Line(raw_element=elm).text  # type: ignore[arg-type]
            elif elm.tag == "Sup":
                text += Sup.from_xml_tree(root=elm).text  # type: ignore[arg-type]
            elif elm.tag == "Sub":
                text += Sub.from_xml_tree(root=elm).text  # type: ignore[arg-type]
            else:
                raise NotImplementedError(f"tag: {elm.tag} is not supported yet")

            # Tail text
            if elm.tail is not None:
                text += elm.tail

        return text

    raw_element: etree._Element = Field(exclude=True)


class WithWritingMode(TaggedText):
    """
    A mixin class to add the below attribute.

    Attributes:
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """

    @computed_attr(name="WritingMode")  # type: ignore[arg-type]
    def writing_mode(self) -> Optional[Literal["vertical", "horizontal"]]:
        writing_mode: Optional[str] = get_attr(element=self.raw_element, tag="WritingMode")
        if writing_mode is None:
            return None
        elif writing_mode == "vertical":
            return "vertical"
        elif writing_mode == "horizontal":
            return "horizontal"
        else:
            raise NotImplementedError


class Sentence(WithWritingMode, tag="Sentence"):
    """
    段

    Attributes:
        num: 番号
        function: 機能（"main"：本文、"proviso"：ただし書）
        indent: インデント（"Paragraph"：項、"Item"：号、"Subitem1"：号細分、"Subitem2"：号細分２、
        "Subitem3"：号細分３、"Subitem4"：号細分４、"Subitem5"：号細分５、"Subitem6"：号細分６、
        "Subitem7"：号細分７、"Subitem8"：号細分８、"Subitem9"：号細分９、"Subitem10"：号細分１０）
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """

    @computed_attr(name="Num")  # type: ignore[arg-type]
    def num(self) -> Optional[NonNegativeInt]:
        num: Optional[str] = get_attr(element=self.raw_element, tag="Num")
        if num is None:
            return None
        else:
            return int(num)

    @computed_attr(name="Function")  # type: ignore[arg-type]
    def function(self) -> Optional[Literal["main", "proviso"]]:
        func: Optional[str] = get_attr(element=self.raw_element, tag="Function")
        if func is None:
            return None
        elif func == "main":
            return "main"
        elif func == "proviso":
            return "proviso"
        else:
            raise NotImplementedError

    @computed_attr(name="Indent")  # type: ignore[arg-type]
    def indent(  # noqa: C901
        self
    ) -> Optional[
        Literal[
            "Paragraph",
            "Item",
            "Subitem1",
            "Subitem2",
            "Subitem3",
            "Subitem4",
            "Subitem5",
            "Subitem6",
            "Subitem7",
            "Subitem8",
            "Subitem9",
            "Subitem10",
        ]
    ]:
        indent: Optional[str] = get_attr(element=self.raw_element, tag="Indent")
        if indent is None:
            return None
        elif indent == "Paragraph":
            return "Paragraph"
        elif indent == "Item":
            return "Item"
        elif indent == "Subitem1":
            return "Subitem1"
        elif indent == "Subitem2":
            return "Subitem2"
        elif indent == "Subitem3":
            return "Subitem3"
        elif indent == "Subitem4":
            return "Subitem4"
        elif indent == "Subitem5":
            return "Subitem5"
        elif indent == "Subitem6":
            return "Subitem6"
        elif indent == "Subitem7":
            return "Subitem7"
        elif indent == "Subitem8":
            return "Subitem8"
        elif indent == "Subitem9":
            return "Subitem9"
        elif indent == "Subitem10":
            return "Subitem10"
        else:
            raise NotImplementedError

    @computed_field  # type: ignore[misc]
    @cached_property
    def contents(self) -> list[Union[Text, Line, QuoteStruct, ArithFormula, Ruby, Sup, Sub]]:
        element = self.raw_element
        contents: list[Union[Text, Line, QuoteStruct, ArithFormula, Ruby, Sup, Sub]] = []

        # Head text
        if element.text is not None:
            contents.append(Text(text=element.text))

        elm: etree._Element
        for elm in element.iterchildren():
            if elm.tag == "Line":
                contents.append(Line(raw_element=elm))
            elif elm.tag == "QuoteStruct":
                contents.append(QuoteStruct(raw_element=elm))
            elif elm.tag == "ArithFormula":
                contents.append(ArithFormula.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Ruby":
                contents.append(Ruby.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Sup":
                contents.append(Sup.from_xml_tree(root=elm))  # type: ignore[arg-type]
            elif elm.tag == "Sub":
                contents.append(Sub.from_xml_tree(root=elm))  # type: ignore[arg-type]
            else:
                raise NotImplementedError

            # Tail text
            if elm.tail is not None:
                contents.append(Text(text=elm.tail))

        return contents

    @computed_field  # type: ignore[misc]
    @cached_property
    def text(self) -> str:
        text = ""
        for content in self.contents:
            # element of contents should have the `text` attribute.
            text += content.text
        return text

    raw_element: etree._Element = Field(exclude=True)


class WithSentences(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        sentences: 段
    """

    @computed_field  # type: ignore[misc]
    @cached_property
    def sentences(self) -> Optional[list[Sentence]]:
        if self.sentence_raw is None:
            return None
        sentences: list[Sentence] = []
        for elm in self.sentence_raw:
            sentences.append(Sentence(raw_element=elm))
        return sentences

    sentence_raw: Optional[list[etree._Element]] = element(tag="Sentence", default=None, exclude=True)


class Note(WithSentences, tag="Note"):
    """
    記

    Attributes:
        sentences: 段
        figs: 図
        items: 号
        arith_formulas: 算式
        lists: 列記
    """

    figs: Optional[list[Fig]] = None
    items: Optional[list["Item"]] = None
    arith_formulas: Optional[list[ArithFormula]] = None
    lists: Optional[list["List"]] = None


class Style(BaseXmlModel, tag="Style"):
    """
    様式

    Attributes:
        figs: 図
    """

    figs: Optional[list[Fig]] = None


class Format(BaseXmlModel, tag="Format"):
    """
    書式

    Attributes:
        figs: 図
    """

    figs: Optional[list[Fig]] = None


class ParagraphCaption(TaggedText, tag="ParagraphCaption"):
    """
    項見出し

    Attributes:
        common_caption: 共通見出し

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """

    common_caption: Optional[bool] = attr(name="CommonCaption", default=None)


class WithParagraphCaption(
    BaseXmlModel,
    arbitrary_types_allowed=True,
):
    """
    A mixin class to add the below attribute.

    Attributes:
        paragraph_caption: 項見出し
    """

    @computed_element(tag="ParagraphCaption")  # type: ignore[arg-type]
    def paragraph_caption(self) -> Optional[ParagraphCaption]:
        if self.paragraph_caption_raw is None:
            return None
        return ParagraphCaption(raw_element=self.paragraph_caption_raw)

    paragraph_caption_raw: Optional[etree._Element] = element(tag="ParagraphCaption", default=None, exclude=True)


class ParagraphNum(TaggedText, tag="ParagraphNum"):
    """
    項番号

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithParagraphNum(
    BaseXmlModel,
    arbitrary_types_allowed=True,
):
    """
    A mixin class to add the below attribute.

    Attributes:
        paragraph_num: 項番号
    """

    @computed_element(tag="ParagraphNum")  # type: ignore[arg-type]
    def paragraph_num(self) -> ParagraphNum:
        return ParagraphNum(raw_element=self.paragraph_num_raw)

    paragraph_num_raw: etree._Element = element(tag="ParagraphNum", default=None, exclude=True)


class ItemTitle(TaggedText, tag="ItemTitle"):
    """
    号名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithItemTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        item_title: 号名
    """

    @computed_element(tag="ItemTitle")  # type: ignore[arg-type]
    def item_title(self) -> Optional[ItemTitle]:
        if self.item_title_raw is None:
            return None
        return ItemTitle(raw_element=self.item_title_raw)

    item_title_raw: Optional[etree._Element] = element(tag="ItemTitle", default=None, exclude=True)


class ClassTitle(TaggedText, tag="ClassTitle"):
    """
    類名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithClassTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        class_title: 類名
    """

    @computed_element(tag="ClassTitle")  # type: ignore[arg-type]
    def class_title(self) -> Optional[ClassTitle]:
        if self.class_title_raw is None:
            return None
        return ClassTitle(raw_element=self.class_title_raw)

    class_title_raw: Optional[etree._Element] = element(tag="ClassTitle", default=None, exclude=True)


class ArticleTitle(TaggedText, tag="ArticleTitle"):
    """
    条名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithArticleTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        article_title: 条名
    """

    @computed_element(tag="ArticleTitle")  # type: ignore[arg-type]
    def article_title(self) -> ArticleTitle:
        return ArticleTitle(raw_element=self.article_title_raw)

    article_title_raw: etree._Element = element(tag="ArticleTitle", default=None, exclude=True)


class ArticleCaption(TaggedText, tag="ArticleCaption"):
    """
    条見出し

    Attributes:
        common_caption: 共通見出し

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """

    common_caption: Optional[bool] = attr(name="CommonCaption", default=None)


class WithArticleCaption(
    BaseXmlModel,
    arbitrary_types_allowed=True,
):
    """
    A mixin class to add the below attribute.

    Attributes:
        article_caption: 条見出し
    """

    @computed_element(tag="ArticleCaption")  # type: ignore[arg-type]
    def article_caption(self) -> Optional[ArticleCaption]:
        if self.article_caption_raw is None:
            return None
        return ArticleCaption(raw_element=self.article_caption_raw)

    article_caption_raw: Optional[etree._Element] = element(tag="ArticleCaption", default=None, exclude=True)


class DivisionTitle(TaggedText, tag="DivisionTitle"):
    """
    目名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithDivisionTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        division_title: 目名
    """

    @computed_element(tag="DivisionTitle")  # type: ignore[arg-type]
    def division_title(self) -> Optional[DivisionTitle]:
        if self.division_title_raw is None:
            return None
        return DivisionTitle(raw_element=self.division_title_raw)

    division_title_raw: etree._Element = element(tag="DivisionTitle", default=None, exclude=True)


class SectionTitle(TaggedText, tag="SectionTitle"):
    """
    節名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSectionTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        section_title: 節名
    """

    @computed_element(tag="SectionTitle")  # type: ignore[arg-type]
    def section_title(self) -> Optional[SectionTitle]:
        if self.section_title_raw is None:
            return None
        return SectionTitle(raw_element=self.section_title_raw)

    section_title_raw: etree._Element = element(tag="SectionTitle", default=None, exclude=True)


class SubsectionTitle(TaggedText, tag="SubsectionTitle"):
    """
    款名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubsectionTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subsection_title: 款名
    """

    @computed_element(tag="SubsectionTitle")  # type: ignore[arg-type]
    def subsection_title(self) -> Optional[SubsectionTitle]:
        if self.subsection_title_raw is None:
            return None
        return SubsectionTitle(raw_element=self.subsection_title_raw)

    subsection_title_raw: etree._Element = element(tag="SubsectionTitle", default=None, exclude=True)


class ChapterTitle(TaggedText, tag="ChapterTitle"):
    """
    章名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithChapterTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        chapter_title: 章名
    """

    @computed_element(tag="ChapterTitle")  # type: ignore[arg-type]
    def chapter_title(self) -> Optional[ChapterTitle]:
        if self.chapter_title_raw is None:
            return None
        return ChapterTitle(raw_element=self.chapter_title_raw)

    chapter_title_raw: etree._Element = element(tag="ChapterTitle", default=None, exclude=True)


class PartTitle(TaggedText, tag="PartTitle"):
    """
    編名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithPartTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        part_title: 編名
    """

    @computed_element(tag="PartTitle")  # type: ignore[arg-type]
    def part_title(self) -> Optional[PartTitle]:
        if self.part_title_raw is None:
            return None
        return PartTitle(raw_element=self.part_title_raw)

    part_title_raw: etree._Element = element(tag="PartTitle", default=None, exclude=True)


class RemarksLabel(TaggedText, tag="RemarksLabel"):
    """
    備考ラベル

    Attributes:
        line_break: 改行

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """

    line_break: Optional[bool] = attr(Name="LineBreak", default=None)


class WithRemarksLabel(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        remarks_label: 備考ラベル
    """

    @computed_element(tag="RemarksLabel")  # type: ignore[arg-type]
    def remarks_label(self) -> Optional[RemarksLabel]:
        if self.remarks_label_raw is None:
            return None
        return RemarksLabel(raw_element=self.remarks_label_raw)

    remarks_label_raw: etree._Element = element(tag="RemarksLabel", default=None, exclude=True)


class LawTitle(TaggedText, tag="LawTitle"):
    """
    題名

    Attributes:
        kana: 読み
        abbrev: 略称
        abbrev_kana: 略称読み

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """

    @computed_attr(name="Kana")  # type: ignore[arg-type]
    def kana(self) -> Optional[str]:
        return self.raw_element.get(key="Kana")

    @computed_attr(name="Abbrev")  # type: ignore[arg-type]
    def abbrev(self) -> Optional[str]:
        return self.raw_element.get(key="Abbrev")

    @computed_attr(name="AbbrevKana")  # type: ignore[arg-type]
    def abbrev_kana(self) -> Optional[str]:
        return self.raw_element.get(key="AbbrevKana")


class WithLawTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        law_title: 題名
    """

    @computed_element(tag="LawTitle")  # type: ignore[arg-type]
    def law_title(self) -> Optional[LawTitle]:
        if self.law_title_raw is None:
            return None
        return LawTitle(raw_element=self.law_title_raw)

    law_title_raw: Optional[etree._Element] = element(tag="LawTitle", default=None, exclude=True)


class EnactStatement(TaggedText, tag="EnactStatement"):
    """
    制定文

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithEnactStatement(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        enact_statement: 制定文
    """

    @computed_element(tag="EnactStatement")  # type: ignore[arg-type]
    def enact_statement(self) -> Optional[EnactStatement]:
        if self.enact_statement_raw is None:
            return None
        return EnactStatement(raw_element=self.enact_statement_raw)

    enact_statement_raw: Optional[etree._Element] = element(tag="EnactStatement", default=None, exclude=True)


class SupplNote(TaggedText, tag="SupplNote"):
    """
    付記

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSupplNote(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        suppl_note: 付記
    """

    @computed_element(tag="SupplNote")  # type: ignore[arg-type]
    def suppl_note(self) -> Optional[SupplNote]:
        if self.suppl_note_raw is None:
            return None
        return SupplNote(raw_element=self.suppl_note_raw)

    suppl_note_raw: Optional[etree._Element] = element(tag="SupplNote", default=None, exclude=True)


class WithSupplNotes(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        suppl_notes: 付記
    """

    @computed_element(tag="SupplNote")  # type: ignore[arg-type]
    def suppl_notes(self) -> Optional[list[SupplNote]]:
        if self.suppl_notes_raw is None:
            return None
        notes: list[SupplNote] = []
        for elm in self.suppl_notes_raw:
            notes.append(SupplNote(raw_element=elm))
        return notes

    suppl_notes_raw: Optional[etree._Element] = element(tag="SupplNote", default=None, exclude=True)


class ArticleRange(TaggedText, tag="ArticleRange"):
    """
    目名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithArticleRange(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        article_range: 条範囲
    """

    @computed_element(tag="ArticleRange")  # type: ignore[arg-type]
    def article_range(self) -> Optional[ArticleRange]:
        if self.article_range is None:
            return None
        return ArticleRange(raw_element=self.article_range)

    article_range_raw: Optional[etree._Element] = element(tag="ArticleRange", default=None, exclude=True)


class TableHeaderColumn(TaggedText, tag="TableHeaderColumn"):
    """
    表欄名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithTableHeaderColumns(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        table_header_column: 表欄名
    """

    @computed_element(tag="TableHeaderColumn")  # type: ignore[arg-type]
    def table_header_columns(self) -> Optional[list[TableHeaderColumn]]:
        if self.table_header_column_raw is None:
            return None
        columns: list[TableHeaderColumn] = []
        for elm in self.table_header_column_raw:
            columns.append(TableHeaderColumn(raw_element=elm))
        return columns

    table_header_column_raw: Optional[etree._Element] = element(tag="TableHeaderColumn", default=None, exclude=True)


class TableStructTitle(WithWritingMode, tag="TableStructTitle"):
    """
    表項目名

    Attributes:
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithTableStructTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        table_struct_title: 表項目名
    """

    @computed_element(tag="TableStructTitle")  # type: ignore[arg-type]
    def table_struct_title(self) -> Optional[TableStructTitle]:
        if self.table_struct_title_raw is None:
            return None
        return TableStructTitle(raw_element=self.table_struct_title_raw)

    table_struct_title_raw: Optional[etree._Element] = element(tag="TableStructTitle", default=None, exclude=True)


class FigStructTitle(TaggedText, tag="FigStructTitle"):
    """
    図項目名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithFigStructTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        fig_struct_title: 図項目名
    """

    @computed_element(tag="FigStructTitle")  # type: ignore[arg-type]
    def fig_struct_title(self) -> Optional[FigStructTitle]:
        if self.fig_struct_title_raw is None:
            return None
        return FigStructTitle(raw_element=self.fig_struct_title_raw)

    fig_struct_title_raw: Optional[etree._Element] = element(tag="FigStructTitle", default=None, exclude=True)


class NoteStructTitle(TaggedText, tag="NoteStructTitle"):
    """
    記項名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithNoteStructTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        note_struct_title: 記項名
    """

    @computed_element(tag="NoteStructTitle")  # type: ignore[arg-type]
    def note_struct_title(self) -> Optional[NoteStructTitle]:
        if self.note_struct_title_raw is None:
            return None
        return NoteStructTitle(raw_element=self.note_struct_title_raw)

    note_struct_title_raw: Optional[etree._Element] = element(tag="NoteStructTitle", default=None, exclude=True)


class StyleStructTitle(TaggedText, tag="StyleStructTitle"):
    """
    様式項目名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithStyleStructTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        style_struct_title: 様式項目名
    """

    @computed_element(tag="StyleStructTitle")  # type: ignore[arg-type]
    def style_struct_title(self) -> Optional[StyleStructTitle]:
        if self.style_struct_title_raw is None:
            return None
        return StyleStructTitle(raw_element=self.style_struct_title_raw)

    style_struct_title_raw: Optional[etree._Element] = element(tag="StyleStructTitle", default=None, exclude=True)


class FormatStructTitle(TaggedText, tag="FormatStructTitle"):
    """
    書式項目名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithFormatStructTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        format_struct_title: 書式項目名
    """

    @computed_element(tag="FormatStructTitle")  # type: ignore[arg-type]
    def format_struct_title(self) -> Optional[FormatStructTitle]:
        if self.format_struct_title_raw is None:
            return None
        return FormatStructTitle(raw_element=self.format_struct_title_raw)

    format_struct_title_raw: Optional[etree._Element] = element(tag="FormatStructTitle", default=None, exclude=True)


class SupplProvisionLabel(TaggedText, tag="SupplProvisionLabel"):
    """
    附則ラベル

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSupplProvisionLabel(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        suppl_provision_label: 附則ラベル
    """

    @computed_element(tag="SupplProvisionLabel")  # type: ignore[arg-type]
    def suppl_provision_label(self) -> Optional[SupplProvisionLabel]:
        if self.suppl_provision_label_raw is None:
            return None
        return SupplProvisionLabel(raw_element=self.suppl_provision_label_raw)

    suppl_provision_label_raw: Optional[etree._Element] = element(
        tag="SupplProvisionLabel", default=None, exclude=True
    )


class SupplProvisionAppdxTableTitle(TaggedText, tag="SupplProvisionAppdxTableTitle"):
    """
    附則別表名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSupplProvisionAppdxTableTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        suppl_provision_appdx_table_title: 附則別表名
    """

    @computed_element(tag="SupplProvisionAppdxTableTitle")  # type: ignore[arg-type]
    def suppl_provision_appdx_table_title(self) -> Optional[SupplProvisionAppdxTableTitle]:
        if self.suppl_provision_appdx_table_title_raw is None:
            return None
        return SupplProvisionAppdxTableTitle(raw_element=self.suppl_provision_appdx_table_title_raw)

    suppl_provision_appdx_table_title_raw: Optional[etree._Element] = element(
        tag="SupplProvisionAppdxTableTitle", default=None, exclude=True
    )


class SupplProvisionAppdxStyleTitle(WithWritingMode, tag="SupplProvisionAppdxStyleTitle"):
    """
    附則様式名

    Attributes:
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSupplProvisionAppdxStyleTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        suppl_provision_appdx_style_title: 附則様式名
    """

    @computed_element(tag="SupplProvisionAppdxStyleTitle")  # type: ignore[arg-type]
    def suppl_provision_appdx_style_title(self) -> Optional[SupplProvisionAppdxStyleTitle]:
        if self.suppl_provision_appdx_style_title_raw is None:
            return None
        return SupplProvisionAppdxStyleTitle(raw_element=self.suppl_provision_appdx_style_title_raw)

    suppl_provision_appdx_style_title_raw: Optional[etree._Element] = element(
        tag="SupplProvisionAppdxStyleTitle", default=None, exclude=True
    )


class AppdxTableTitle(WithWritingMode, tag="AppdxTableTitle"):
    """
    別表名

    Attributes:
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithAppdxTableTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        appdx_table_title: 別表名
    """

    @computed_element(tag="AppdxTableTitle")  # type: ignore[arg-type]
    def appdx_table_title(self) -> Optional[AppdxTableTitle]:
        if self.appdx_table_title_raw is None:
            return None
        return AppdxTableTitle(raw_element=self.appdx_table_title_raw)

    appdx_table_title_raw: Optional[etree._Element] = element(tag="AppdxTableTitle", default=None, exclude=True)


class AppdxNoteTitle(WithWritingMode, tag="AppdxTableTitle"):
    """
    別記名

    Attributes:
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithAppdxNoteTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        appdx_note_title: 別表名
    """

    @computed_element(tag="AppdxNoteTitle")  # type: ignore[arg-type]
    def appdx_note_title(self) -> Optional[AppdxNoteTitle]:
        if self.appdx_note_title_raw is None:
            return None
        return AppdxNoteTitle(raw_element=self.appdx_note_title_raw)

    appdx_note_title_raw: Optional[etree._Element] = element(tag="AppdxNoteTitle", default=None, exclude=True)


class AppdxStyleTitle(WithWritingMode, tag="AppdxStyleTitle"):
    """
    別記様式名

    Attributes:
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithAppdxStyleTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        appdx_style_title: 別記様式名
    """

    @computed_element(tag="AppdxStyleTitle")  # type: ignore[arg-type]
    def appdx_style_title(self) -> Optional[AppdxStyleTitle]:
        if self.appdx_style_title_raw is None:
            return None
        return AppdxStyleTitle(raw_element=self.appdx_style_title_raw)

    appdx_style_title_raw: Optional[etree._Element] = element(tag="AppdxStyleTitle", default=None, exclude=True)


class AppdxFigTitle(WithWritingMode, tag="AppdxFigTitle"):
    """
    別図名

    Attributes:
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithAppdxFigTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        appdx_fig_title: 別記様式名
    """

    @computed_element(tag="AppdxFigTitle")  # type: ignore[arg-type]
    def appdx_fig_title(self) -> Optional[AppdxFigTitle]:
        if self.appdx_fig_title_raw is None:
            return None
        return AppdxFigTitle(raw_element=self.appdx_fig_title_raw)

    appdx_fig_title_raw: Optional[etree._Element] = element(tag="AppdxFigTitle", default=None, exclude=True)


class AppdxFormatTitle(WithWritingMode, tag="AppdxFormatTitle"):
    """
    別記書式名

    Attributes:
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithAppdxFormatTitle(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        appdx_format_title: 別記書式名
    """

    @computed_element(tag="AppdxFormatTitle")  # type: ignore[arg-type]
    def appdx_format_title(self) -> Optional[AppdxFormatTitle]:
        if self.appdx_format_title_raw is None:
            return None
        return AppdxFormatTitle(raw_element=self.appdx_format_title_raw)

    appdx_format_title_raw: Optional[etree._Element] = element(tag="AppdxFormatTitle", default=None, exclude=True)


class RelatedArticleNum(TaggedText, tag="RelatedArticleNum"):
    """
    関係条文番号

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithRelatedArticleNum(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        related_article_num: 関係条文番号
    """

    @computed_element(tag="RelatedArticleNum")  # type: ignore[arg-type]
    def related_article_num(self) -> Optional[RelatedArticleNum]:
        if self.related_article_num_raw is None:
            return None
        return RelatedArticleNum(raw_element=self.related_article_num_raw)

    related_article_num_raw: Optional[etree._Element] = element(tag="RelatedArticleNum", default=None, exclude=True)


class ArithFormulaNum(TaggedText, tag="ArithFormulaNum"):
    """
    算式番号

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithArithFormulaNum(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        arith_formula_num: 算式番号
    """

    @computed_element(tag="RelatedArticleNum")  # type: ignore[arg-type]
    def arith_formula_num(self) -> Optional[ArithFormulaNum]:
        if self.arith_formula_num_raw is None:
            return None
        return ArithFormulaNum(raw_element=self.arith_formula_num_raw)

    arith_formula_num_raw: Optional[etree._Element] = element(tag="ArithFormulaNum", default=None, exclude=True)


class TOCAppdxTableLabel(TaggedText, tag="TOCAppdxTableLabel"):
    """
    目次別表ラベル

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithTOCAppdxTableLabels(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        toc_appdx_table_labels: 目次別表ラベル
    """

    @computed_element(tag="TOCAppdxTableLabel")  # type: ignore[arg-type]
    def toc_appdx_table_label(self) -> Optional[list[TOCAppdxTableLabel]]:
        if self.toc_appdx_table_labels_raw is None:
            return None
        labels: list[TOCAppdxTableLabel] = []
        for elm in self.toc_appdx_table_labels_raw:
            labels.append(TOCAppdxTableLabel(raw_element=elm))
        return labels

    toc_appdx_table_labels_raw: Optional[etree._Element] = element(
        tag="TOCAppdxTableLabel", default=None, exclude=True
    )


class Subitem1Title(TaggedText, tag="Subitem1Title"):
    """
    号細分名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem1Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem1_title: 号細分名
    """

    @computed_element(tag="Subitem1Title")  # type: ignore[arg-type]
    def subitem1_title(self) -> Optional[Subitem1Title]:
        if self.subitem1_title_raw is None:
            return None
        return Subitem1Title(raw_element=self.subitem1_title_raw)

    subitem1_title_raw: Optional[etree._Element] = element(tag="Subitem1Title", default=None, exclude=True)


class Subitem2Title(TaggedText, tag="Subitem2Title"):
    """
    号細分２名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem2Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem2_title: 号細分２名
    """

    @computed_element(tag="Subitem2Title")  # type: ignore[arg-type]
    def subitem2_title(self) -> Optional[Subitem2Title]:
        if self.subitem2_title_raw is None:
            return None
        return Subitem2Title(raw_element=self.subitem2_title_raw)

    subitem2_title_raw: Optional[etree._Element] = element(tag="Subitem2Title", default=None, exclude=True)


class Subitem3Title(TaggedText, tag="Subitem3Title"):
    """
    号細分３名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem3Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem3_title: 号細分３名
    """

    @computed_element(tag="Subitem3Title")  # type: ignore[arg-type]
    def subitem3_title(self) -> Optional[Subitem3Title]:
        if self.subitem3_title_raw is None:
            return None
        return Subitem3Title(raw_element=self.subitem3_title_raw)

    subitem3_title_raw: Optional[etree._Element] = element(tag="Subitem3Title", default=None, exclude=True)


class Subitem4Title(TaggedText, tag="Subitem4Title"):
    """
    号細分４名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem4Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem4_title: 号細分４名
    """

    @computed_element(tag="Subitem4Title")  # type: ignore[arg-type]
    def subitem4_title(self) -> Optional[Subitem4Title]:
        if self.subitem4_title_raw is None:
            return None
        return Subitem4Title(raw_element=self.subitem4_title_raw)

    subitem4_title_raw: Optional[etree._Element] = element(tag="Subitem4Title", default=None, exclude=True)


class Subitem5Title(TaggedText, tag="Subitem5Title"):
    """
    号細分５名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem5Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem5_title: 号細分５名
    """

    @computed_element(tag="Subitem5Title")  # type: ignore[arg-type]
    def subitem5_title(self) -> Optional[Subitem5Title]:
        if self.subitem5_title_raw is None:
            return None
        return Subitem5Title(raw_element=self.subitem5_title_raw)

    subitem5_title_raw: Optional[etree._Element] = element(tag="Subitem5Title", default=None, exclude=True)


class Subitem6Title(TaggedText, tag="Subitem6Title"):
    """
    号細分６名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem6Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem6_title: 号細分６名
    """

    @computed_element(tag="Subitem6Title")  # type: ignore[arg-type]
    def subitem6_title(self) -> Optional[Subitem6Title]:
        if self.subitem6_title_raw is None:
            return None
        return Subitem6Title(raw_element=self.subitem6_title_raw)

    subitem6_title_raw: Optional[etree._Element] = element(tag="Subitem6Title", default=None, exclude=True)


class Subitem7Title(TaggedText, tag="Subitem7Title"):
    """
    号細分７名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem7Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem7_title: 号細分７名
    """

    @computed_element(tag="Subitem7Title")  # type: ignore[arg-type]
    def subitem7_title(self) -> Optional[Subitem7Title]:
        if self.subitem7_title_raw is None:
            return None
        return Subitem7Title(raw_element=self.subitem7_title_raw)

    subitem7_title_raw: Optional[etree._Element] = element(tag="Subitem7Title", default=None, exclude=True)


class Subitem8Title(TaggedText, tag="Subitem8Title"):
    """
    号細分８名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem8Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem8_title: 号細分８名
    """

    @computed_element(tag="Subitem8Title")  # type: ignore[arg-type]
    def subitem8_title(self) -> Optional[Subitem8Title]:
        if self.subitem8_title_raw is None:
            return None
        return Subitem8Title(raw_element=self.subitem8_title_raw)

    subitem8_title_raw: Optional[etree._Element] = element(tag="Subitem8Title", default=None, exclude=True)


class Subitem9Title(TaggedText, tag="Subitem9Title"):
    """
    号細分９名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem9Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem9_title: 号細分９名
    """

    @computed_element(tag="Subitem9Title")  # type: ignore[arg-type]
    def subitem9_title(self) -> Optional[Subitem9Title]:
        if self.subitem9_title_raw is None:
            return None
        return Subitem9Title(raw_element=self.subitem9_title_raw)

    subitem9_title_raw: Optional[etree._Element] = element(tag="Subitem9Title", default=None, exclude=True)


class Subitem10Title(TaggedText, tag="Subitem10Title"):
    """
    号細分１０名

    Attributes:
        tagged_text: タグ付きテキスト
        text: テキスト文字列
    """


class WithSubitem10Title(BaseXmlModel, arbitrary_types_allowed=True):
    """
    A mixin class to add the below attribute.

    Attributes:
        subitem10_title: 号細分１０名
    """

    @computed_element(tag="Subitem10Title")  # type: ignore[arg-type]
    def subitem10_title(self) -> Optional[Subitem10Title]:
        if self.subitem10_title_raw is None:
            return None
        return Subitem10Title(raw_element=self.subitem10_title_raw)

    subitem10_title_raw: Optional[etree._Element] = element(tag="Subitem10Title", default=None, exclude=True)


class Column(WithSentences, tag="Column"):
    """
    欄

    Attributes:
        num: 番号
        line_break: 改行
        align: 欄位置（"left"：左詰め、"center"：中央寄せ、"right"：右詰め、"justify"：均等割り付け）

        sentences: 段
    """

    num: Optional[NonNegativeInt] = attr(name="Num", default=None)
    line_break: Optional[bool] = attr(Name="LineBreak", default=None)
    align: Optional[Literal["left", "center", "right", "justify"]] = attr(Name="Align", default=None)

    def texts(self) -> Generator[str, None, None]:
        if self.sentences is not None:
            for sentence in self.sentences:
                yield sentence.text


class TableColumn(WithSentences, tag="TableColumn", search_mode="unordered"):
    """
    表欄

    Attributes:
        border_top: 上罫線（"solid"：実線、"dotted"：点線、"double"：二重線、"none"：無）
        border_bottom: 下罫線（"solid"：実線、"dotted"：点線、"double"：二重線、"none"：無）
        border_left: 左罫線（"solid"：実線、"dotted"：点線、"double"：二重線、"none"：無）
        border_right: 右罫線（"solid"：実線、"dotted"：点線、"double"：二重線、"none"：無）
        rowspan: 項結合
        colspan: 欄結合
        align: 欄位置（"left"：左詰め、"center"：中央寄せ、"right"：右詰め、"justify"：均等割り付け）
        valign: 項位置（"top"：上寄せ、"middle"：中央寄せ、"bottom"：下寄せ）

        parts: 編
        chapters: 章
        sections: 節
        subsections: 款
        divisions: 目
        articles: 条
        paragraphs: 項
        items: 号
        subitems1: 号細分
        subitems2: 号細分２
        subitems3: 号細分３
        subitems4: 号細分４
        subitems5: 号細分５
        subitems6: 号細分６
        subitems7: 号細分７
        subitems8: 号細分８
        subitems9: 号細分９
        subitems10: 号細分１０
        fig_structs: 図項目
        remarks: 備考
        sentences: 段
        columns: 欄
    """

    border_top: Optional[Literal["solid", "dotted", "double", "none"]] = attr(name="BorderTop", default=None)
    border_bottom: Optional[Literal["solid", "dotted", "double", "none"]] = attr(name="BorderBottom", default=None)
    border_left: Optional[Literal["solid", "dotted", "double", "none"]] = attr(name="BorderLeft", default=None)
    border_right: Optional[Literal["solid", "dotted", "double", "none"]] = attr(name="BorderRight", default=None)
    rowspan: Optional[PositiveInt] = attr(name="rowspan", default=None)
    colspan: Optional[PositiveInt] = attr(name="colspan", default=None)
    align: Optional[Literal["left", "center", "right", "justify"]] = attr(name="Align", default=None)
    valign: Optional[Literal["top", "middle", "bottom"]] = attr(name="Valign", default=None)

    parts: Optional[list["Part"]] = None
    chapters: Optional[list["Chapter"]] = None
    sections: Optional[list["Section"]] = None
    subsections: Optional[list["Subsection"]] = None
    divisions: Optional[list["Division"]] = None
    articles: Optional[list["Article"]] = None
    paragraphs: Optional[list["Paragraph"]] = None
    items: Optional[list["Item"]] = None
    subitems1: Optional[list["Subitem1"]] = None
    # subitems2: Optional[list[Subitem2]] = None
    # subitems3: Optional[list[Subitem3]] = None
    # subitems4: Optional[list[Subitem4]] = None
    # subitems5: Optional[list[Subitem5]] = None
    # subitems6: Optional[list[Subitem6]] = None
    # subitems7: Optional[list[Subitem7]] = None
    # subitems8: Optional[list[Subitem8]] = None
    # subitems9: Optional[list[Subitem9]] = None
    # subitems10: Optional[list[Subitem10]] = None
    fig_structs: Optional[list["FigStruct"]] = None
    remarks: Optional["Remarks"] = None
    columns: Optional[list["Column"]] = None


class TableRow(BaseXmlModel, tag="TableRow"):
    """
    表項

    Attributes:
        table_columns: 表欄
    """

    table_columns: list[TableColumn]


class TableHeaderRow(WithTableHeaderColumns, tag="TableHeaderRow"):
    """
    表欄名項

    Attributes:
        table_header_columns: 表欄名
    """


class Table(BaseXmlModel, tag="Table"):
    """
    表

    Attributes:
        writing_mode: 行送り方向（"vertical"：縦書き、"horizontal"：横書き）

        table_header_row: 表欄名項
        table_row: 表項
    """

    writing_mode: Optional[Literal["vertical", "horizontal"]] = attr(name="WritingMode", default=None)

    table_header_rows: Optional[list[TableHeaderRow]] = None
    table_rows: list[TableRow]


class ItemSentence(WithSentences, tag="ItemSentence", search_mode="unordered"):
    """
    号文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None

    def texts(self) -> Generator[str, None, None]:
        if self.sentences is not None:
            for sentence in self.sentences:
                yield sentence.text
        if self.columns is not None:
            for column in self.columns:
                for text in column.texts():
                    yield text
        # TODO Other fields https://www.tashiro-ip.com/ip-law/xml-schema.html#e-ItemSentence


class ClassSentence(WithSentences, tag="ClassSentence", search_mode="unordered"):
    """
    類文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class TableStruct(WithTableStructTitle, tag="TableStruct"):
    """
    表項目

    Attributes:
        table_struct_title: 表項目名
        pre_remarks: 備考
        table: 表
        post_remarks: 備考
    """

    pre_remarks: Optional[list["Remarks"]] = None
    table: Table
    post_remarks: Optional[list["Remarks"]] = None


class FigStruct(WithFigStructTitle, tag="FigStruct"):
    """
    図項目

    Attributes:
        fig_struct_title: 図項目名
        pre_remarks: 備考
        fig: 図
        post_remarks: 備考
    """

    pre_remarks: Optional[list["Remarks"]] = None
    fig: Fig
    post_remarks: Optional[list["Remarks"]] = None


class NoteStruct(WithNoteStructTitle, tag="NoteStruct"):
    """
    様式項目

    Attributes:
        note_struct_title: 様式項目名
        pre_remarks: 備考
        note: 記
        post_remarks: 備考
    """

    pre_remarks: Optional[list["Remarks"]] = None
    note: Note
    post_remarks: Optional[list["Remarks"]] = None


class StyleStruct(WithStyleStructTitle, tag="StyleStruct"):
    """
    様式項目

    Attributes:
        style_struct_title: 様式項目名
        pre_remarks: 備考
        style: 様式
        post_remarks: 備考
    """

    pre_remarks: Optional[list["Remarks"]] = None
    style: Style
    post_remarks: Optional[list["Remarks"]] = None


class FormatStruct(WithFormatStructTitle, tag="FormatStruct"):
    """
    書式項目

    Attributes:
        format_struct_title: 書式項目名
        pre_remarks: 備考
        format: 書式
        post_remarks: 備考
    """

    pre_remarks: Optional[list["Remarks"]] = None
    format: Format
    post_remarks: Optional[list["Remarks"]] = None


class ListSentence(WithSentences, tag="ListSentence"):
    """
    列記文

    Attributes:
        sentences: 段
        columns: 欄
    """

    columns: Optional[list[Column]] = None


class Sublist1Sentence(WithSentences, tag="Sublist1Sentence"):
    """
    列記細分１文

    Attributes:
        sentences: 段
        columns: 欄
    """

    columns: Optional[list[Column]] = None


class Sublist2Sentence(WithSentences, tag="Sublist2Sentence"):
    """
    列記細分２文

    Attributes:
        sentences: 段
        columns: 欄
    """

    columns: Optional[list[Column]] = None


class Sublist3Sentence(WithSentences, tag="Sublist3Sentence"):
    """
    列記細分３文

    Attributes:
        sentences: 段
        columns: 欄
    """

    columns: Optional[list[Column]] = None


class Sublist3(BaseXmlModel, tag="Sublist3"):
    """
    列記細分３

    Attributes:
        sublist1_sentence: 列記細分３文
    """

    sublist3_sentence: Sublist3Sentence


class Sublist2(BaseXmlModel, tag="Sublist2"):
    """
    列記細分２

    Attributes:
        sublist2_sentence: 列記細分２文
        sublists3: 列記細分３
    """

    sublist2_sentence: Sublist2Sentence
    sublists3: Optional[list[Sublist3]] = None


class Sublist1(BaseXmlModel, tag="Sublist1"):
    """
    列記細分１

    Attributes:
        sublist1_sentence: 列記細分１文
        sublists2: 列記細分２
    """

    sublist1_sentence: Sublist1Sentence
    sublists2: Optional[list[Sublist2]] = None


class List(BaseXmlModel, tag="List"):
    """
    列記

    Attributes:
        list_sentence: 列記文
        sublists1: 列記細分１
    """

    list_sentence: ListSentence
    sublists1: Optional[list[Sublist1]] = None


class Subitem1Sentence(WithSentences, tag="Subitem1Sentence", search_mode="unordered"):
    """
    号細分文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None

    def texts(self) -> Generator[str, None, None]:
        if self.sentences is not None:
            for sentence in self.sentences:
                yield sentence.text
        if self.columns is not None:
            for column in self.columns:
                for text in column.texts():
                    yield text
        # TODO self.table


class Subitem2Sentence(WithSentences, tag="Subitem2Sentence", search_mode="unordered"):
    """
    号細分２文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class Subitem3Sentence(WithSentences, tag="Subitem3Sentence", search_mode="unordered"):
    """
    号細分３文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class Subitem4Sentence(WithSentences, tag="Subitem4Sentence", search_mode="unordered"):
    """
    号細分４文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class Subitem5Sentence(WithSentences, tag="Subitem5Sentence", search_mode="unordered"):
    """
    号細分５文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class Subitem6Sentence(WithSentences, tag="Subitem6Sentence", search_mode="unordered"):
    """
    号細分６文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class Subitem7Sentence(WithSentences, tag="Subitem7Sentence", search_mode="unordered"):
    """
    号細分７文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class Subitem8Sentence(WithSentences, tag="Subitem8Sentence", search_mode="unordered"):
    """
    号細分８文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class Subitem9Sentence(WithSentences, tag="Subitem9Sentence", search_mode="unordered"):
    """
    号細分９文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class Subitem10Sentence(WithSentences, tag="Subitem10Sentence", search_mode="unordered"):
    """
    号細分１０文

    Attributes:
        sentences: 段
        columns: 欄
        table: 表
    """

    columns: Optional[list[Column]] = None
    table: Optional[Table] = None


class Subitem10(WithSubitem10Title, tag="Subitem10", search_mode="unordered"):
    """
    号細分１０

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem10_title: 号細分１０名
        subitem10_sentence: 号細分１０文
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem10_sentence: Subitem10Sentence
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None


class Subitem9(WithSubitem9Title, tag="Subitem9", search_mode="unordered"):
    """
    号細分９

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem9_title: 号細分９名
        subitem9_sentence: 号細分９文
        subitems10: 号細分１０
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem9_sentence: Subitem9Sentence
    subitems10: Optional[list[Subitem10]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None


class Subitem8(WithSubitem8Title, tag="Subitem8", search_mode="unordered"):
    """
    号細分８

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem8_title: 号細分８名
        subitem8_sentence: 号細分８文
        subitems9: 号細分９
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem8_sentence: Subitem8Sentence
    subitems9: Optional[list[Subitem9]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None


class Subitem7(WithSubitem7Title, tag="Subitem7", search_mode="unordered"):
    """
    号細分７

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem7_title: 号細分７名
        subitem7_sentence: 号細分７文
        subitems8: 号細分８
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem7_sentence: Subitem7Sentence
    subitems8: Optional[list[Subitem8]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None


class Subitem6(WithSubitem6Title, tag="Subitem6", search_mode="unordered"):
    """
    号細分６

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem6_title: 号細分６名
        subitem6_sentence: 号細分６文
        subitems7: 号細分７
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem6_sentence: Subitem6Sentence
    subitems7: Optional[list[Subitem7]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None


class Subitem5(WithSubitem5Title, tag="Subitem5", search_mode="unordered"):
    """
    号細分５

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem5_title: 号細分５名
        subitem5_sentence: 号細分５文
        subitems6: 号細分６
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem5_sentence: Subitem5Sentence
    subitems6: Optional[list[Subitem6]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None


class Subitem4(WithSubitem4Title, tag="Subitem4", search_mode="unordered"):
    """
    号細分４

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem4_title: 号細分４名
        subitem4_sentence: 号細分４文
        subitems5: 号細分５
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem4_sentence: Subitem4Sentence
    subitems5: Optional[list[Subitem5]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None


class Subitem3(WithSubitem3Title, tag="Subitem3", search_mode="unordered"):
    """
    号細分３

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem3_title: 号細分３名
        subitem3_sentence: 号細分３文
        subitems4: 号細分４
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem3_sentence: Subitem3Sentence
    subitems4: Optional[list[Subitem4]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None


class Subitem2(WithSubitem2Title, tag="Subitem2", search_mode="unordered"):
    """
    号細分２

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem2_title: 号細分２名
        subitem2_sentence: 号細分２文
        subitems3: 号細分３
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem2_sentence: Subitem2Sentence
    subitems3: Optional[list[Subitem3]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None


class Subitem1(WithSubitem1Title, tag="Subitem1", search_mode="unordered"):
    """
    号細分

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subitem1_title: 号細分名
        subitem1_sentence: 号細分文
        subitems2: 号細分２
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    subitem1_sentence: Subitem1Sentence
    subitems2: Optional[list[Subitem2]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None

    def texts(self) -> Generator[str, None, None]:
        if self.subitem1_title is not None:
            yield self.subitem1_title.text
        for text in self.subitem1_sentence.texts():
            yield text
        # TODO self.subitems2
        # if self.subitems2 is not None:
        #     for subitem2 in self.subitems2:
        #         for text in subitem2.texts():
        #             yield text
        # TODO self.table_structs
        # TODO self.fig_structs
        # TODO self.style_structs
        # TODO self.lists


class Item(WithItemTitle, tag="Item", search_mode="unordered"):
    """
    号

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        item_title: 号名
        item_sentence: 号文
        subitems: 号細分
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        lists: 列記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    item_sentence: ItemSentence
    subitems: Optional[list[Subitem1]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    lists: Optional[list[List]] = None

    def texts(self) -> Generator[str, None, None]:
        if self.item_title is not None:
            yield self.item_title.text
        for text in self.item_sentence.texts():
            yield text
        if self.subitems is not None:
            for subitem in self.subitems:
                for text in subitem.texts():
                    yield text
        # TODO Other fields https://www.tashiro-ip.com/ip-law/xml-schema.html#e-Item


class Class(WithClassTitle, tag="Class", search_mode="unordered"):
    """
    類

    Attributes:
        num: 番号

        class_title: 類名
        class_sentence: 類文
        items: 号
    """

    num: str = attr(name="Num")

    class_sentence: ClassSentence
    items: Optional[list[Item]] = None


class AmendProvisionSentence(WithSentences, tag="AmendProvisionSentence"):
    """
    改正規定文

    Attributes:
        sentences: 段
    """


class AmendProvision(BaseXmlModel, tag="AmendProvision"):
    """
    改正規定

    Attributes:
        amend_provision_sentence: 改正規定文
        new_provisions: 新規定
    """

    amend_provision_sentence: Optional[AmendProvisionSentence] = None
    new_provisions: Optional[list["NewProvision"]] = None


class ParagraphSentence(WithSentences, tag="ParagraphSentence"):
    """
    項文

    Attributes:
        sentences: 段
    """

    def texts(self) -> Generator[str, None, None]:
        if self.sentences is not None:
            for sentence in self.sentences:
                yield sentence.text


class Paragraph(WithParagraphCaption, WithParagraphNum, tag="Paragraph", search_mode="unordered"):
    """
    項

    Attributes:
        num: 番号
        old_style: 旧スタイル
        old_num: 旧番号
        hide: 非表示

        paragraph_caption: 条名
        paragraph_num: 項番号
        paragraph_sentence: 項文
        amend_provisions: 改正規定
        classes: 類
        table_structs: 表項目
        fig_structs: 図項目
        style_structs: 様式項目
        items: 号
    """

    num: NonNegativeInt = attr(name="Num")
    old_style: Optional[bool] = attr(name="OldStyle", default=None)
    old_num: Optional[bool] = attr(name="OldNum", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    paragraph_sentence: ParagraphSentence
    amend_provisions: Optional[list[AmendProvision]] = None
    classes: Optional[list[Class]] = None
    table_structs: Optional[list[TableStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    items: Optional[list[Item]] = None

    def texts(self) -> Generator[str, None, None]:
        for text in self.paragraph_sentence.texts():
            yield text
        if self.items is not None:
            for item in self.items:
                for text in item.texts():
                    yield text
        # TODO Other fields https://www.tashiro-ip.com/ip-law/xml-schema.html#e-Paragraph


class Article(
    WithArticleCaption,
    WithArticleTitle,
    WithSupplNote,
    tag="Article",
    search_mode="unordered",
):
    """
    条

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        article_caption: 条見出し
        article_title: 条名
        paragraphs: 項
        suppl_note: 付記
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    paragraphs: list[Paragraph]

    def texts(self) -> Generator[str, None, None]:
        if self.article_caption is not None:
            yield self.article_caption.text

        article_title: ArticleTitle = self.article_title
        yield article_title.text

        if self.paragraphs is not None:
            for paragraph in self.paragraphs:
                for text in paragraph.texts():
                    yield text

        if self.suppl_note is not None:
            yield self.suppl_note.text


class Division(WithDivisionTitle, tag="Division"):
    """
    目

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        division_title: 目名
        articles: 条
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    articles: Optional[list[Article]] = None

    def texts(self) -> Generator[str, None, None]:
        if self.division_title is not None:
            yield self.division_title.text
        if self.articles is not None:
            for article in self.articles:
                for text in article.texts():
                    yield text


class Subsection(WithSubsectionTitle, tag="Subsection", search_mode="unordered"):
    """
    款

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        subsection_title: 款名
        articles: 条
        divisions: 目
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    articles: Optional[list[Article]] = None
    divisions: Optional[list[Division]] = None

    def texts(self) -> Generator[str, None, None]:
        if self.subsection_title is not None:
            yield self.subsection_title.text
        if self.articles is not None:
            for article in self.articles:
                for text in article.texts():
                    yield text
        if self.divisions is not None:
            for division in self.divisions:
                for text in division.texts():
                    yield text


class Section(WithSectionTitle, tag="Section", search_mode="unordered"):
    """
    節

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        section_title: 節名
        articles: 条
        subsections: 款
        divisions: 目
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    articles: Optional[list[Article]] = None
    subsections: Optional[list[Subsection]] = None
    divisions: Optional[list[Division]] = None

    def texts(self) -> Generator[str, None, None]:
        if self.section_title is not None:
            yield self.section_title.text
        if self.articles is not None:
            for article in self.articles:
                for text in article.texts():
                    yield text
        if self.subsections is not None:
            for subsection in self.subsections:
                for text in subsection.texts():
                    yield text
        if self.divisions is not None:
            for division in self.divisions:
                for text in division.texts():
                    yield text


class Chapter(WithChapterTitle, tag="Chapter", search_mode="unordered"):
    """
    章

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        part_title: 章名
        articles: 条
        sections: 節
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    articles: Optional[list[Article]] = None
    sections: Optional[list[Section]] = None

    def texts(self) -> Generator[str, None, None]:
        if self.chapter_title is not None:
            yield self.chapter_title.text
        if self.articles is not None:
            for article in self.articles:
                for text in article.texts():
                    yield text
        if self.sections is not None:
            for section in self.sections:
                for text in section.texts():
                    yield text


class Part(WithPartTitle, tag="Part", search_mode="unordered"):
    """
    編

    Attributes:
        num: 番号
        delete: 削除
        hide: 非表示

        part_title: 編名
        articles: 条
        chapters: 章
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)
    hide: Optional[bool] = attr(name="Hide", default=None)

    articles: Optional[list[Article]] = None
    chapters: Optional[list[Chapter]] = None

    def texts(self) -> Generator[str, None, None]:
        if self.part_title is not None:
            yield self.part_title.text
        if self.articles is not None:
            for article in self.articles:
                for text in article.texts():
                    yield text
        if self.chapters is not None:
            for chapter in self.chapters:
                for text in chapter.texts():
                    yield text


class TOCDivision(WithDivisionTitle, WithArticleRange, tag="TOCDivision"):
    """
    目次目

    Attributes:
        division_title: 目名
        article_range: 条範囲
    """


class TOCSubsection(WithSubsectionTitle, WithArticleRange, tag="TOCSubsection", search_mode="unordered"):
    """
    目次款

    Attributes:
        num: 番号
        delete: 削除

        subsection_title: 款名
        article_range: 条範囲
        toc_divisions: 目次目
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)

    toc_divisions: Optional[list[TOCDivision]] = None


class TOCSection(WithSectionTitle, WithArticleRange, tag="TOCSection", search_mode="unordered"):
    """
    目次節

    Attributes:
        num: 番号
        delete: 削除

        section_title: 節名
        article_range: 条範囲
        toc_subsections: 目次款
        toc_divisions: 目次目
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)

    toc_subsections: Optional[list[TOCSubsection]] = None
    toc_divisions: Optional[list[TOCDivision]] = None


class TOCArticle(WithArticleTitle, WithArticleCaption, tag="TOCArticle"):
    """
    目次条

    Attributes:
        num: 番号
        delete: 削除

        article_title: 条名
        article_caption: 条見出し
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)


class TOCChapter(WithChapterTitle, WithArticleRange, tag="TOCChapter", search_mode="unordered"):
    """
    目次章

    Attributes:
        num: 番号
        delete: 削除

        chapter_title: 章名
        article_range: 条範囲
        toc_section: 目次節
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)

    toc_sections: Optional[list[TOCSection]] = None


class TOCPart(WithPartTitle, tag="TOCPart", search_mode="unordered"):
    """
    目次編

    Attributes:
        num: 番号
        delete: 削除

        part_title: 編名
        toc_chapter: 目次章
    """

    num: str = attr(name="Num")
    delete: Optional[bool] = attr(name="Delete", default=None)

    toc_chapters: Optional[list[TOCChapter]] = None


class TOCSupplProvision(WithSupplProvisionLabel, WithArticleRange, tag="TOCSupplProvision", search_mode="unordered"):
    """
    目次附則

    Attributes:
        suppl_provision_label: 附則ラベル
        article_range: 条範囲
        toc_articles: 目次条
        toc_chapters: 目次章
    """

    toc_articles: Optional[list[TOCArticle]] = None
    toc_chapters: Optional[list[TOCChapter]] = None


class TOC(WithTOCAppdxTableLabels, tag="TOC", search_mode="unordered"):
    """
    目次

    Attributes:
        toc_label: 目次ラベル
        toc_preamble_label: 目次前文ラベル
        toc_parts: 目次編
        toc_chapters: 目次章
        toc_sections: 目次節
        toc_articles: 目次条
        toc_suppl_provision: 目次附則
        toc_appdx_table_labels: 目次別表ラベル
    """

    toc_label: Optional[str] = element(tag="TOCLabel", default=None)
    toc_preamble_label: Optional[str] = element(tag="TOCPreambleLabel", default=None)
    toc_parts: Optional[list[TOCPart]] = None
    toc_chapters: Optional[list[TOCChapter]] = None
    toc_sections: Optional[list[TOCSection]] = None
    toc_articles: Optional[list[TOCArticle]] = None
    toc_suppl_provision: Optional[TOCSupplProvision] = None


class Preamble(BaseXmlModel, tag="Preamble"):
    """
    前文

    Attributes:
        paragraphs: 項
    """

    paragraphs: list[Paragraph]


class MainProvision(BaseXmlModel, tag="MainProvision", search_mode="unordered"):
    """
    本則

    Attributes:
        extract: 抄

        parts: 編
        chapters: 章
        sections: 節
        articles: 条
        paragraphs: 項
    """

    extract: Optional[bool] = attr(name="Extract", default=None)

    parts: Optional[list[Part]] = None
    chapters: Optional[list[Chapter]] = None
    sections: Optional[list[Section]] = None
    articles: Optional[list[Article]] = None
    paragraphs: Optional[list[Paragraph]] = None

    def texts(self) -> Generator[str, None, None]:
        if self.parts is not None:
            for part in self.parts:
                for text in part.texts():
                    yield text
        if self.chapters is not None:
            for chapter in self.chapters:
                for text in chapter.texts():
                    yield text
        if self.sections is not None:
            for section in self.sections:
                for text in section.texts():
                    yield text
        if self.articles is not None:
            for article in self.articles:
                for text in article.texts():
                    yield text
        if self.paragraphs is not None:
            for paragraph in self.paragraphs:
                for text in paragraph.texts():
                    yield text


class SupplProvisionAppdxTable(
    WithSupplProvisionAppdxTableTitle, WithRelatedArticleNum, tag="SupplProvisionAppdxTable"
):
    """
    附則別表

    Attributes:
        num: 番号

        suppl_provision_appdx_table_title: 附則別表名
        related_article_num: 関係条文番号
        table_structs: 表項目
    """

    num: Optional[str] = attr(name="Num", default=None)

    table_structs: Optional[list[TableStruct]] = None


class SupplProvisionAppdxStyle(
    WithSupplProvisionAppdxStyleTitle, WithRelatedArticleNum, tag="SupplProvisionAppdxStyle"
):
    """
    附則様式

    Attributes:
        num: 番号

        suppl_provision_appdx_style_title: 附則様式名
        related_article_num: 関係条文番号
        style_structs: 様式項目
    """

    num: Optional[str] = attr(name="Num", default=None)

    style_structs: Optional[list[StyleStruct]] = None


class SupplProvisionAppdx(WithArithFormulaNum, WithRelatedArticleNum, tag="SupplProvisionAppdx"):
    """
    附則付録

    Attributes:
        num: 番号

        arith_formula_num: 算式番号
        related_article_num: 関係条文番号
        arith_formulas: 算式
    """

    num: Optional[str] = attr(name="Num", default=None)

    arith_formulas: Optional[list[ArithFormula]] = None


class SupplProvision(WithSupplProvisionLabel, tag="SupplProvision", search_mode="unordered"):
    """
    附則

    Attributes:
        type: 種類（"New"：制定、"Amend"：改正）
        amend_law_num: 改正法令番号
        extract: 抄

        suppl_provision_label: 附則ラベル
        chapters: 章
        articles: 条
        paragraphs: 項
        suppl_provision_appdx_tables: 附則別表
        suppl_provision_appdx_styles: 附則様式
        suppl_provision_appdx: 附則付録
    """

    type: Optional[Literal["New", "Amend"]] = attr(name="Type", default=None)
    amend_law_num: Optional[str] = attr(name="AmendLawNum", default=None)
    extract: Optional[bool] = attr(name="Extract", default=None)

    chapters: Optional[list[Chapter]] = None
    articles: Optional[list[Article]] = None
    paragraphs: Optional[list[Paragraph]] = None
    suppl_provision_appdx_tables: Optional[list[SupplProvisionAppdxTable]] = None
    suppl_provision_appdx_styles: Optional[list[SupplProvisionAppdxStyle]] = None
    suppl_provision_appdx: Optional[list[SupplProvisionAppdx]] = None


class AppdxTable(WithAppdxTableTitle, WithRelatedArticleNum, tag="AppdxTable", search_mode="unordered"):
    """
    別表

    Attributes:
        num: 番号

        appdx_table_title: 別表名
        related_article_num: 関係条文番号
        table_structs: 表項目
        items: 号
        remarks: 備考
    """

    num: Optional[str] = attr(name="Num", default=None)

    table_structs: Optional[list[TableStruct]] = None
    items: Optional[list[Item]] = None
    remarks: Optional[list["Remarks"]] = None


class AppdxNote(WithAppdxNoteTitle, WithRelatedArticleNum, tag="AppdxNote", search_mode="unordered"):
    """
    別記

    Attributes:
        num: 番号

        appdx_note_title: 別記名
        related_article_num: 関係条文番号
        note_structs: 記項目
        fig_structs: 図項目
        table_structs: 表項目
        remarks: 備考
    """

    num: Optional[str] = attr(name="Num", default=None)

    note_structs: Optional[list[NoteStruct]] = None
    fig_structs: Optional[list[FigStruct]] = None
    table_structs: Optional[list[TableStruct]] = None
    remarks: Optional[list["Remarks"]] = None


class AppdxStyle(WithAppdxStyleTitle, WithRelatedArticleNum, tag="AppdxStyle"):
    """
    別記様式

    Attributes:
        num: 番号

        appdx_style_title: 別記様式名
        related_article_num: 関係条文番号
        style_structs: 様式項目
        remarks: 備考
    """

    num: Optional[str] = attr(name="Num", default=None)

    style_structs: Optional[list[StyleStruct]] = None
    remarks: Optional[list["Remarks"]] = None


class Appdx(WithArithFormulaNum, WithRelatedArticleNum, tag="Appdx"):
    """
    付録

    Attributes:
        arith_formula_num: 算式番号
        related_article_num: 関係条文番号
        arith_formulas: 算式
        remarks: 備考
    """

    arith_formulas: Optional[list[ArithFormula]] = None
    remarks: Optional[list["Remarks"]] = None


class AppdxFig(WithAppdxFigTitle, WithRelatedArticleNum, tag="AppdxFig"):
    """
    別図

    Attributes:
        num: 番号

        appdx_fig_title: 別図名
        related_article_num: 関係条文番号
        fig_structs: 図項目
        table_structs: 表項目
    """

    num: Optional[str] = attr(name="Num", default=None)

    fig_structs: Optional[list[FigStruct]] = None
    table_structs: Optional[list[TableStruct]] = None


class AppdxFormat(WithAppdxFormatTitle, WithRelatedArticleNum, tag="AppdxFig"):
    """
    別記書式

    Attributes:
        num: 番号

        appdx_format_title: 別記書式名
        related_article_num: 関係条文番号
        format_structs: 書式項目
        remarks: 備考
    """

    num: Optional[str] = attr(name="Num", default=None)

    format_structs: Optional[list[FormatStruct]] = None
    remarks: Optional[list["Remarks"]] = None


class LawBody(
    WithLawTitle,
    WithEnactStatement,
    tag="LawBody",
    search_mode="unordered",
):
    """
    法令本体

    Attributes:
        subject: 件名

        law_title: 題名
        enact_statement: 制定文
        toc: 目次
        preamble: 前文
        main_provision: 本則
        suppl_provisions: 附則
        appdx_tables: 別表
        appdx_notes: 別記
        appdx_styles: 別記様式
        appdx: 付録
        appdx_figs: 別図
        appdx_formats: 別記書式
    """

    subject: Optional[str] = attr(name="Subject", default=None)

    toc: Optional[TOC] = None
    preamble: Optional[Preamble] = None
    main_provision: MainProvision
    suppl_provisions: Optional[list[SupplProvision]] = None
    appdx_tables: Optional[list[AppdxTable]] = None
    appdx_notes: Optional[list[AppdxNote]] = None
    appdx_styles: Optional[list[AppdxStyle]] = None
    appdx: Optional[list[Appdx]] = None
    appdx_figs: Optional[list[AppdxFig]] = None
    appdx_formats: Optional[list[AppdxFormat]] = None

    def texts(self) -> Generator[str, None, None]:
        if self.law_title is not None:
            yield self.law_title.text
        if self.enact_statement is not None:
            yield self.enact_statement.text
        # TODO self.preamble
        for text in self.main_provision.texts():
            yield text
        # TODO Other fields


class Remarks(WithRemarksLabel, WithSentences, tag="Remarks"):
    """
    備考

    Attributes:
        remarks_label: 備考ラベル
        items: 号
        sentences: 段
    """

    items: Optional[list[Item]] = None


class NewProvision(
    WithLawTitle,
    WithPartTitle,
    WithChapterTitle,
    WithSectionTitle,
    WithSubsectionTitle,
    WithDivisionTitle,
    WithSupplNotes,
    WithSentences,
    tag="NewProvision",
    search_mode="unordered",
):
    """
    新規定

    Attributes:
        preamble: 前文
        toc: 目次
        parts: 編
        part_title: 編名
        chapters: 章
        chapter_title: 章名
        sections: 節
        section_title: 節名
        subsections: 款
        subsection_title: 款名
        divisions: 目
        division_title: 目名
        articles: 条
        suppl_notes: 付記
        paragraphs: 項
        items: 号
        subitems1: 号細分
        subitems2: 号細分２
        subitems3: 号細分３
        subitems4: 号細分４
        subitems5: 号細分５
        subitems6: 号細分６
        subitems7: 号細分７
        subitems8: 号細分８
        subitems9: 号細分９
        subitems10: 号細分１０
        lists: 列記
        sentences: 段
        amend_provisions: 改正規定
        appdx_tables: 別表
        appdx_notes: 別記
        appdx_styles: 別記様式
        appdxs: 付録
        appdx_figs: 別図
        appdx_formats: 別記書式
        suppl_provision_appdx_styles: 附則様式
        suppl_provision_appdx_tables: 附則別表
        suppl_provision_appdxs: 附則付録
        table_structs: 表項目
        table_rows: 表項
        table_columns: 表欄
        fig_structs: 図項目
        note_structs: 記項目
        style_structs: 様式項目
        format_structs: 書式項目
        remarks: 備考
        law_body: 法令本体
    """

    preamble: Optional[Preamble] = None
    toc: Optional[TOC] = None
    parts: Optional[list[Part]] = None
    chapters: Optional[list[Chapter]] = None
    sections: Optional[list[Section]] = None
    sub_sections: Optional[list[Subsection]] = None
    divisions: Optional[list[Division]] = None
    articles: Optional[list[Article]] = None
    paragraphs: Optional[list[Paragraph]] = None
    items: Optional[list[Item]] = None
    subitems1: Optional[list[Subitem1]] = None
    subitems2: Optional[list[Subitem2]] = None
    subitems3: Optional[list[Subitem3]] = None
    subitems4: Optional[list[Subitem4]] = None
    subitems5: Optional[list[Subitem5]] = None
    subitems6: Optional[list[Subitem6]] = None
    subitems7: Optional[list[Subitem7]] = None
    subitems8: Optional[list[Subitem8]] = None
    subitems9: Optional[list[Subitem9]] = None
    subitems10: Optional[list[Subitem10]] = None
    lists: Optional[list[List]] = None
    amend_provisions: Optional[list[AmendProvision]] = None
    appdx_tables: Optional[list[AppdxTable]] = None
    appdx_notes: Optional[list[AppdxNote]] = None
    appdx_styles: Optional[list[AppdxStyle]] = None
    appdx: Optional[list[Appdx]] = None
    appdx_figs: Optional[list[AppdxFig]] = None
    appdx_formats: Optional[list[AppdxFormat]] = None
    suppl_provision_appdx_styles: Optional[list[SupplProvisionAppdxStyle]] = None
    suppl_provision_appdx_tables: Optional[list[SupplProvisionAppdxTable]] = None
    suppl_provision_appdxs: Optional[list[SupplProvisionAppdx]] = None
    table_structs: Optional[list[TableStruct]] = None
    table_rows: Optional[list[TableRow]] = None
    table_columns: Optional[list[TableColumn]] = None
    fig_structs: Optional[list[FigStruct]] = None
    note_structs: Optional[list[NoteStruct]] = None
    style_structs: Optional[list[StyleStruct]] = None
    format_structs: Optional[list[FormatStruct]] = None
    remarks: Optional[list[Remarks]] = None
    law_body: Optional[LawBody] = None


class Law(BaseXmlModel, tag="Law"):
    """
    法令

    Attributes:
        era: 元号
        year: 年号
        num: 番号
        law_type: 種別（"Constitution"：憲法、"Act"：法律、"CabinetOrder"：政令、
        "ImperialOrder"：勅令、"MinisterialOrdinance"：府省令、"Rule"：規則、"Misc"：その他）
        lang: 言語
        promulgate_month: 公布月
        promulgate_day: 公布日

        law_num: 法令番号
        law_body: 法令本体
    """

    era: str = attr(name="Era")
    year: PositiveInt = attr(name="Year")
    num: NonNegativeInt = attr(name="Num")
    law_type: Literal[
        "Constitution",
        "Act",
        "CabinetOrder",
        "ImperialOrder",
        "MinisterialOrdinance",
        "Rule",
        "Misc",
    ] = attr(name="LawType")
    lang: Literal["ja", "en"] = attr(name="Lang")
    promulgate_month: Optional[PositiveInt] = attr(name="PromulgateMonth", default=None)
    promulgate_day: Optional[PositiveInt] = attr(name="PromulgateDay", default=None)

    law_num: str = element(tag="LawNum")
    law_body: LawBody

    def texts(self) -> Generator[str, None, None]:
        for text in self.law_body.texts():
            yield text


def get_attr(element: etree._Element, tag: str) -> Optional[str]:
    attr: Optional[Union[str, bytes]] = element.attrib.get(tag)
    if attr is None:
        return None
    elif isinstance(attr, bytes):
        attr = attr.decode()
    return attr


# For avoiding "model is partially initialized" error.
# Type annotations of `Sentence`, `Line`, `QuoteStruct`, etc. depend on each other with the lazy manner.
# So, pydantic requires calling `model_rebuild()` after defining all classes.
# See details: https://errors.pydantic.dev/2.4/u/class-not-fully-defined
model = sys.modules[__name__]
for name, cls in inspect.getmembers(model, inspect.isclass):
    model_rebuild = getattr(cls, "model_rebuild", None)
    if callable(model_rebuild):
        model_rebuild()
