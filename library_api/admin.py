from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Book, Category, BorrowRecord, Fine


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
    list_filter   = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Library Role', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Library Role', {'fields': ('role', 'phone', 'email')}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['id', 'name', 'description']
    search_fields = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display  = ['id', 'title', 'author', 'isbn', 'category', 'total_quantity', 'available_quantity', 'created_at']
    list_filter   = ['category']
    search_fields = ['title', 'author', 'isbn']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display  = ['id', 'user', 'book', 'borrow_date', 'due_date', 'return_date', 'status', 'fine_amount']
    list_filter   = ['status']
    search_fields = ['user__username', 'book__title']
    readonly_fields = ['borrow_date', 'created_at']


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ['id', 'amount_per_day', 'updated_by', 'updated_at']
