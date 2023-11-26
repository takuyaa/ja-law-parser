# Japanese Law Parser

[法令標準 XML スキーマ](https://elaws.e-gov.go.jp/file/XMLSchemaForJapaneseLaw_v3.xsd)に準拠する XML ファイルを解析し、 [pydantic](https://docs.pydantic.dev/) のモデルに変換するライブラリです。

[e-Gov法令検索](https://elaws.e-gov.go.jp/)で公開されている、日本国の法令 XML（憲法・法律・政令・勅令・府令・省令・規則）をパースし、解析結果を Python から利用することができます。

内部的に [pydantic-xml](https://pydantic-xml.readthedocs.io/) を利用して XML をパースしています。


## Installation

```shell
pip install ja-law-parser
```

## Usage

```python
from typing import Optional

from ja_law_parser.model import Article, Chapter, Law, Paragraph
from ja_law_parser.parser import LawParser

parser = LawParser()

law: Law = parser.parse(path="321CONSTITUTION_19470503_000000000000000.xml")
print(law.law_body.law_title.text)
# => 日本国憲法

chapter3: Optional[Chapter] = law.law_body.main_provision.chapters[2]
print(chapter3.chapter_title.text)
# => 三章　国民の権利及び義務

article11: Optional[Article] = chapter3.articles[1]
print(article11.article_title.text)
# => 第十一条

paragraph11: Optional[Paragraph] = article11.paragraphs[0]
print(paragraph11.paragraph_sentence.sentences[0].text)
# => 国民は、すべての基本的人権の享有を妨げられない。
print(paragraph11.paragraph_sentence.sentences[1].text)
# => この憲法が国民に保障する基本的人権は、侵すことのできない永久の権利として、現在及び将来の国民に与へられる。
```

詳細は API ドキュメントを参照してください。

## Reference

- [e-Gov法令検索 | デジタル庁](https://elaws.e-gov.go.jp/)
- [e-Gov法令検索 ヘルプ | デジタル庁](https://elaws.e-gov.go.jp/help/)
- [e-Gov法令検索 XML一括ダウンロード | デジタル庁](https://elaws.e-gov.go.jp/download/)
- [法令標準XMLスキーマについて | Web知財法](https://www.tashiro-ip.com/ip-law/xml-schema.html)
- [法律等を読み解くうえで必要な基礎知識 (PDF) | 株式会社みらい](https://www.mirai-inc.jp/support/roppo/basic-knowledge.pdf)
- [pydantic](https://github.com/pydantic/pydantic)
- [pydantic-xml](https://github.com/dapper91/pydantic-xml)
