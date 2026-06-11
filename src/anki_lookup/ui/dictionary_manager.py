"""Native dictionary management dialog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..dictionary import DictionaryInfo, ImportResult
from ..runtime import dictionary_service


class DictionaryManager:
    """Own a Qt dialog without importing Qt outside Anki."""

    def __init__(self, parent: Any) -> None:
        from aqt.qt import (
            QAbstractItemView,
            QDialog,
            QDialogButtonBox,
            QFileDialog,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QListWidgetItem,
            QPushButton,
            Qt,
            QVBoxLayout,
        )

        self._qt = {
            "QFileDialog": QFileDialog,
            "QListWidgetItem": QListWidgetItem,
            "Qt": Qt,
        }
        self._updating = False
        self.dialog = QDialog(parent)
        self.dialog.setWindowTitle("Anki Lookup Dictionaries")
        self.dialog.resize(720, 460)

        layout = QVBoxLayout(self.dialog)
        description = QLabel(
            "Import Yomitan format-3 term dictionaries. Dictionary files stay "
            "on this computer and are indexed in Anki Lookup's user data."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.itemChanged.connect(self._on_item_changed)
        self.list_widget.itemSelectionChanged.connect(self._update_buttons)
        layout.addWidget(self.list_widget, 1)

        action_layout = QHBoxLayout()
        self.import_button = QPushButton("Import...")
        self.remove_button = QPushButton("Remove")
        self.up_button = QPushButton("Move Up")
        self.down_button = QPushButton("Move Down")
        action_layout.addWidget(self.import_button)
        action_layout.addWidget(self.remove_button)
        action_layout.addStretch(1)
        action_layout.addWidget(self.up_button)
        action_layout.addWidget(self.down_button)
        layout.addLayout(action_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.dialog.reject)
        layout.addWidget(buttons)

        self.import_button.clicked.connect(self._choose_import)
        self.remove_button.clicked.connect(self._remove_selected)
        self.up_button.clicked.connect(lambda: self._move_selected(-1))
        self.down_button.clicked.connect(lambda: self._move_selected(1))
        self.refresh()

    def show(self) -> None:
        self.dialog.exec()

    def refresh(self, select_id: int | None = None) -> None:
        dictionaries = dictionary_service().list_dictionaries()
        Qt = self._qt["Qt"]
        QListWidgetItem = self._qt["QListWidgetItem"]

        self._updating = True
        try:
            self.list_widget.clear()
            for dictionary in dictionaries:
                item = QListWidgetItem(_dictionary_label(dictionary))
                item.setData(Qt.ItemDataRole.UserRole, dictionary.id)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.CheckState.Checked if dictionary.enabled else Qt.CheckState.Unchecked
                )
                item.setToolTip(
                    f"Revision: {dictionary.revision}\n"
                    f"Format: {dictionary.format}\n"
                    f"Terms: {dictionary.term_count:,}"
                )
                self.list_widget.addItem(item)
                if dictionary.id == select_id:
                    self.list_widget.setCurrentItem(item)
        finally:
            self._updating = False
        self._update_buttons()

    def _choose_import(self) -> None:
        QFileDialog = self._qt["QFileDialog"]
        filename, _ = QFileDialog.getOpenFileName(
            self.dialog,
            "Import Yomitan Dictionary",
            "",
            "Yomitan dictionaries (*.zip);;ZIP archives (*.zip)",
        )
        if not filename:
            return

        from aqt import mw
        from aqt.operations import QueryOp
        from aqt.utils import showWarning

        self._set_busy(True)
        (
            QueryOp(
                parent=self.dialog,
                op=lambda _collection: dictionary_service().import_archive(
                    Path(filename),
                    should_cancel=lambda: bool(mw and mw.progress.want_cancel()),
                ),
                success=self._import_succeeded,
            )
            .without_collection()
            .with_progress("Importing dictionary...")
            .failure(lambda error: self._operation_failed(error, showWarning))
            .run_in_background()
        )

    def _import_succeeded(self, result: ImportResult) -> None:
        from aqt.utils import tooltip

        self._set_busy(False)
        self.refresh(result.dictionary.id)
        tooltip(
            f"Imported {result.dictionary.title}: "
            f"{result.dictionary.term_count:,} terms in "
            f"{result.elapsed_seconds:.1f} seconds.",
            parent=self.dialog,
        )

    def _remove_selected(self) -> None:
        dictionary_id = self._selected_id()
        if dictionary_id is None:
            return

        from aqt.operations import QueryOp
        from aqt.utils import askUser, showWarning

        item = self.list_widget.currentItem()
        if item is None or not askUser(
            f"Remove {item.text()} and its local index?", parent=self.dialog
        ):
            return

        self._set_busy(True)
        (
            QueryOp(
                parent=self.dialog,
                op=lambda _collection: dictionary_service().remove(dictionary_id),
                success=lambda _result: self._remove_succeeded(),
            )
            .without_collection()
            .with_progress("Removing dictionary...")
            .failure(lambda error: self._operation_failed(error, showWarning))
            .run_in_background()
        )

    def _remove_succeeded(self) -> None:
        self._set_busy(False)
        self.refresh()

    def _on_item_changed(self, item: Any) -> None:
        if self._updating:
            return
        Qt = self._qt["Qt"]
        dictionary_id = item.data(Qt.ItemDataRole.UserRole)
        enabled = item.checkState() == Qt.CheckState.Checked
        try:
            dictionary_service().set_enabled(int(dictionary_id), enabled)
        except Exception as error:
            from aqt.utils import showWarning

            showWarning(f"Could not update dictionary: {error}", parent=self.dialog)
            self.refresh(int(dictionary_id))

    def _move_selected(self, offset: int) -> None:
        dictionary_id = self._selected_id()
        if dictionary_id is None:
            return
        try:
            dictionary_service().move(dictionary_id, offset)
        except Exception as error:
            from aqt.utils import showWarning

            showWarning(f"Could not reorder dictionary: {error}", parent=self.dialog)
            return
        self.refresh(dictionary_id)

    def _selected_id(self) -> int | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        Qt = self._qt["Qt"]
        return int(item.data(Qt.ItemDataRole.UserRole))

    def _update_buttons(self) -> None:
        row = self.list_widget.currentRow()
        count = self.list_widget.count()
        has_selection = row >= 0
        self.remove_button.setEnabled(has_selection)
        self.up_button.setEnabled(has_selection and row > 0)
        self.down_button.setEnabled(has_selection and row < count - 1)

    def _set_busy(self, busy: bool) -> None:
        self.import_button.setEnabled(not busy)
        self.remove_button.setEnabled(not busy and self._selected_id() is not None)
        self.up_button.setEnabled(not busy)
        self.down_button.setEnabled(not busy)

    def _operation_failed(self, error: Exception, show_warning: Any) -> None:
        self._set_busy(False)
        show_warning(str(error), parent=self.dialog)


def show_dictionary_manager(parent: Any) -> None:
    DictionaryManager(parent).show()


def _dictionary_label(dictionary: DictionaryInfo) -> str:
    return f"{dictionary.title} - {dictionary.term_count:,} terms"
