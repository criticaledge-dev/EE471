"""Validated media models and an in-memory library collection."""


class ItemNotFoundError(LookupError):
    """Raised when an item ID is absent from the collection."""


class ItemStateError(Exception):
    """Raised when an operation conflicts with an item's current state."""


def _validate_text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Title and author must be non-empty text.")
    return value


def _validate_positive_integer(value):
    if type(value) is not int or value <= 0:
        raise ValueError("Page count and duration must be positive integers.")
    return value


class MediaItem:
    """A validated media item with a collection-assigned, read-only ID."""

    _item_type = "media"
    _field_validators = {"title": _validate_text, "author": _validate_text}

    def __init__(self, title, author, is_available=True):
        """Create an item without assigning a collection ID yet."""
        self._id = None
        self.title = title
        self.author = author
        self.is_available = is_available

    @property
    def id(self):
        """Return the assigned ID, or None before the first addition."""
        return self._id

    @property
    def title(self):
        """Return the non-empty title."""
        return self._title

    @title.setter
    def title(self, value):
        """Validate and assign the title."""
        self._title = _validate_text(value)

    @property
    def author(self):
        """Return the non-empty author."""
        return self._author

    @author.setter
    def author(self, value):
        """Validate and assign the author."""
        self._author = _validate_text(value)

    @property
    def is_available(self):
        """Return whether the item is available for checkout."""
        return self._is_available

    @is_available.setter
    def is_available(self, value):
        """Accept only a boolean availability state."""
        if type(value) is not bool:
            raise ValueError("Availability must be a boolean.")
        self._is_available = value

    def to_dict(self):
        """Return the common serializable item fields."""
        return {
            "id": self.id,
            "type": self._item_type,
            "title": self.title,
            "author": self.author,
            "is_available": self.is_available,
        }

    def checkout(self):
        """Check out an available item or raise ItemStateError."""
        if not self.is_available:
            raise ItemStateError("Item is already checked out.")
        self.is_available = False
        return "Successful checkout"

    def return_item(self):
        """Return a checked-out item or raise ItemStateError."""
        if self.is_available:
            raise ItemStateError("Item is already available.")
        self.is_available = True
        return "Successful return"

    def __str__(self):
        """Describe the title, author and current availability."""
        status = "Available" if self.is_available else "Checked Out"
        return f"{self.title} by {self.author} [{status}]"


class Book(MediaItem):
    """A media item with a positive integer page count."""

    _item_type = "book"
    _field_validators = {**MediaItem._field_validators, "page_count": _validate_positive_integer}

    def __init__(self, title, author, page_count, is_available=True):
        """Create a book and validate its common and book-specific fields."""
        super().__init__(title, author, is_available)
        self.page_count = page_count

    @property
    def page_count(self):
        """Return the positive page count."""
        return self._page_count

    @page_count.setter
    def page_count(self, value):
        """Validate and assign the page count."""
        self._page_count = _validate_positive_integer(value)

    def to_dict(self):
        """Extend the common fields with the page count."""
        return {**super().to_dict(), "page_count": self.page_count}

    def __str__(self):
        """Describe the book and its page count."""
        return f"{super().__str__()} - {self.page_count} pages"


class DVD(MediaItem):
    """A media item with a positive integer duration in minutes."""

    _item_type = "dvd"
    _field_validators = {**MediaItem._field_validators, "duration": _validate_positive_integer}

    def __init__(self, title, author, duration, is_available=True):
        """Create a DVD and validate its common and DVD-specific fields."""
        super().__init__(title, author, is_available)
        self.duration = duration

    @property
    def duration(self):
        """Return the positive duration in minutes."""
        return self._duration

    @duration.setter
    def duration(self, value):
        """Validate and assign the duration."""
        self._duration = _validate_positive_integer(value)

    def to_dict(self):
        """Extend the common fields with the DVD duration."""
        return {**super().to_dict(), "duration": self.duration}

    def checkout(self):
        """Use the base checkout and append the disc-care warning."""
        return f"{super().checkout()}. Handle with care: Do not scratch the disc."


class LibraryCollection:
    """Store items in insertion order with IDs never reused by this collection."""

    def __init__(self):
        """Start an empty collection whose first assigned ID will be 1."""
        self.items = []
        self._next_id = 1

    def add_item(self, item):
        """Assign and return a new ID; reject items already assigned an ID."""
        if not isinstance(item, MediaItem):
            raise ValueError("Only MediaItem instances can be added.")
        if item.id is not None:
            raise ItemStateError("Item has already been assigned an ID.")
        item._id = self._next_id
        self._next_id += 1
        self.items.append(item)
        return item.id

    def get_item(self, item_id):
        """Find an integer ID or raise ItemNotFoundError."""
        if type(item_id) is int:
            for item in self.items:
                if item.id == item_id:
                    return item
        raise ItemNotFoundError(f"Item not found: {item_id!r}")

    def create_item(self, fields):
        """Validate a complete book/DVD description, add it and return the item."""
        if not isinstance(fields, dict):
            raise ValueError("Item fields must be an object.")
        item_type = fields.get("type")
        models = {"book": Book, "dvd": DVD}
        if not isinstance(item_type, str) or item_type not in models:
            raise ValueError("type must be 'book' or 'dvd'.")
        model = models[item_type]
        required = set(model._field_validators)
        self._require_fields(fields, required | {"type"})
        item = model(**{field: fields[field] for field in required})
        self.add_item(item)
        return item

    def list_items(self, available=None, item_type=None):
        """Return items matching both optional, strictly validated filters."""
        if available is not None and type(available) is not bool:
            raise ValueError("available must be None, True or False.")
        if item_type is not None and (
            not isinstance(item_type, str) or item_type not in ("book", "dvd")
        ):
            raise ValueError("item_type must be None, 'book' or 'dvd'.")
        return [
            item for item in self.items
            if (available is None or item.is_available is available)
            and (item_type is None or item._item_type == item_type)
        ]

    def list_available(self):
        """Return available item titles in insertion order."""
        return [item.title for item in self.list_items(available=True)]

    def update_item(self, item_id, **fields):
        """Validate every requested field before updating and returning the item."""
        item = self.get_item(item_id)
        return self._apply_update(item, fields)

    def replace_item(self, item_id, fields):
        """Require every editable field and atomically update an existing item."""
        item = self.get_item(item_id)
        self._require_fields(fields, set(item._field_validators))
        return self._apply_update(item, fields)

    def patch_item(self, item_id, fields):
        """Atomically apply at least one editable field to an existing item."""
        item = self.get_item(item_id)
        if not isinstance(fields, dict) or not fields:
            raise ValueError("At least one editable field is required.")
        return self._apply_update(item, fields)

    @staticmethod
    def _require_fields(fields, required):
        if not isinstance(fields, dict) or set(fields) != required:
            raise ValueError("Exactly these fields are required: " + ", ".join(sorted(required)))

    @staticmethod
    def _apply_update(item, fields):
        validators = item._field_validators
        for field, value in fields.items():
            if field not in validators:
                raise ValueError(f"Field cannot be updated for this item: {field}")
            validators[field](value)
        for field, value in fields.items():
            setattr(item, field, value)
        return item

    def remove_item(self, item_id):
        """Remove an available item, rejecting absent or checked-out items."""
        item = self.get_item(item_id)
        if not item.is_available:
            raise ItemStateError("Cannot remove a checked-out item.")
        self.items.remove(item)
