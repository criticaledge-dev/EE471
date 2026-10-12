from custom_classes import MediaItem


def main():
    book = MediaItem("The Hobbit", "J.R.R. Tolkien")
    movie = MediaItem("Inception", "Christopher Nolan")

    print("Initial library items:")
    print(book)
    print(movie)

    print("\nChecking out the book:")
    print(book.checkout())

    print("\nFinal library items:")
    print(book)
    print(movie)


if __name__ == "__main__":
    main()
