from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Book, Category, BorrowRecord, Fine


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'phone', 'role']
        extra_kwargs = {'role': {'default': 'user'}}

    def create(self, validated_data):
        # Only admins can create admin/staff; default role is 'user'
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled")
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'category', 'category_name',
                  'total_quantity', 'available_quantity', 'published_year',
                  'description', 'cover_image', 'is_available', 'created_at']


class BorrowRecordSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)
    current_fine = serializers.SerializerMethodField()

    class Meta:
        model = BorrowRecord
        fields = ['id', 'user', 'user_name', 'user_email', 'book', 'book_title',
                  'book_author', 'borrow_date', 'due_date', 'return_date',
                  'status', 'fine_amount', 'fine_paid', 'current_fine', 'created_at']
        read_only_fields = ['id', 'borrow_date', 'due_date', 'created_at']

    def get_current_fine(self, obj):
        return float(obj.calculate_fine())


class FineSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = Fine
        fields = ['id', 'amount_per_day', 'updated_at', 'updated_by', 'updated_by_name']
        read_only_fields = ['id', 'updated_at', 'updated_by']
