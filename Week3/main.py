from custom_classes import Book, DVD, LibraryCollection


def main():
    """Demonstrate the functionality of the MediaItem, Book, DVD, and LibraryCollection classes."""
    collection = LibraryCollection()
    print("Available titles in the empty library:")
    print(collection.list_available())

    book = Book("The Hobbit", "J.R.R. Tolkien", page_count=310)
    dvd = DVD("Inception", "Christopher Nolan", duration=148)
    second_book = Book("1984", "George Orwell", page_count=328)

    print(f"\nAdding: {book.title}")
    collection.add_item(book)
    print(collection.list_available())
    print(f"\nAdding: {dvd.title}")
    collection.add_item(dvd)
    print(collection.list_available())
    print(f"\nAdding: {second_book.title}")
    collection.add_item(second_book)
    print(collection.list_available())

    print("\nInitial library items:")
    print(book)
    print(dvd)
    print(second_book)

    print("\nChecking out the book:")
    print(book.checkout())

    print("\nChecking out the DVD:")
    print(dvd.checkout())

    print("\nFinal library items:")
    print(book)
    print(dvd)
    print(second_book)

    print("\nAvailable titles after checking out two items:")
    print(collection.list_available())


if __name__ == "__main__":
    main()
