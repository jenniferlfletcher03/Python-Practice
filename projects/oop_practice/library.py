"""Library program — OOP practice.

A simple two-class model:
- Book:    a single book, knows who (if anyone) has it checked out.
- Library: holds books and members, handles checkout/return.

Run with `python3 library.py` to see the demo scenario at the bottom.
"""


class Book:
    def __init__(self, title, author, isbn):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.check_out_by = None  # None == available; otherwise a member_id


class Library:
    def __init__(self):
        self.books = {}       # isbn -> Book
        self.members = set()  # member_ids

    def add_book(self, title, author, isbn):
        if isbn in self.books:
            return False
        self.books[isbn] = Book(title, author, isbn)
        return True

    def add_member(self, member_id):
        if member_id in self.members:
            return False
        self.members.add(member_id)
        return True

    def checkout(self, isbn, member_id):
        if isbn not in self.books:
            return False
        if member_id not in self.members:
            return False
        book = self.books[isbn]
        if book.check_out_by is not None:
            return False
        book.check_out_by = member_id
        return True

    def return_book(self, isbn):
        if isbn not in self.books:
            return False
        book = self.books[isbn]
        if book.check_out_by is None:
            return False
        book.check_out_by = None
        return True


if __name__ == "__main__":
    lib = Library()
    lib.add_book("Dune", "Frank Herbert", "9780441013593")
    lib.add_member("m1")

    print("checkout :", lib.checkout("9780441013593", "m1"))
    print("holder   :", lib.books["9780441013593"].check_out_by)
    print("return   :", lib.return_book("9780441013593"))
    print("holder   :", lib.books["9780441013593"].check_out_by)
