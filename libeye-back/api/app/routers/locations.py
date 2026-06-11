from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import LibraryMaster

router = APIRouter(prefix="/api/v1/locations", tags=["Locations"])

@router.get("")
def get_locations(db: Session = Depends(get_db)):
    locations = db.query(LibraryMaster).filter(LibraryMaster.is_active == True).all()
    return [{"location_id": loc.location_id, "room_name": loc.room_name, "section": loc.section, "shelf_num": loc.shelf_num, "level_num": loc.level_num} for loc in locations]
