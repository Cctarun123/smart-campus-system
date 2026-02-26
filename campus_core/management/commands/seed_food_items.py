from django.core.management.base import BaseCommand

from campus_core.models import FoodItem, FoodStall


SAMPLE_STALLS = {
    "GoMeal Burger Hub": [
        {
            "name": "Classic Cheese Burger",
            "price": "149.00",
            "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Double Patty Smash Burger",
            "price": "199.00",
            "image_url": "https://images.unsplash.com/photo-1572802419224-296b0aeee0d9?auto=format&fit=crop&w=900&q=80",
        },
    ],
    "GoMeal Pizza Point": [
        {
            "name": "Pepperoni Pizza",
            "price": "289.00",
            "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Margherita Pizza",
            "price": "249.00",
            "image_url": "https://images.unsplash.com/photo-1595854341625-f33ee10dbf94?auto=format&fit=crop&w=900&q=80",
        },
    ],
    "GoMeal Chicken House": [
        {
            "name": "Spicy Crispy Chicken",
            "price": "229.00",
            "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Chicken Wings Bucket",
            "price": "259.00",
            "image_url": "https://images.unsplash.com/photo-1527477396000-e27163b481c2?auto=format&fit=crop&w=900&q=80",
        },
    ],
    "GoMeal Beverage Bar": [
        {
            "name": "Fresh Orange Juice",
            "price": "89.00",
            "image_url": "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Berry Smoothie",
            "price": "119.00",
            "image_url": "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=900&q=80",
        },
    ],
    "GoMeal Bakery": [
        {
            "name": "Butter Croissant",
            "price": "79.00",
            "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Chocolate Muffin",
            "price": "69.00",
            "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=900&q=80",
        },
    ],
    "GoMeal Seafood Dock": [
        {
            "name": "Garlic Butter Prawns",
            "price": "319.00",
            "image_url": "https://images.unsplash.com/photo-1559847844-d721426d6edc?auto=format&fit=crop&w=900&q=80",
        },
        {
            "name": "Grilled Fish Fillet",
            "price": "299.00",
            "image_url": "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=900&q=80",
        },
    ],
}


class Command(BaseCommand):
    help = "Seed sample food stalls and items with images for Food Pre-Order dashboard"

    def handle(self, *args, **options):
        created_items = 0
        for stall_name, items in SAMPLE_STALLS.items():
            stall, _ = FoodStall.objects.get_or_create(name=stall_name, defaults={"is_active": True})
            for item in items:
                _, created = FoodItem.objects.update_or_create(
                    stall=stall,
                    name=item["name"],
                    defaults={
                        "price": item["price"],
                        "image_url": item["image_url"],
                    },
                )
                if created:
                    created_items += 1

        self.stdout.write(self.style.SUCCESS(f"Food seeding complete. New items created: {created_items}"))
