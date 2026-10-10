"""Qt worker for non-blocking SAS operations."""

import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class SasWorker(QObject):
    """Worker that runs a callable in a separate thread."""

    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, callable_func, *args, **kwargs):
        super().__init__()
        self._callable = callable_func
        self._args = args
        self._kwargs = kwargs

    @pyqtSlot()
    def run(self) -> None:
        try:
            result = self._callable(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as exc:
            logger.exception("SAS worker operation failed")
            self.failed.emit(str(exc))
