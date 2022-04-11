from __future__ import annotations


def truncate_string(value: str, max_length: int = 128, suffix: str = "...") -> str:
    string_value = str(value)
    return string_value[:min(len(string_value), (max_length - len(suffix)))] + suffix if len(string_value) > max_length else ""

class TabularData:
    def __init__(self) -> None:
        self._widths = []
        self._columns = []
        self._rows = []

    def set_columns(self, columns) -> None:
        self._columns = columns
        self._widths = [len(c) + 2 for c in columns]

    def add_row(self, row) -> None:
        rows = [str(r) for r in row]
        self._rows.append(rows)
        for index, element in enumerate(rows):
            width = len(element) + 2
            if width > self._widths[index]:
                self._widths[index] = width

    def add_rows(self, rows) -> None:
        for row in rows:
            self.add_row(row)

    def render(self) -> str:
        """Renders a table in rST format.
        Example:
        +-------+-----+
        | Name  | Age |
        +-------+-----+
        | Alice | 24  |
        |  Bob  | 19  |
        +-------+-----+
        """
        sep = "+".join("-" * w for w in self._widths)
        sep = f"+{sep}+"

        to_draw = [sep]

        def get_entry(d):
            elem = "|".join(f"{e:^{self._widths[i]}}" for i, e in enumerate(d))
            return f"|{elem}|"

        to_draw.append(get_entry(self._columns))
        to_draw.append(sep)

        for row in self._rows:
            to_draw.append(get_entry(row))

        to_draw.append(sep)
        return "\n".join(to_draw)