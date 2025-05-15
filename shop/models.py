from django.db import models
from django.contrib.auth.models import User
import datetime

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('PC', 'PC'),
        ('Laptop', 'Laptop'),
        ('Laptop Gaming', 'Laptop Gaming'),
        ('Laptop office', 'Laptop Văn Phòng'),
        ('phụ kiện máy tính', 'Phụ kiện máy tính'),
    ]
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)
    colors = models.CharField(max_length=200, blank=True, help_text="Các màu sắc, phân cách bằng dấu phẩy")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0, 
                               help_text="Đánh giá trung bình (0.0-5.0)")
    rating_count = models.IntegerField(default=0, help_text="Số lượng đánh giá")

    def __str__(self):
        return self.name
    
    def color_list(self):
        """Trả về danh sách các màu sắc dưới dạng list"""
        if not self.colors:
            return []
        return [color.strip() for color in self.colors.split(',')]

class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    rating = models.IntegerField(default=5, help_text="Đánh giá từ 1-5 sao")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Bình luận bởi {self.user.username} cho {self.product.name}"

# Model đơn hàng
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Chờ xác nhận'),
        ('processing', 'Đang xử lý'),
        ('shipped', 'Đang giao hàng'),
        ('delivered', 'Đã giao hàng'),
        ('cancelled', 'Đã hủy'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f'Đơn hàng #{self.id} - {self.user.username}'
    
    @property
    def get_status_display_vi(self):
        status_map = dict(self.STATUS_CHOICES)
        return status_map.get(self.status, self.status)

# Chi tiết đơn hàng
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)  # Lưu tên sản phẩm để phòng trường hợp sản phẩm bị xóa
    product_price = models.DecimalField(max_digits=10, decimal_places=2)  # Lưu giá sản phẩm tại thời điểm mua
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f'{self.quantity} x {self.product_name}'
    
    @property
    def get_total(self):
        return self.product_price * self.quantity
