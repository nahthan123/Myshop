from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
import re
from django.core.paginator import Paginator
from django.http import JsonResponse
from decimal import Decimal

from .models import Product, Comment, Order, OrderItem
from .forms import CustomUserCreationForm


# Trang chủ (homepage)
def home(request):
    # Lấy 8 sản phẩm mới nhất
    latest_products = Product.objects.all().order_by('-id')[:8]
    
    # Lấy 4 sản phẩm được đánh giá cao
    top_rated_products = Product.objects.all().order_by('-rating')[:4]
    
    return render(request, 'shop/home.html', {
        'latest_products': latest_products,
        'top_rated_products': top_rated_products,
    })


# Trang danh sách sản phẩm
def product_list(request):
    category = request.GET.get('category')
    search = request.GET.get('search')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort')
    products = Product.objects.all()

    if category:
        products = products.filter(category__iexact=category)
    if search:
        products = products.filter(name__icontains=search)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Sắp xếp
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-id')  # hoặc '-created_at' nếu có trường này

    # Phân trang: 12 sản phẩm/trang
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'shop/products.html', {
        'page_obj': page_obj,
        'category': category,
        'search': search,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
    })


# Trang chi tiết sản phẩm
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    comments = product.comments.all()
    
    # Xử lý form bình luận
    if request.method == 'POST' and request.user.is_authenticated:
        content = request.POST.get('content', '').strip()
        rating = int(request.POST.get('rating', 5))
        
        if content:
            # Tạo bình luận mới
            comment = Comment.objects.create(
                product=product,
                user=request.user,
                content=content,
                rating=rating
            )
            
            # Cập nhật đánh giá trung bình của sản phẩm
            all_ratings = product.comments.values_list('rating', flat=True)
            product.rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
            product.rating_count = len(all_ratings)
            product.save()
            
            messages.success(request, 'Cảm ơn bạn đã đánh giá sản phẩm!')
            return redirect('product_detail', pk=product.pk)
    
    context = {
        'product': product,
        'comments': comments,
        'star_range': range(1, 6),  # Để hiển thị 5 sao trong giao diện
    }
    return render(request, 'shop/product_detail.html', context)


# Thêm vào giỏ hàng
@require_POST
def add_to_cart(request, product_id):
    quantity = int(request.POST.get('quantity', 1))
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    cart[product_id_str] = cart.get(product_id_str, 0) + quantity
    request.session['cart'] = cart

    # Nếu là AJAX request, trả về JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': sum(cart.values())})
    return redirect(request.POST.get('next', 'view_cart'))


# Hiển thị giỏ hàng
def view_cart(request):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
        request.session['cart'] = cart

    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)

    cart_items, total = [], 0
    for product in products:
        quantity = cart.get(str(product.id), 0)
        total_price = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': total_price
        })
        total += total_price

    # Calculate tax (5%)
    tax = total * Decimal('0.05')
    final_total = total + tax

    # Nếu là yêu cầu AJAX, trả về JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        cart_data = {
            'cart_items': [
                {
                    'product': {
                        'id': item['product'].id,
                        'name': item['product'].name,
                        'price': item['product'].price,
                        'image': item['product'].image.url if item['product'].image else None
                    },
                    'quantity': item['quantity'],
                    'total_price': item['total_price']
                } for item in cart_items
            ],
            'total': total,
            'tax': tax,
            'final_total': final_total
        }
        return JsonResponse(cart_data)

    return render(request, 'shop/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'final_total': final_total
    })


# Cập nhật số lượng sản phẩm trong giỏ hàng
@require_POST
def update_cart(request, product_id):
    quantity = int(request.POST.get('quantity', 1))
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        if quantity > 0:
            cart[str(product_id)] = quantity
        else:
            del cart[str(product_id)]

    request.session['cart'] = cart
    
    # Nếu là AJAX request, trả về JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Tính tổng tiền
        product_ids = cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        total = 0
        for product in products:
            total += product.price * cart.get(str(product.id), 0)
        
        return JsonResponse({
            'success': True, 
            'cart_count': sum(cart.values()),
            'item_total': product.price * quantity if quantity > 0 else 0,
            'cart_total': total
        })
        
    return redirect('view_cart')


