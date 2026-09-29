from fastapi import APIRouter, HTTPException, Query

from backend.services.recommendation_service import get_recommendations


router = APIRouter(
    tags=["Energy Recommendations"]
)


@router.get("/recommendations")
def recommendations(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of latest recommendations to return"
    )
):
    try:
        data = get_recommendations(limit)

        return {
            "status": "success",
            "count": len(data),
            "data": data
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while loading recommendations"
        )