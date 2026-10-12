from custom_classes import Book, DVD


def main():
    book = Book("The Hobbit", "J.R.R. Tolkien", page_count=310)
    dvd = DVD("Inception", "Christopher Nolan", duration=148)

    print("Initial library items:")
    print(book)
    print(dvd)

    print("\nChecking out the DVD:")
    print(dvd.checkout())

    print("\nFinal library items:")
    print(book)
    print(dvd)

    print("\nTrying to check out the DVD again:")
    print(dvd.checkout())


if __name__ == "__main__":
    main()
