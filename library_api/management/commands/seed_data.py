from django.core.management.base import BaseCommand
from library_api.models import User, Book, Category, Fine


class Command(BaseCommand):
    help = 'Seed initial data'

    def handle(self, *args, **options):
        # Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin', email='admin@library.com',
                password='admin123', role='admin',
                first_name='Admin', last_name='User'
            )
            self.stdout.write('Created admin user')

        # Staff
        if not User.objects.filter(username='staff1').exists():
            User.objects.create_user(
                username='staff1', email='staff@library.com',
                password='staff123', role='staff',
                first_name='John', last_name='Staff'
            )

        # Regular user
        if not User.objects.filter(username='user1').exists():
            User.objects.create_user(
                username='user1', email='user@library.com',
                password='user123', role='user',
                first_name='Alice', last_name='Reader'
            )

        # Categories
        cats = ['Fiction', 'Non-Fiction', 'Science', 'History', 'Technology', 'Biography']
        cat_objs = {}
        for c in cats:
            obj, _ = Category.objects.get_or_create(name=c)
            cat_objs[c] = obj

        # Books
        books_data = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 'Fiction', 5, 1925),
            ('Sapiens', 'Yuval Noah Harari', '9780062316097', 'Non-Fiction', 3, 2011),
            ('A Brief History of Time', 'Stephen Hawking', '9780553380163', 'Science', 4, 1988),
            ('Clean Code', 'Robert C. Martin', '9780132350884', 'Technology', 6, 2008),
            ('1984', 'George Orwell', '9780451524935', 'Fiction', 5, 1949),
            ('The Selfish Gene', 'Richard Dawkins', '9780198788607', 'Science', 3, 1976),
            ('Steve Jobs', 'Walter Isaacson', '9781451648539', 'Biography', 4, 2011),
            ('Guns, Germs, and Steel', 'Jared Diamond', '9780393317558', 'History', 2, 1997),
            ('Python Crash Course', 'Eric Matthes', '9781593279288', 'Technology', 8, 2015),
            ('To Kill a Mockingbird', 'Harper Lee', '9780061935466', 'Fiction', 4, 1960),
        ]

        for title, author, isbn, cat, qty, year in books_data:
            Book.objects.get_or_create(
                isbn=isbn,
                defaults={
                    'title': title, 'author': author,
                    'category': cat_objs[cat],
                    'total_quantity': qty,
                    'available_quantity': qty,
                    'published_year': year,
                }
            )

        # Fine setting
        if not Fine.objects.exists():
            admin = User.objects.get(username='admin')
            Fine.objects.create(amount_per_day=5.00, updated_by=admin)

        self.stdout.write(self.style.SUCCESS('✅ Seed data created successfully!'))
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Staff: staff1 / staff123')
        self.stdout.write('User: user1 / user123')
