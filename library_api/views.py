from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.db import transaction
from .models import User, Book, Category, BorrowRecord, Fine
from .serializers import (RegisterSerializer, LoginSerializer, UserSerializer,
                           BookSerializer, CategorySerializer, BorrowRecordSerializer, FineSerializer)


class IsAdminOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'staff']


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'message': 'Logged out successfully'})


@api_view(['GET'])
def me(request):
    return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrStaff()]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related('category').all().order_by('-created_at')
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        available = self.request.query_params.get('available')
        if search:
            qs = qs.filter(title__icontains=search) | qs.filter(author__icontains=search)
        if category:
            qs = qs.filter(category_id=category)
        if available == 'true':
            qs = qs.filter(available_quantity__gt=0)
        return qs


class BorrowRecordViewSet(viewsets.ModelViewSet):
    queryset = BorrowRecord.objects.select_related('user', 'book').all().order_by('-created_at')
    serializer_class = BorrowRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'user':
            qs = qs.filter(user=user)
        status_filter = self.request.query_params.get('status')
        user_filter = self.request.query_params.get('user_id')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if user_filter and user.role in ['admin', 'staff']:
            qs = qs.filter(user_id=user_filter)
        return qs

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        book_id = request.data.get('book')
        try:
            book = Book.objects.select_for_update().get(pk=book_id)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)

        if book.available_quantity <= 0:
            return Response({'error': 'Book is not available'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already has this book
        existing = BorrowRecord.objects.filter(
            user=request.user, book=book, status__in=['borrowed', 'overdue']
        ).exists()
        if existing:
            return Response({'error': 'You already have this book borrowed'}, status=status.HTTP_400_BAD_REQUEST)

        record = BorrowRecord.objects.create(user=request.user, book=book)
        book.available_quantity -= 1
        book.save()
        return Response(BorrowRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def return_book(self, request, pk=None):
        record = self.get_object()
        if record.status == 'returned':
            return Response({'error': 'Book already returned'}, status=status.HTTP_400_BAD_REQUEST)

        record.return_date = timezone.now().date()
        record.status = 'returned'
        fine = record.calculate_fine()
        record.fine_amount = fine
        record.save()

        book = Book.objects.select_for_update().get(pk=record.book.pk)
        book.available_quantity += 1
        book.save()

        return Response(BorrowRecordSerializer(record).data)

    @action(detail=False, methods=['get'])
    def my_books(self, request):
        records = BorrowRecord.objects.filter(
            user=request.user, status__in=['borrowed', 'overdue']
        ).select_related('book')
        return Response(BorrowRecordSerializer(records, many=True).data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        if request.user.role not in ['admin', 'staff']:
            return Response({'error': 'Forbidden'}, status=403)
        today = timezone.now().date()
        records = BorrowRecord.objects.filter(
            status='borrowed', due_date__lt=today
        ).select_related('user', 'book')
        # Update status
        records.update(status='overdue')
        return Response(BorrowRecordSerializer(records, many=True).data)


class FineViewSet(viewsets.ModelViewSet):
    queryset = Fine.objects.all()
    serializer_class = FineSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)
