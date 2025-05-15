from django.contrib import admin
from .models import Product, Order, OrderItem

# admin.site.register(Category)
admin.site.register(Product)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'product_price', 'quantity']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'phone', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['full_name', 'email', 'phone']
    readonly_fields = ['user', 'full_name', 'email', 'phone', 'address', 'city', 'total_amount', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    list_editable = ['status']
    list_per_page = 20
    
    def has_delete_permission(self, request, obj=None):
        # Không cho phép xóa đơn hàng từ admin
        return False
    
    def has_add_permission(self, request):
        # Không cho phép thêm đơn hàng mới từ admin
        return False