# Xóa sản phẩm khỏi giỏ hàng
@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        
    # Nếu là AJAX request, trả về JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Tính tổng tiền
        product_ids = cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        total = 0
        for product in products:
            total += product.price * cart.get(str(product.id), 0)
            
        return JsonResponse({
            'success': True, 
            'cart_count': sum(cart.values()),
            'cart_total': total
        })
        
    return redirect('view_cart')


# Bắt buộc đăng nhập để thanh toán
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('view_cart')

    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)

    cart_items = []
    total = Decimal('0')

    for product in products:
        quantity = cart.get(str(product.id), 0)
        total_price = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': total_price
        })
        total += total_price

    # Calculate tax (5%)
    tax = total * Decimal('0.05')
    final_total = total + tax

    return render(request, 'shop/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'final_total': final_total
    })


# Hoàn tất đơn hàng (chỉ xoá giỏ hàng tạm thời)
@require_POST
@login_required(login_url='login')
def complete_order(request):
    # Lấy thông tin giỏ hàng
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('view_cart')
        
    # Lấy thông tin khách hàng từ form
    full_name = request.POST.get('full_name')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    address = request.POST.get('address')
    city = request.POST.get('city')
    
    # Tính tổng tiền
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    total_amount = 0
    
    for product in products:
        quantity = cart.get(str(product.id), 0)
        total_amount += product.price * quantity
    
    # Tạo đơn hàng
    order = Order.objects.create(
        user=request.user,
        full_name=full_name,
        email=email,
        phone=phone,
        address=address,
        city=city,
        total_amount=total_amount,
        status='pending'
    )
    
    # Tạo chi tiết đơn hàng
    for product in products:
        quantity = cart.get(str(product.id), 0)
        if quantity > 0:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_price=product.price,
                quantity=quantity
            )
    
    # Xóa giỏ hàng
    request.session['cart'] = {}
    
    messages.success(request, 'Đặt hàng thành công! Cảm ơn bạn đã mua sắm.')
    return render(request, 'shop/order_complete.html', {'order': order})


# Trang tài khoản người dùng
@login_required(login_url='login')
def user_account(request):
    # Lấy tất cả đơn hàng của người dùng
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Tổng số đơn hàng
    total_orders = orders.count()
    
    # Số lượng đơn hàng theo trạng thái
    pending_orders = orders.filter(status='pending').count()
    orders_processing = orders.filter(status='processing').count()
    orders_shipped = orders.filter(status='shipped').count()
    orders_delivered = orders.filter(status='delivered').count()
    processing_orders = orders_processing + orders_shipped # Tổng đơn hàng đang xử lý và đang giao
    
    # Đơn hàng gần đây (5 đơn hàng mới nhất)
    recent_orders = orders[:5]
    
    context = {
        'user': request.user,
        'orders': orders,
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'orders_processing': orders_processing,
        'orders_shipped': orders_shipped,
        'orders_delivered': orders_delivered,
        'processing_orders': processing_orders,
    }
    
    return render(request, 'shop/user_account.html', context)


# Chi tiết đơn hàng
@login_required(login_url='login')
def order_detail(request, order_id):
    # Lấy thông tin đơn hàng
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Lấy các sản phẩm trong đơn hàng
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'shop/order_detail.html', context)


# Đăng ký người dùng
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Tạo tài khoản thành công! Bạn đã được đăng nhập.')
            return redirect('product_list')
        else:
            messages.error(request, 'Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'shop/register.html', {'form': form})


def custom_login(request):
    error_message = None
    username = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember', False) == 'on'
        # Kiểm tra cả hai trường
        if not username and not password:
            error_message = "Vui lòng nhập tên đăng nhập và mật khẩu"
        elif not username:
            error_message = "Vui lòng nhập tên đăng nhập"
        elif not password:
            error_message = "Vui lòng nhập mật khẩu"
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Đăng nhập với tùy chọn ghi nhớ
                login(request, user)
                
                # Xử lý ghi nhớ đăng nhập
                if remember:
                    # Đặt thời gian session 30 ngày thay vì mặc định (thường là khi đóng trình duyệt)
                    request.session.set_expiry(30 * 24 * 60 * 60)  # 30 ngày tính bằng giây
                else:
                    # Mặc định: hết hạn khi đóng trình duyệt
                    request.session.set_expiry(0)
                
                return redirect('product_list')
            else:
                error_message = "Tên đăng nhập hoặc mật khẩu không chính xác"
    return render(request, 'shop/login.html', {'error_message': error_message, 'username': username})