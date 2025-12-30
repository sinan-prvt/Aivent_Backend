from rest_framework.generics import ListAPIView, RetrieveAPIView
from catalog_app.models import Category, Product
from catalog_app.serializers.category import CategorySerializer
from catalog_app.serializers.product import ProductSerializer
from rest_framework.generics import ListCreateAPIView
from catalog_app.utils.categories import get_category_and_descendants
from rest_framework.permissions import AllowAny

class CategoryListView(ListAPIView):
    authentication_classes = []   # 🔥 disable JWT
    permission_classes = [AllowAny]

    queryset = Category.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = CategorySerializer



class ProductByCategoryView(ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    serializer_class = ProductSerializer

    def get_queryset(self):
        slug = self.kwargs["slug"]

        category = Category.objects.get(slug=slug)

        category_ids = get_category_and_descendants(category)

        return Product.objects.filter(
            category_id__in=category_ids,
            status=Product.STATUS_APPROVED,
            is_available=True
        )



class ProductDetailView(RetrieveAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductListView(ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    queryset = Product.objects.filter(status=Product.STATUS_APPROVED)
    serializer_class = ProductSerializer

