from os import PathLike
from pathlib import Path

from .model import Law


class LawParser:
    def parse(
        self,
        path: str | PathLike[str],
    ) -> Law:
        """
        Parses the XML file and returns the result object.

        Args:
            path: The XML file path.

        Returns:
            The Law object.
        """
        bytes = Path(path).read_bytes()
        return self.parse_from(bytes)

    def parse_from(self, xml: str | bytes) -> Law:
        """
        Parses the XML text and returns the result object.

        Args:
            path: The XML text.

        Returns:
            The Law object.
        """
        return Law.from_xml(xml)
