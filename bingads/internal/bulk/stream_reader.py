from bingads.bulk import DownloadFileType
from .bulk_object import _BulkObject
from ..error_messages import _ErrorMessages
from .format_version import _FormatVersion
from .object_reader import _BulkObjectReader


class _BulkStreamReader():
    """ Reads a bulk object and also its related data (for example corresponding errors) from the stream."""

    __SUPPORTED_VERSIONS = ["3", "3.0"]

    def __init__(self, file_path, file_format, encoding=None):
        self._file_path = file_path
        self._file_format = file_format
        self._encoding = encoding

        self._delimiter = ',' if self.file_format == DownloadFileType.csv else '\t'
        self._passed_first_row = False
        self._bulk_object_reader = _BulkObjectReader(self.file_path, self.delimiter)
        self._bulk_object_reader.__enter__()
        self._next_object = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._bulk_object_reader.__exit__(exc_type, exc_val, exc_tb)

    def __iter__(self):
        return self

    def __next__(self):
        return self.read()

    def close(self):
        self.__exit__(None, None, None)

    def next(self):
        return self.__next__()

    def read(self):
        """ Returns the next object from the file

        :return: next object
        :rtype: :class:`._BulkObject`
        """

        _, bulk_object = self.try_read(_BulkObject)
        return bulk_object

    def try_read(self, return_type, predicate=lambda x: True):
        """ Reads the object only if it has a certain type

        :param return_type: The type of object that should be returned
        :type return_type: class
        :param predicate: A test that should be run against the object
        :type predicate: function accepting on argument of the BulkObject
        :return: an object of the type specified
        :rtype: (bool, _BulkObject)
        """
        peeked = self._peek()
        if peeked is not None and isinstance(peeked, return_type) and predicate(peeked):
            self._next_object = None
            peeked.read_related_data_from_stream(self)
            return True, peeked
        return False, None

    def _peek(self):
        if not self._passed_first_row:
            first_row_object = self._bulk_object_reader.read_next_bulk_object()
            if isinstance(first_row_object, _FormatVersion):
                if first_row_object.value not in _BulkStreamReader.__SUPPORTED_VERSIONS:
                    raise NotImplementedError(
                        _ErrorMessages.get_format_version_not_supported_message(str(first_row_object.value)))
            else:
                self._next_object = first_row_object
            self._passed_first_row = True
        if self._next_object is not None:
            return self._next_object
        self._next_object = self._bulk_object_reader.read_next_bulk_object()
        return self._next_object

    @property
    def file_path(self):
        return self._file_path

    @property
    def file_format(self):
        return self._file_format

    @property
    def delimiter(self):
        return self._delimiter

    @property
    def encoding(self):
        return self._encoding
