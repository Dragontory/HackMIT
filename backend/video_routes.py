from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, auth, database

router = APIRouter()

# Get videos of the logged-in user
@router.get("/my_videos")
async def get_my_videos(token: str = Depends(auth.verify_token), db: Session = Depends(database.get_db)):
    # Use the token's subject to find the user
    user = db.query(models.User).filter(models.User.username == token["sub"]).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch the videos of that user
    videos = db.query(models.Video).filter(models.Video.user_id == user.id).all()
    return videos

