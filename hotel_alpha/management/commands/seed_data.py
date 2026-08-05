from django.core.management.base import BaseCommand
from hotel_alpha.models import Hotel, Room


class Command(BaseCommand):
    help = 'Seed database with sample hotels and rooms'

    def handle(self, *args, **options):
        if Hotel.objects.exists():
            self.stdout.write('Hotels already exist, skipping seed.')
            return

        hotels_data = [
            {
                'name': 'The Grand Palace',
                'city': 'Mumbai',
                'description': 'A luxurious 5-star hotel overlooking the Arabian Sea, featuring world-class dining, a rooftop infinity pool, and a rejuvenating spa.',
                'rating': 5,
                'rate_per_night': 12000,
                'rooms': [
                    ('Deluxe Room', 2, True, [101, 102, 103], 4500, 'City view, king bed, marble bathroom'),
                    ('Premium Suite', 3, True, [201, 202], 8500, 'Sea view, private balcony, separate living area'),
                    ('Presidential Suite', 4, True, [301], 18000, 'Panoramic sea view, butler service, jacuzzi'),
                ],
            },
            {
                'name': 'Heritage Haveli',
                'city': 'Jaipur',
                'description': 'Experience royal Rajasthani hospitality in this restored 18th-century haveli. Traditional architecture meets modern luxury.',
                'rating': 4,
                'rate_per_night': 6000,
                'rooms': [
                    ('Standard Room', 2, True, [101, 102, 103, 104], 2500, 'Courtyard view, traditional decor'),
                    ('Royal Suite', 3, True, [201, 202], 7000, 'Palace view, antique furniture, private garden'),
                ],
            },
            {
                'name': 'Mountain View Resort',
                'city': 'Manali',
                'description': 'Nestled in the Himalayas, this cozy resort offers breathtaking mountain views, bonfire evenings, and adventure sports packages.',
                'rating': 4,
                'rate_per_night': 4500,
                'rooms': [
                    ('Cottage Room', 2, False, [101, 102, 103], 2200, 'Wooden cottage, mountain views, fireplace'),
                    ('Family Cottage', 4, False, [201, 202], 4000, 'Two bedrooms, living area, private garden'),
                ],
            },
            {
                'name': 'Beachside Inn',
                'city': 'Goa',
                'description': 'A vibrant beachfront property with direct access to the sand. Enjoy sunset cocktails, water sports, and live music every evening.',
                'rating': 3,
                'rate_per_night': 3500,
                'rooms': [
                    ('Garden Room', 2, True, [101, 102, 103, 104, 105], 1800, 'Garden view, AC, balcony'),
                    ('Beach Front Room', 2, True, [201, 202, 203], 3500, 'Direct beach access, sea view, hammock'),
                ],
            },
            {
                'name': 'The Urban Loft',
                'city': 'Bangalore',
                'description': 'A chic boutique hotel in the heart of the city. Modern design, rooftop cafe, co-working spaces, and easy access to tech parks.',
                'rating': 4,
                'rate_per_night': 5000,
                'rooms': [
                    ('Studio Room', 1, True, [101, 102, 103, 104], 2500, 'Compact and modern, work desk, smart TV'),
                    ('Executive Suite', 2, True, [201, 202, 203], 5500, 'Spacious, city skyline view, minibar'),
                ],
            },
            {
                'name': 'Backwater Retreat',
                'city': 'Kochi',
                'description': 'Set along the serene Kerala backwaters, this eco-friendly resort offers houseboat stays, Ayurvedic spa treatments, and authentic local cuisine.',
                'rating': 5,
                'rate_per_night': 9000,
                'rooms': [
                    ('Lake View Room', 2, True, [101, 102, 103], 4500, 'Backwater views, traditional decor, private sit-out'),
                    ('Premium Villa', 4, True, [201, 202], 10000, 'Private pool, butler service, lake access'),
                ],
            },
            {
                'name': 'Desert Oasis Camp',
                'city': 'Jaisalmer',
                'description': 'Luxury desert camping under the stars. Camel safaris, folk performances, and authentic Rajasthani meals in the Thar Desert.',
                'rating': 3,
                'rate_per_night': 4000,
                'rooms': [
                    ('Tent Room', 2, False, [101, 102, 103, 104], 2500, 'Swiss tent, attached bathroom, desert views'),
                    ('Luxury Tent', 2, False, [201, 202], 5500, 'Premium tent, A/C, private campfire area'),
                ],
            },
            {
                'name': 'Skyline Tower Hotel',
                'city': 'Mumbai',
                'description': 'A modern high-rise in the bustling business district. Panoramic city views, multiple restaurants, and a state-of-the-art fitness center.',
                'rating': 4,
                'rate_per_night': 7500,
                'rooms': [
                    ('City Room', 2, True, [101, 102, 103, 104, 105], 4000, 'City view, work desk, modern amenities'),
                    ('Corner Suite', 3, True, [201, 202, 203], 9000, '180-degree city views, executive lounge access'),
                ],
            },
            {
                'name': 'Sunrise Homestay',
                'city': 'Darjeeling',
                'description': 'A charming family-run homestay with stunning views of Kanchenjunga. Home-cooked meals, tea garden tours, and warm hospitality.',
                'rating': 3,
                'rate_per_night': 2000,
                'rooms': [
                    ('Standard Room', 2, False, [101, 102, 103], 1200, 'Mountain views, cozy decor, shared balcony'),
                    ('Family Room', 3, False, [201, 202], 2200, 'Spacious, panoramic views, sitting area'),
                ],
            },
        ]

        for hotel_data in hotels_data:
            rooms = hotel_data.pop('rooms')
            hotel = Hotel.objects.create(**hotel_data)

            for room_data in rooms:
                room_type, capacity, ac, room_nos, price, desc = room_data
                amenities = ['WiFi', 'TV', 'Room Service'] if ac else ['WiFi', 'Room Service']
                for room_no in room_nos:
                    Room.objects.create(
                        hotel=hotel,
                        room_type=room_type,
                        capacity=capacity,
                        ac=ac,
                        room_no=room_no,
                        price=price,
                        description=desc,
                        amenities=amenities,
                    )

        self.stdout.write(self.style.SUCCESS(f'Seeded {len(hotels_data)} hotels with rooms.'))
