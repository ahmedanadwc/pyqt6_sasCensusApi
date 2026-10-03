"""Qt worker for non-blocking SAS operations."""

from PyQt6.QtCore import QObject, pyqtSignal


class SasWorker(QObject):
    """Worker that runs a callable in a separate thread."""

    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, callable_func, *args, **kwargs):
        super().__init__()
        self._callable = callable_func
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._callable(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
