import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyShop.settings')
django.setup()

from shop.models import Product

# Cập nhật màu sắc cho tất cả sản phẩm
for product in Product.objects.all():
    product.colors = 'Black,White,Gray'
    product.save()
    
print(f"Đã cập nhật màu sắc cho {Product.objects.count()} sản phẩm") 