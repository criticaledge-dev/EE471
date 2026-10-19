class MediaItem:
    """A media item with a title, author, and availability status."""
    def __init__(self, title, author, is_available=True):
        self.title = title
        self.author = author
        self.is_available = is_available

    def checkout(self):
        """Mark the item as checked out if available, otherwise indicate it's already out."""
        if self.is_available:
            self.is_available = False
            return "Successful checkout"
        return "Already out"

    def return_item(self):
        """Mark the item as available if it was checked out, otherwise indicate it's already in."""
        self.is_available = True

    def __str__(self):
        """Return a string representation of the media item."""
        status = "Available" if self.is_available else "Checked Out"
        return f"{self.title} by {self.author} [{status}]"


class Book(MediaItem):
    """A book media item with a page count."""
    def __init__(self, title, author, page_count, is_available=True):
        super().__init__(title, author, is_available)
        self.page_count = page_count

    def __str__(self):
        return f"{super().__str__()} - {self.page_count} pages"


class DVD(MediaItem):
    """A DVD media item with a duration in minutes."""
    def __init__(self, title, author, duration, is_available=True):
        super().__init__(title, author, is_available)
        self.duration = duration

    def checkout(self):
        """Override the checkout method to add a message about handling DVDs with care."""
        result = super().checkout()
        if result == "Successful checkout":
            print("Handle with care: Do not scratch the disc.")
        return result


class LibraryCollection:
    """Store library items and list available titles."""
    def __init__(self):
        self.items = []

    def add_item(self, item):
        """Add a MediaItem to the collection."""
        self.items.append(item)

    def list_available(self):
        """Return available item titles in insertion order."""
        return [item.title for item in self.items if item.is_available]
