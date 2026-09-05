"""Utility routes - health checks, favorites, listone updates"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.convert_quotazioni import QuotazioniConverter

router = APIRouter()

# In-memory favorites storage (temporary - ideally use DB)
favorites_store = set()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    from ..main import app_state

    return {
        "status": "ok",
        "message": "Backend operativo",
        "data_loaded": app_state.data_manager is not None,
        "players_count": len(app_state.df_with_overall) if app_state.df_with_overall is not None else 0
    }


@router.get("/favorites")
async def get_favorites():
    """Get list of favorite player IDs"""
    return {"favorites": list(favorites_store)}


@router.post("/favorites/{player_id}")
async def add_favorite(player_id: int):
    """Add player to favorites"""
    favorites_store.add(player_id)
    return {"success": True, "player_id": player_id}


@router.delete("/favorites/{player_id}")
async def remove_favorite(player_id: int):
    """Remove player from favorites"""
    favorites_store.discard(player_id)
    return {"success": True, "player_id": player_id}


@router.post("/update-listone")
async def update_listone(file: UploadFile = File(...)):
    """
    Update listone from uploaded Excel file
    Uses existing convert_quotazioni.py logic

    Args:
        file: Excel file (.xlsx or .xls) with quotazioni

    Returns:
        Success message with player count
    """
    # Validate file extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="File must be .xlsx or .xls format"
        )

    try:
        # Save uploaded file temporarily
        temp_path = Path("data") / "temp_upload.xlsx"
        temp_path.parent.mkdir(exist_ok=True)

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Use existing converter logic
        converter = QuotazioniConverter()
        output_path, message = converter.run_auto(file_path=temp_path)

        # Clean up temp file
        temp_path.unlink(missing_ok=True)

        if output_path is None:
            raise HTTPException(status_code=500, detail=message)

        # Reload data in backend
        from ..main import app_state
        app_state.reload_data()

        return {
            "success": True,
            "message": message,
            "output_file": str(output_path),
            "players_count": len(app_state.df_with_overall) if app_state.df_with_overall is not None else 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore aggiornamento listone: {str(e)}"
        )
