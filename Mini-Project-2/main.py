"""Console demonstration for Week 4 Section 2 Part 2."""

from custom_classes import (
    Book, DVD, ItemNotFoundError, ItemStateError, LibraryCollection,
)


def main():
    """Demonstrate IDs, serialization, filters, updates and expected errors."""
    collection = LibraryCollection()
    book = Book("The Hobbit", "J.R.R. Tolkien", 310)
    dvd = DVD("Inception", "Christopher Nolan", 148)
    second_book = Book("1984", "George Orwell", 328)

    print("Adding mixed media and returned IDs:")
    book_id = collection.add_item(book)
    dvd_id = collection.add_item(dvd)
    second_book_id = collection.add_item(second_book)
    print(f"Book ID: {book_id}; DVD ID: {dvd_id}; second book ID: {second_book_id}")

    print("\nto_dict() and __str__():")
    for item in collection.list_items():
        print(item.to_dict())
        print(str(item))

    print("\nFind by ID:", collection.get_item(dvd_id))
    print("Available titles:", collection.list_available())
    print("All items:", [item.to_dict() for item in collection.list_items()])
    print("Books:", [item.title for item in collection.list_items(item_type="book")])

    print("\nEditing book and DVD:")
    print(collection.update_item(book_id, title="The Hobbit (revised)", page_count=320))
    print(collection.update_item(dvd_id, author="C. Nolan", duration=150).to_dict())

    print("\nCheckout book:", book.checkout())
    dvd_message = dvd.checkout()
    print("DVD checkout returned message:", dvd_message)
    print("DVD warning is in returned message:", "Handle with care" in dvd_message)
    print("Available items:", [item.title for item in collection.list_items(available=True)])
    print("Checked-out items:", [item.title for item in collection.list_items(available=False)])
    print("Checked-out DVDs:", [
        item.title for item in collection.list_items(available=False, item_type="dvd")
    ])
    print("Available titles after checkout:", collection.list_available())

    print("\nExpected errors:")
    try:
        collection.get_item(999)
    except ItemNotFoundError as error:
        print("ItemNotFoundError:", error)
    try:
        book.checkout()
    except ItemStateError as error:
        print("ItemStateError (checkout):", error)
    try:
        collection.remove_item(dvd_id)
    except ItemStateError as error:
        print("ItemStateError (remove):", error)
    try:
        collection.add_item(book)
    except ItemStateError as error:
        print("ItemStateError (duplicate object):", error)

    before = book.to_dict()
    try:
        collection.update_item(book_id, title="Must not be applied", page_count=True)
    except ValueError as error:
        print("ValueError (invalid update):", error)
    print("Failed update left item unchanged:", before == book.to_dict())
    try:
        collection.list_items(available=1)
    except ValueError as error:
        print("ValueError (invalid filter):", error)

    print("\nReturn book:", book.return_item())
    print("Return DVD:", dvd.return_item())
    try:
        dvd.return_item()
    except ItemStateError as error:
        print("ItemStateError (return):", error)

    collection.remove_item(second_book_id)
    print(f"\nRemoved item ID: {second_book_id}")
    try:
        collection.get_item(second_book_id)
    except ItemNotFoundError as error:
        print("ItemNotFoundError (removed ID):", error)
    new_id = collection.add_item(DVD("Spirited Away", "Hayao Miyazaki", 125))
    print(f"New item ID: {new_id}; removed ID was not reused: {new_id > second_book_id}")
    print("Final available titles:", collection.list_available())


if __name__ == "__main__":
    main()
