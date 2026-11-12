from fastapi import APIRouter, Depends
from utils.module7_dependencies import demo_api_key

router = APIRouter(prefix="/module7/practice",
                   tags=["Module 7 router practice"], dependencies=[Depends(demo_api_key)])


@router.get("/sample")
def sample_endpoint():
    return {"message": "First endpint executed"}


@router.get("/another-sample")
def another_sample_endpoint():
    return {"message": "Another endpoint executed"}
