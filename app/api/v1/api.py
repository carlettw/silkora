from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, tours, geo, bookings, payments, reviews, blogs, site_stats, contact

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(geo.router)
api_router.include_router(tours.router)
api_router.include_router(bookings.router)
api_router.include_router(payments.router)
api_router.include_router(reviews.router)
api_router.include_router(blogs.router)
api_router.include_router(site_stats.router)
api_router.include_router(contact.router)
