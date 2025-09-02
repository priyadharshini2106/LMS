# Fully coded views.py for library
print('library views.py loaded')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Book, BookIssue
from .forms import BookForm, BookIssueForm


def library_dashboard(request):
    return render(request, 'library/library_dashboard.html')

# ✅ BOOK VIEWS
@login_required
def book_list(request):
    books = Book.objects.all()
    return render(request, 'library/book_list.html', {'books': books})


@login_required
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Book added successfully.")
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form, 'title': 'Add Book'})


@login_required
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Book updated successfully.")
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'library/book_form.html', {'form': form, 'title': 'Edit Book'})


# ✅ BOOK ISSUE VIEWS
@login_required
def issue_list(request):
    issues = BookIssue.objects.select_related('book', 'student').all()
    return render(request, 'library/issue_list.html', {'issues': issues})


@login_required
def issue_book(request):
    if request.method == 'POST':
        form = BookIssueForm(request.POST)
        if form.is_valid():
            book = form.cleaned_data['book']
            if book.available_copies > 0:
                book.available_copies -= 1
                book.save()
                form.save()
                messages.success(request, "Book issued successfully.")
                return redirect('issue_list')
            else:
                messages.error(request, "No available copies of this book.")
    else:
        form = BookIssueForm()
    return render(request, 'library/issue_form.html', {'form': form, 'title': 'Issue Book'})


@login_required
def return_book(request, pk):
    issue = get_object_or_404(BookIssue, pk=pk)
    if not issue.return_date:
        issue.return_date = request.POST.get('return_date') or None
        if issue.return_date:
            issue.book.available_copies += 1
            issue.book.save()
            issue.save()
            messages.success(request, "Book returned successfully.")
        else:
            messages.error(request, "Return date is required.")
    return redirect('issue_list')
