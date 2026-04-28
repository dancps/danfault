import json
import re
import sys
from pathlib import Path

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )


RECIPES_FILE = Path.home() / ".config" / "danfault" / "coffee_recipes.json"

DEFAULT_RECIPES: dict[str, str] = {
    "V60": "1:15",
    "French Press": "1:10",
    "Espresso": "1:2",
    "Chemex": "1:17",
    "AeroPress": "1:13",
    "Cold Brew": "1:5",
    "Moka Pot": "1:7",
}

_GREEN = "#27ae60"
_RED = "#e74c3c"
_GRAY = "#888888"
_TOLERANCE = 0.5  # grams


def _load_recipes() -> dict[str, str]:
    if RECIPES_FILE.exists():
        try:
            data = json.loads(RECIPES_FILE.read_text())
            if isinstance(data, dict):
                return DEFAULT_RECIPES | data
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_RECIPES)


def _save_recipes(recipes: dict[str, str]) -> None:
    user_entries = {
        k: v for k, v in recipes.items()
        if k not in DEFAULT_RECIPES or v != DEFAULT_RECIPES[k]
    }
    RECIPES_FILE.parent.mkdir(parents=True, exist_ok=True)
    RECIPES_FILE.write_text(json.dumps(user_entries, indent=2))


def _parse_ratio(text: str):
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s*$", text)
    if m:
        c, w = float(m.group(1)), float(m.group(2))
        if c > 0 and w > 0:
            return c, w
    return None


def _parse_positive(text: str):
    try:
        v = float(text.strip())
        return v if v > 0 else None
    except (ValueError, AttributeError):
        return None


def _colored(text: str, color: str) -> str:
    return f'<span style="color:{color}; font-weight:600;">{text}</span>'


def _neutral(text: str) -> str:
    return f'<span style="color:{_GRAY};">{text}</span>'


def _compute_hints(ratio, coffee, water) -> tuple[str, str, str]:
    """Return (ratio_html, coffee_html, water_html) for the inline info labels."""
    filled = sum(x is not None for x in [ratio, coffee, water])
    if filled < 2:
        return "", "", ""

    if ratio is None:
        # Derive ratio from coffee + water
        derived = f"1:{water / coffee:.2f}".rstrip("0").rstrip(".")
        return _neutral(derived), "", ""

    rc, rw = ratio
    mult = rw / rc

    if water is None:
        return "", "", _neutral(f"{coffee * mult:.1f}g")

    if coffee is None:
        return "", _neutral(f"{water / mult:.1f}g"), ""

    # All three filled
    water_target = coffee * mult
    if abs(water - water_target) <= _TOLERANCE:
        return _colored("✓", _GREEN), "", ""

    coffee_target = water / mult
    coffee_diff = coffee_target - coffee
    water_diff = water_target - water

    coffee_diff_str = f"{coffee_diff:+.1f}g"
    water_diff_str = f"{water_diff:+.1f}g"

    coffee_diff_color = _GREEN if coffee_diff > 0 else _RED
    water_diff_color = _GREEN if water_diff > 0 else _RED

    coffee_html = f'{_neutral(f"{coffee_target:.1f}g")} {_colored(f"({coffee_diff_str})", coffee_diff_color)}'
    water_html = f'{_neutral(f"{water_target:.1f}g")} {_colored(f"({water_diff_str})", water_diff_color)}'

    return _colored("✗", _RED), coffee_html, water_html


class InfoLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setMinimumWidth(140)


class CoffeeCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coffee Calculator")
        self.setMinimumWidth(500)
        self._recipes = _load_recipes()
        self._build_ui()
        self._connect()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        bold = QFont()
        bold.setPointSize(13)
        bold.setBold(True)

        # ── Recipe bar ────────────────────────────────────────────────
        recipe_row = QHBoxLayout()
        recipe_row.setSpacing(8)

        recipe_label = QLabel("Recipe")
        recipe_label.setFont(bold)
        recipe_row.addWidget(recipe_label)

        self.recipe_combo = QComboBox()
        self.recipe_combo.setMinimumWidth(160)
        self._refresh_combo()
        recipe_row.addWidget(self.recipe_combo)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setFixedWidth(72)
        recipe_row.addWidget(self.apply_btn)

        self.save_btn = QPushButton("Save as…")
        self.save_btn.setFixedWidth(80)
        recipe_row.addWidget(self.save_btn)

        recipe_row.addStretch()
        outer.addLayout(recipe_row)

        # ── Divider ───────────────────────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        outer.addWidget(divider)

        # ── Input grid: label | field | info ─────────────────────────
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0, 150)
        grid.setColumnStretch(2, 1)

        grid.addWidget(QLabel("Ratio (coffee:water)"), 0, 0)
        self.ratio_input = QLineEdit()
        self.ratio_input.setPlaceholderText("e.g. 1:15 or 15:200")
        grid.addWidget(self.ratio_input, 0, 1)
        self.ratio_info = InfoLabel()
        grid.addWidget(self.ratio_info, 0, 2)

        grid.addWidget(QLabel("Coffee (g)"), 1, 0)
        self.coffee_input = QLineEdit()
        self.coffee_input.setPlaceholderText("e.g. 20")
        grid.addWidget(self.coffee_input, 1, 1)
        self.coffee_info = InfoLabel()
        grid.addWidget(self.coffee_info, 1, 2)

        grid.addWidget(QLabel("Water (g)"), 2, 0)
        self.water_input = QLineEdit()
        self.water_input.setPlaceholderText("e.g. 300")
        grid.addWidget(self.water_input, 2, 1)
        self.water_info = InfoLabel()
        grid.addWidget(self.water_info, 2, 2)

        outer.addLayout(grid)
        outer.addStretch()

    def _refresh_combo(self):
        self.recipe_combo.clear()
        for name in sorted(self._recipes):
            self.recipe_combo.addItem(f"{name}  ({self._recipes[name]})", userData=name)

    def _connect(self):
        for field in (self.ratio_input, self.coffee_input, self.water_input):
            field.textChanged.connect(self._calculate)
        self.apply_btn.clicked.connect(self._apply_recipe)
        self.save_btn.clicked.connect(self._save_recipe)

    # ── Recipe actions ────────────────────────────────────────────────

    def _apply_recipe(self):
        name = self.recipe_combo.currentData()
        if name and name in self._recipes:
            self.ratio_input.setText(self._recipes[name])

    def _save_recipe(self):
        ratio_text = self.ratio_input.text().strip()
        if not _parse_ratio(ratio_text):
            QMessageBox.warning(self, "Invalid ratio", "Enter a valid ratio (e.g. 1:15) before saving.")
            return

        name, ok = QInputDialog.getText(self, "Save Recipe", "Recipe name:")
        if not ok or not name.strip():
            return

        name = name.strip()
        if name in self._recipes:
            confirm = QMessageBox.question(
                self,
                "Overwrite?",
                f'"{name}" already exists ({self._recipes[name]}). Overwrite?',
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        self._recipes[name] = ratio_text
        _save_recipes(self._recipes)
        self._refresh_combo()

        for i in range(self.recipe_combo.count()):
            if self.recipe_combo.itemData(i) == name:
                self.recipe_combo.setCurrentIndex(i)
                break

    # ── Calculation ───────────────────────────────────────────────────

    def _calculate(self):
        ratio = _parse_ratio(self.ratio_input.text()) if self.ratio_input.text().strip() else None
        coffee = _parse_positive(self.coffee_input.text()) if self.coffee_input.text().strip() else None
        water = _parse_positive(self.water_input.text()) if self.water_input.text().strip() else None

        r_html, c_html, w_html = _compute_hints(ratio, coffee, water)
        self.ratio_info.setText(r_html)
        self.coffee_info.setText(c_html)
        self.water_info.setText(w_html)


def main():
    app = QApplication(sys.argv)
    window = CoffeeCalculator()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
