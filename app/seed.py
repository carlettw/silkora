"""
Boshlang'ich test ma'lumotlarini bazaga yozadi (davlatlar, bitta tur).
Ishlatish: python -m app.seed
"""
from app.core.database import SessionLocal
from app.models.geo import Country, Destination
from app.models.tour import Tour, TourCategory, TourItineraryDay

db = SessionLocal()

try:
    uzbekistan = Country(
        name={"uz": "O'zbekiston", "ru": "Узбекистан", "en": "Uzbekistan"},
        slug="uzbekistan",
    )
    db.add(uzbekistan)
    db.flush()

    samarkand = Destination(
        name={"uz": "Samarqand", "ru": "Самарканд", "en": "Samarkand"},
        slug="samarkand",
        description={"uz": "Ipak yo'lidagi tarixiy shahar", "ru": "Исторический город на Шёлковом пути", "en": "Historic Silk Road city"},
        country_id=uzbekistan.id,
    )
    db.add(samarkand)
    db.flush()

    tour = Tour(
        title={"uz": "Samarqand: 2 kunlik sayohat", "ru": "Самарканд: путешествие на 2 дня", "en": "Samarkand: 2-Day Trip"},
        slug="samarkand-2-day-trip",
        short_description={"uz": "Registon, Shohi Zinda va Amir Temur maqbarasi", "ru": "Регистан, Шахи Зинда и мавзолей Амира Темура", "en": "Registan, Shah-i-Zinda and Amir Temur Mausoleum"},
        category=TourCategory.multi_day,
        duration_days=2,
        duration_nights=1,
        price=150.00,
        currency="USD",
    )
    tour.countries = [uzbekistan]
    tour.destinations = [samarkand]
    db.add(tour)
    db.flush()

    db.add(TourItineraryDay(
        tour_id=tour.id, day_number=1,
        title={"uz": "Registon maydoni", "ru": "Площадь Регистан", "en": "Registan Square"},
        description={"uz": "Registon, Bibi-Xonim masjidi va bozor", "ru": "Регистан, мечеть Биби-Ханым и базар", "en": "Registan, Bibi-Khanym Mosque and bazaar"},
    ))
    db.add(TourItineraryDay(
        tour_id=tour.id, day_number=2,
        title={"uz": "Shohi Zinda", "ru": "Шахи Зинда", "en": "Shah-i-Zinda"},
        description={"uz": "Maqbaralar majmuasi va Amir Temur maqbarasi", "ru": "Комплекс мавзолеев и мавзолей Амира Темура", "en": "Necropolis complex and Amir Temur Mausoleum"},
    ))

    db.commit()
    print("Demo ma'lumotlar muvaffaqiyatli qo'shildi.")
finally:
    db.close()
