from rest_framework.permissions import BasePermission

from .models import ChangelogEntry, Product, Version


class OwnsProduct(BasePermission):
    """Object access stays with the maintainer who owns the product."""

    def has_object_permission(self, request, view, obj) -> bool:
        if isinstance(obj, Product):
            product = obj
        elif isinstance(obj, (Version, ChangelogEntry)):
            product = obj.product
        else:
            return False
        return product.owner_id == request.user.id
