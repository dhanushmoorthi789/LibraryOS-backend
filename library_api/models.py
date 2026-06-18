from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    ROLE_CHOICES = [('admin', 'Admin'), ('staff', 'Staff'), ('user', 'User')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    total_quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    published_year = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def is_available(self):
        return self.available_quantity > 0


class Fine(models.Model):
    amount_per_day = models.DecimalField(max_digits=8, decimal_places=2, default=5.00)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Fine: ₹{self.amount_per_day}/day"

    class Meta:
        verbose_name = "Fine Setting"


class BorrowRecord(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_records')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_records')
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='borrowed')
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.due_date = timezone.now().date() + timedelta(days=10)
        super().save(*args, **kwargs)

    def calculate_fine(self):
        if self.status == 'returned' and self.return_date:
            if self.return_date > self.due_date:
                overdue_days = (self.return_date - self.due_date).days
                fine_setting = Fine.objects.last()
                rate = fine_setting.amount_per_day if fine_setting else 5
                return overdue_days * rate
        elif self.status in ['borrowed', 'overdue']:
            today = timezone.now().date()
            if today > self.due_date:
                overdue_days = (today - self.due_date).days
                fine_setting = Fine.objects.last()
                rate = fine_setting.amount_per_day if fine_setting else 5
                return overdue_days * rate
        return 0

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.status})"
