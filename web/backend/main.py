"""
FastAPI main application
Backend locale per FMManager - mantiene CSV/JSON, usa logica esistente
"""
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import sys
import json
from pathlib import Path
import shutil
import tempfile
import subprocess
import asyncio

# Aggiungi root al path per import
root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path))

from web.backend.schemas import (
    HealthResponse,
    PlayerListItem,
    PlayerDetail,
    PlayerNote,
    TeamListItem,
    TeamStats,
    BuildRosaRequest,
    BuildRosaResponse,
    LineupRecommendationRequest,
    ComparisonResponse,
    ErrorResponse,
    AuctionInitializeRequest,
    AuctionOpenPlayerRequest,
    AuctionBidRequest,
    AuctionPhaseRequest,
    AuctionStateResponse,
    AuctionPlayer
)
from web.backend.services.player_service import PlayerService
from web.backend.services.team_service import TeamService
from web.backend.services.optimizer_service import OptimizerService
from web.backend.services.lineup_service import LineupCalendarError, LineupService, LineupValidationError
from web.backend.services.comparison_service import ComparisonService
from web.backend.services.recommendation_service import RecommendationService
from web.backend.services.settings_service import SettingsService
from web.backend.services.ai_service import chat as ai_chat
from src.data.auto_downloader import AutoDownloader
from src.data.auto_tags import AutoTagsManager
from src.data.settings_manager import get_settings_manager
from src.data.goalkeeper_rotation import get_rotation_analyzer
from web.backend.session_manager import session_manager
from web.backend.progress_tracker import progress_tracker
from web.backend.services.auction_service import AuctionService, AuctionValidationError
from web.backend.services.auction_advisor_service import AuctionAdvisorService

class AIChatRequest(BaseModel):
    message: str


class AIChatResponse(BaseModel):
    response: str
    tools_used: list[str] = []


# ============================================================================
# APP SETUP
# ============================================================================

app = FastAPI(
    title="FMManager API",
    description="API locale per gestione FantaCalcio",
    version="2.0.0"
)

# CORS per sviluppo locale
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permetti tutti per sviluppo locale
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# APP STATE (singleton)
# ============================================================================

class AppState:
    """Global application state"""
    def __init__(self):
        self.df_with_overall = None
        self.player_service = None
        self.team_service = None
        self.auction_service = None
        self.auction_advisor = None

    def reload_data(self):
        """Reload data from disk (after listone update)"""
        # Reset services to force re-init with new data
        self.player_service = None
        self.team_service = None
        self.auction_service = None
        self.auction_advisor = None
        # Force PlayerService/AuctionAdvisor re-init on next access
        # which will reload the data via DataManager

app_state = AppState()


def get_auction_service() -> AuctionService:
    """Asta sincronizzata con le impostazioni correnti."""
    from src.data.league_config import LeagueConfig
    ps = get_player_service()
    league_config = LeagueConfig.from_settings(SettingsService().get_settings())
    if app_state.auction_service is None:
        app_state.auction_service = AuctionService(ps.df_with_overall, league_config=league_config)
    else:
        app_state.auction_service.players_df = ps.df_with_overall
        app_state.auction_service.sync_league_config(league_config)
    app_state.auction_service.price_calculator = ps.price_calculator
    return app_state.auction_service


def get_auction_advisor() -> AuctionAdvisorService:
    """Advisor singleton.

    IMPORTANT: do not call update_players() on every advice request.
    A price-only bid does not change the player dataset, while update_players()
    invalidates every expensive Advisor cache. Cache invalidation is handled by
    explicit data reloads instead.
    """
    ps = get_player_service()
    if app_state.auction_advisor is None:
        app_state.auction_advisor = AuctionAdvisorService(ps.df_with_overall, ps.price_calculator)
    return app_state.auction_advisor


def get_player_service() -> PlayerService:
    """Ottieni player service (lazy init)"""
    if app_state.player_service is None:
        app_state.player_service = PlayerService()
        app_state.df_with_overall = app_state.player_service.df_with_overall
    return app_state.player_service


def get_team_service() -> TeamService:
    """Ottieni team service (lazy init)"""
    if app_state.team_service is None:
        # Usa il DataFrame del player service
        ps = get_player_service()
        app_state.team_service = TeamService(ps.df_with_overall)
    return app_state.team_service


@app.on_event("startup")
async def startup_event():
    """
    Execute on application startup:
    1. Download tiratori data if needed (once per 24h)
    2. Assign automatic tags (rigorista, tiratore piazzati)
    """
    print("\nStarting FMManager Backend...")

    # Download tiratori data
    downloader = AutoDownloader()
    try:
        downloader.download_tiratori()
    except Exception as e:
        print(f"Error downloading tiratori: {e}")

    # Aggiorna automaticamente il calendario prima di inizializzare i servizi
    # che possono creare FixtureDifficultyCalculator.
    try:
        from data.Calendario.download_calendario import sync_current_calendar
        sync_current_calendar(season='2026-27', max_age_hours=6)

        from src.data.fixture_difficulty import invalidate_fixture_calculator
        invalidate_fixture_calculator()
    except Exception as e:
        print(f"Error updating calendar: {e}")

    # Initialize player service (loads all data)
    ps = get_player_service()

    # Assign automatic tags
    if ps.df_with_overall is not None:
        try:
            auto_tags = AutoTagsManager()
            auto_tags.assign_auto_tags(ps.df_with_overall)
        except Exception as e:
            print(f"Error assigning auto tags: {e}")

    print("Backend ready!\n")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Registra heartbeat
    session_manager.heartbeat()

    try:
        ps = get_player_service()
        players_count = len(ps.df_with_overall) if ps.df_with_overall is not None else 0

        return HealthResponse(
            status="ok",
            message="FMManager API is running",
            data_loaded=players_count > 0,
            players_count=players_count
        )
    except Exception as e:
        return HealthResponse(
            status="error",
            message=str(e),
            data_loaded=False,
            players_count=0
        )


@app.post("/api/heartbeat")
async def heartbeat():
    """Endpoint per heartbeat dal frontend - mantiene il server attivo"""
    session_manager.heartbeat()
    return {"status": "ok", "timestamp": session_manager.last_heartbeat}


@app.get("/api/simulation-progress")
async def get_simulation_progress():
    """Ottieni il progresso della simulazione corrente"""
    return progress_tracker.get_status()


# ============================================================================
# AUCTION ENDPOINTS - FASE 0
# ============================================================================

@app.get("/api/auction/state", response_model=AuctionStateResponse)
async def get_auction_state():
    try:
        return get_auction_service().get_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auction/initialize", response_model=AuctionStateResponse)
async def initialize_auction(request: AuctionInitializeRequest):
    try:
        service = get_auction_service()
        current_rules = service.get_state().get("rules") or {}
        return service.initialize(
            team_names=request.team_names,
            starting_credits=int(request.starting_credits if request.starting_credits is not None else current_rules.get("starting_credits", 1)),
            composition=request.composition or dict(current_rules.get("composition") or {}),
            minimum_price=int(request.minimum_price if request.minimum_price is not None else current_rules.get("minimum_price", 1)),
            bid_increment=int(request.bid_increment if request.bid_increment is not None else current_rules.get("bid_increment", 1)),
            reserve_per_slot=int(request.reserve_per_slot if request.reserve_per_slot is not None else current_rules.get("reserve_per_slot", 0)),
            call_policy=request.call_policy or current_rules.get("call_policy", "call"),
        )
    except AuctionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auction/players", response_model=List[AuctionPlayer])
async def get_auction_players():
    try:
        return get_auction_service().get_players()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auction/teams")
async def get_auction_teams():
    try:
        return get_auction_service().get_team_summaries()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auction/advice")
async def get_auction_advice(
    player_id: int,
    team_id: Optional[str] = Query(None),
    current_price: Optional[float] = Query(None),
):
    try:
        service = get_auction_service()
        return get_auction_advisor().advise(
            service.get_state(),
            player_id,
            team_id,
            current_price=current_price,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auction/overview")
async def get_auction_overview(team_id: Optional[str] = Query(None)):
    try:
        service = get_auction_service()
        return get_auction_advisor().overview(service.get_state(), team_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auction/start", response_model=AuctionStateResponse)
async def start_auction():
    try:
        return get_auction_service().start_auction()
    except AuctionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auction/phase", response_model=AuctionStateResponse)
async def set_auction_phase(request: AuctionPhaseRequest):
    try:
        return get_auction_service().set_phase(request.phase)
    except AuctionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auction/open", response_model=AuctionStateResponse)
async def open_auction_player(request: AuctionOpenPlayerRequest):
    try:
        return get_auction_service().open_player(request.player_id)
    except AuctionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auction/bid", response_model=AuctionStateResponse)
async def place_auction_bid(request: AuctionBidRequest):
    try:
        return get_auction_service().place_bid(request.team_id, request.price)
    except AuctionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auction/assign", response_model=AuctionStateResponse)
async def assign_auction_player():
    try:
        return get_auction_service().assign_current()
    except AuctionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auction/undo", response_model=AuctionStateResponse)
async def undo_auction():
    try:
        return get_auction_service().undo()
    except AuctionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auction/redo", response_model=AuctionStateResponse)
async def redo_auction():
    try:
        return get_auction_service().redo()
    except AuctionValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auction/reset", response_model=AuctionStateResponse)
async def reset_auction():
    try:
        return get_auction_service().reset()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players", response_model=List[PlayerListItem])
async def get_players(
    search: Optional[str] = Query(None, description="Search by name"),
    role: Optional[str] = Query(None, description="Filter by role (P/D/C/A)"),
    team: Optional[str] = Query(None, description="Filter by team"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    status: Optional[str] = Query(None, description="Filter by status (Titolare/Panchina/Infortunati/etc)"),
    favorite: Optional[bool] = Query(None, description="Show only favorites"),
    fm_min: Optional[float] = Query(None, description="Minimum FM"),
    fm_max: Optional[float] = Query(None, description="Maximum FM"),
    price_min: Optional[float] = Query(None, description="Minimum price %"),
    price_max: Optional[float] = Query(None, description="Maximum price %"),
    budget: Optional[float] = Query(None, description="Total budget for price calculation"),
    sort: str = Query("Overall", description="Sort by field"),
    order: str = Query("desc", description="Sort order (asc/desc)")
):
    """
    Get players list with filters

    Returns list of players with stats, prices, notes, and favorites
    """
    try:
        from src.data.league_config import LeagueConfig
        if budget is None:
            budget = LeagueConfig.from_settings(SettingsService().get_settings()).starting_budget

        ps = get_player_service()

        players = ps.get_all_players(
            search=search,
            role=role,
            team=team,
            tag=tag,
            status=status,
            favorite=favorite,
            fm_min=fm_min,
            fm_max=fm_max,
            price_min=price_min,
            price_max=price_max,
            budget=budget,
            sort_by=sort,
            sort_order=order
        )

        return players

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/compare", response_model=ComparisonResponse)
async def compare_players(
    ids: str = Query(..., description="Comma-separated player IDs (2-3 players)"),
    budget: Optional[float] = Query(None, description="Total budget for price calculation")
):
    """
    Compare 2-3 players side by side

    Returns detailed comparison with:
    - Individual player stats (FM, MV, Overall, Price)
    - Comparative statistics (averages, best player)
    - Historical data count

    Example: /api/players/compare?ids=123,456,789
    """
    try:
        from src.data.league_config import LeagueConfig
        if budget is None:
            budget = LeagueConfig.from_settings(SettingsService().get_settings()).starting_budget

        # Parse player IDs
        player_ids = [int(pid.strip()) for pid in ids.split(',')]

        if len(player_ids) < 2 or len(player_ids) > 3:
            raise HTTPException(
                status_code=400,
                detail="Devi fornire 2 o 3 player IDs (esempio: ids=123,456,789)"
            )

        ps = get_player_service()

        # Inizializza comparison service
        comparison_service = ComparisonService(ps.df_with_overall)

        # Confronta giocatori
        result = comparison_service.compare_players(
            player_ids=player_ids,
            budget=budget
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/recommend", response_model=List[PlayerListItem])
async def recommend_players(
    selected_ids: Optional[str] = Query(None, description="Comma-separated player IDs already selected (0-2 players)"),
    budget: Optional[float] = Query(None, description="Total budget for price calculation"),
    limit: int = Query(5, description="Number of recommendations")
):
    """
    Get player recommendations based on selected players

    Algorithm:
    - If no players selected: returns top 5 by Overall
    - If players selected: calculates similarity based on role, FM, price, PV

    Uses EXACT logic from Python app player_comparison.py

    Example: /api/players/recommend?selected_ids=123,456&limit=5
    """
    try:
        from src.data.league_config import LeagueConfig
        if budget is None:
            budget = LeagueConfig.from_settings(SettingsService().get_settings()).starting_budget

        ps = get_player_service()

        # Parse selected IDs
        selected_player_ids = []
        if selected_ids:
            selected_player_ids = [int(pid.strip()) for pid in selected_ids.split(',') if pid.strip()]

        # Inizializza recommendation service con price calculator
        recommendation_service = RecommendationService(
            df_with_overall=ps.df_with_overall,
            price_calculator=ps.price_calculator
        )

        # Ottieni raccomandazioni
        recommendations = recommendation_service.get_recommended_players(
            selected_player_ids=selected_player_ids,
            budget=budget,
            limit=limit
        )

        return recommendations

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/{player_id}", response_model=PlayerDetail)
async def get_player_detail(
    player_id: int,
    budget: Optional[float] = Query(None, description="Total budget for price calculation")
):
    """
    Get detailed player information with history

    Returns complete player data including:
    - Current season stats
    - Historical data (3 seasons)
    - Price breakdown
    - Notes and tags
    """
    try:
        from src.data.league_config import LeagueConfig
        if budget is None:
            budget = LeagueConfig.from_settings(SettingsService().get_settings()).starting_budget

        ps = get_player_service()
        player = ps.get_player_by_id(player_id, budget)

        if player is None:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")

        return player

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/favorites", response_model=List[int])
async def get_favorites():
    """Get list of favorite player IDs"""
    try:
        ps = get_player_service()
        return ps.get_favorites()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/players/{player_id}/favorite", response_model=dict)
async def toggle_favorite(player_id: int):
    """
    Toggle player favorite status

    Returns new favorite status (true = favorite)
    """
    try:
        ps = get_player_service()
        is_favorite = ps.toggle_favorite(player_id)

        return {
            "player_id": player_id,
            "is_favorite": is_favorite
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/{player_id}/notes", response_model=PlayerNote)
async def get_player_notes(player_id: int):
    """Get player notes and tags"""
    try:
        ps = get_player_service()
        return ps.get_player_notes(player_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/players/{player_id}/notes", response_model=PlayerNote)
async def update_player_notes(player_id: int, data: PlayerNote):
    """Update player notes and tags"""
    try:
        ps = get_player_service()
        result = ps.update_player_notes(player_id, data.note, data.tags)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/list", response_model=List[str])
async def get_teams_list():
    """Get list of all team names"""
    try:
        ps = get_player_service()
        return ps.get_all_teams()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams", response_model=List[TeamListItem])
async def get_teams():
    """
    Get all teams with basic stats

    Returns team list with league position, points, goals
    """
    try:
        ts = get_team_service()
        return ts.get_all_teams()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/lineup/formations")
async def get_lineup_formations():
    """Restituisce i moduli disponibili dalla configurazione unica."""
    try:
        from src.data.league_config import LeagueConfig
        league_config = LeagueConfig.from_settings(SettingsService().get_settings())
        service = LineupService(get_player_service().df_with_overall, league_config)
        return {"formations": service.available_formations()}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/lineup/recommend")
async def recommend_lineup(request: LineupRecommendationRequest):
    """Recommend a lineup for the single matchday resolved from the local date."""
    from datetime import date

    try:
        local_date = date.fromisoformat(request.local_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="local_date deve usare il formato YYYY-MM-DD.")

    try:
        from src.data.league_config import LeagueConfig
        league_config = LeagueConfig.from_settings(SettingsService().get_settings())
        options = league_config.lineup_options(request.options)
        service = LineupService(get_player_service().df_with_overall, league_config)
        if request.formation == "auto":
            return service.recommend_auto(local_date, request.roster, options)
        return service.recommend(local_date, request.formation, request.roster, options)
    except LineupValidationError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except LineupCalendarError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/build-rosa-complete", response_model=BuildRosaResponse)
async def build_rosa_complete(request: BuildRosaRequest):
    """
    Build optimized squad for Completa Rosa feature

    Enhanced version that supports:
    - Manual player selection (locked by default)
    - Blacklisted player IDs (discarded players)
    - Price percentage adjustment
    - Custom credits per position
    - Re-generation keeping locked players

    Returns optimized squad with statistics
    """
    try:
        ps = get_player_service()
        optimizer_service = OptimizerService(df_with_overall=ps.df_with_overall)

        result = optimizer_service.build_rosa(
            budget=request.budget,
            composition=request.composition,
            budget_per_role=request.budget_per_role,
            selected_players=request.selected_players,
            blacklisted_teams=request.blacklisted_teams,
            custom_credits=request.custom_credits,
            value_priority=request.value_priority,
            price_percentage=request.price_percentage,
            blacklisted_player_ids=request.blacklisted_player_ids
        )

        return result

    except ValueError as e:
        # Errore di validazione/vincoli dell'optimizer
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimizer/build-rosa", response_model=BuildRosaResponse)
async def build_rosa(request: BuildRosaRequest):
    """
    Build optimized squad using knapsack algorithm

    Optimizes player selection based on:
    - Budget constraints per role
    - Composition (number of players per role)
    - Pre-selected players
    - Blacklisted teams
    - Custom credits per position
    - Value priority (FM/MV/PV)

    Returns optimized squad with statistics
    """
    try:
        ps = get_player_service()
        optimizer_service = OptimizerService(df_with_overall=ps.df_with_overall)

        result = optimizer_service.build_rosa(
            budget=request.budget,
            composition=request.composition,
            budget_per_role=request.budget_per_role,
            selected_players=request.selected_players,
            blacklisted_teams=request.blacklisted_teams,
            custom_credits=request.custom_credits,
            value_priority=request.value_priority
        )

        return result

    except ValueError as e:
        # Errore di validazione/vincoli dell'optimizer
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/neopromosse", response_model=List[str])
async def get_neopromosse():
    """
    Get list of neopromosse teams

    Returns list of teams present in current season but without statistics
    """
    try:
        ts = get_team_service()
        return ts.get_neopromosse()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_name}", response_model=TeamStats)
async def get_team_detail(
    team_name: str,
    include_roster: bool = Query(False, description="Include full roster list")
):
    """
    Get detailed team statistics

    Returns complete team data including:
    - League position and stats
    - Key players (best FM, top scorer, top assists)
    - Department strengths
    - Optional: full roster list
    """
    try:
        ts = get_team_service()
        team_stats = ts.get_team_stats(team_name, include_roster=include_roster)

        if team_stats is None:
            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")

        return team_stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teams/{team_name}/dashboard", response_model=TeamStats)
async def get_team_dashboard(
    team_name: str,
    include_roster: bool = Query(False, description="Include full roster list")
):
    """
    Get team dashboard with complete statistics

    Returns comprehensive team data:
    - League position, points, goals (Serie A 2025-26)
    - Key players (best FM, top scorer, top assists)
    - Department analysis (P/D/C/A strengths)
    - Squad depth
    - Optional: full roster list

    This is an alias for GET /api/teams/{team_name}
    """
    try:
        ts = get_team_service()
        team_stats = ts.get_team_stats(team_name, include_roster=include_roster)

        if team_stats is None:
            raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")

        return team_stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/chat", response_model=AIChatResponse)
async def ai_chat_endpoint(request: AIChatRequest):
    """
    Chatbot FantaAI.

    Reuses the existing PlayerService singleton instead of creating a new
    PlayerService for every AI tool call.
    """
    try:
        player_service = get_player_service()
        result = ai_chat(request.message, player_service)
        return AIChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

# Include utility routes (listone update, favorites, health)
from web.backend.routes.utility import router as utility_router
app.include_router(utility_router, prefix="/api", tags=["utility"])


@app.get("/api/settings")
async def get_settings():
    """Get application settings"""
    try:
        settings_service = SettingsService()
        settings = settings_service.get_settings()
        print(f"DEBUG /api/settings: Campi presenti: {list(settings.keys())}")
        print(f"DEBUG: roster_composition presente? {'roster_composition' in settings}")
        print(f"DEBUG: scoring presente? {'scoring' in settings}")
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/settings")
async def update_settings(settings: dict):
    """Update application settings"""
    try:
        settings_service = SettingsService()
        updated_settings = settings_service.save_settings(settings)

        # Invalida cache prezzi quando le impostazioni cambiano
        player_service = get_player_service()
        player_service.invalidate_price_cache()
        print("OK Impostazioni salvate e cache invalidata")

        return updated_settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tags", response_model=List[str])
async def get_all_tags():
    """Get list of all used tags"""
    try:
        ps = get_player_service()
        return ps.get_all_tags()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statuses", response_model=List[str])
async def get_all_statuses():
    """Get list of all available statuses from titolarità data"""
    try:
        ps = get_player_service()
        return ps.get_all_statuses()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inizializza servizi all'avvio"""
    print("Avvio FMManager API...")
    print("Caricamento dati...")

    # Forza inizializzazione player service
    ps = get_player_service()

    if ps.df_with_overall is not None and not ps.df_with_overall.empty:
        print(f"{len(ps.df_with_overall)} giocatori caricati")
    else:
        print("Errore caricamento dati")

    print("API pronta su http://localhost:8000")
    print("Documentazione su http://localhost:8000/docs")


@app.post("/api/update-listone")
async def update_listone(file: UploadFile = File(...)):
    """
    Update player list (listone) from uploaded Excel file

    Workflow:
    1. Validate file format (.xlsx, .xls)
    2. Save to temporary location
    3. Run scripts/convert_quotazioni.py to process
    4. Reload data in memory
    5. Return result with players count

    Uses EXACT logic from Python app update_listone workflow
    """
    try:
        # Validate file extension
        if not file.filename or not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            raise HTTPException(
                status_code=400,
                detail="File format not supported. Only .xlsx and .xls files are allowed."
            )

        # Create temp file to save upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            # Save uploaded file
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        try:
            # Run convert_quotazioni.py script with temp file
            script_path = root_path / "scripts" / "convert_quotazioni.py"

            # Run script with file path as argument
            result = subprocess.run(
                [sys.executable, str(script_path), temp_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(root_path),
                timeout=60
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Conversion failed: {result.stderr}"
                )

            # Reload data in app_state
            ps = get_player_service()
            ps.reload_data()

            players_count = len(ps.df_with_overall) if ps.df_with_overall is not None else 0

            return {
                "success": True,
                "message": "Listone updated successfully",
                "players_count": players_count,
                "output": result.stdout
            }

        finally:
            # Cleanup temp file
            Path(temp_path).unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tiratori")
async def get_tiratori():
    """
    Get penalty takers and set piece takers for all teams

    Returns data from data/Tiratori/tiratori.json with:
    - squadra: team name
    - rigoristi: {1_rigorista, 2_rigorista, 3_rigorista}
    - piazzati_e_angoli: {1_tiratore, 2_tiratore, 3_tiratore}
    """
    try:
        tiratori_file = root_path / 'data' / 'Tiratori' / 'tiratori.json'

        if not tiratori_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Tiratori data not found. Run download first."
            )

        with open(tiratori_file, 'r', encoding='utf-8') as f:
            tiratori_data = json.load(f)

        return tiratori_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/open-season-update-folder")
async def open_season_update_folder():
    """
    Open the Aggiornamento_Fine_Stagione folder in file explorer

    This endpoint is only meant to be called during the season update period
    (July 15 - August 18), but the temporal check is handled on the frontend.
    """
    try:
        import platform
        import os

        folder_path = root_path / "Aggiornamento_Fine_Stagione"

        if not folder_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Aggiornamento_Fine_Stagione folder not found"
            )

        system = platform.system()

        if system == "Windows":
            # Use os.startfile which works better on Windows
            os.startfile(str(folder_path))
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(folder_path)], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", str(folder_path)], check=True)

        return {"success": True, "message": "Folder opened successfully"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Failed to open folder: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/matchday")
async def get_current_matchday():
    """
    Get current matchday setting

    Returns the current matchday (1-38) used for fixture difficulty calculations
    """
    try:
        settings_mgr = get_settings_manager()
        return {
            "current_matchday": settings_mgr.get_current_matchday(),
            "min": 1,
            "max": 38
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings/matchday")
async def set_current_matchday(matchday: int = Query(..., ge=1, le=38)):
    """
    Set current matchday

    Updates the current matchday (1-38) used for fixture difficulty calculations.
    This affects:
    - Next 5 fixtures display
    - Remaining fixtures calculations
    - Fixture difficulty context

    Args:
        matchday: Matchday number (1-38)
    """
    try:
        settings_mgr = get_settings_manager()
        settings_mgr.set_current_matchday(matchday)

        return {
            "success": True,
            "current_matchday": matchday,
            "message": f"Current matchday set to {matchday}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/goalkeeper-rotation/test")
async def test_goalkeeper_rotation():
    """Test endpoint per debug"""
    try:
        import traceback
        ps = get_player_service()

        # Test 1: Get players
        gk1 = ps.get_player_by_id(5841)
        gk2 = ps.get_player_by_id(4431)

        if not gk1 or not gk2:
            return {"error": "Players not found"}

        # Test 2: Build goalkeeper list
        goalkeepers = [
            {'id': gk1['id'], 'name': gk1['nome'], 'team': gk1['squadra']},
            {'id': gk2['id'], 'name': gk2['nome'], 'team': gk2['squadra']}
        ]

        # Test 3: Get analyzer
        analyzer = get_rotation_analyzer()

        # Test 4: Run analysis
        result = analyzer.analyze_goalkeeper_rotation(goalkeepers, 1)

        return {
            "status": "success",
            "goalkeepers": goalkeepers,
            "result_keys": list(result.keys()),
            "from_matchday": result.get('from_matchday'),
            "total_matchdays": result.get('total_matchdays')
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            "status": "error",
            "error": str(e),
            "traceback": error_trace
        }


@app.get("/api/goalkeeper-rotation/analyze")
async def analyze_goalkeeper_rotation(
    goalkeeper_ids: List[int] = Query(..., min_length=2, max_length=3, description="2-3 goalkeeper IDs"),
    from_matchday: Optional[int] = Query(None, ge=1, le=38, description="Starting matchday (None = from settings)")
):
    """
    Analyze goalkeeper rotation for best combinations

    Generates a grid showing difficulty for each goalkeeper across all matchdays,
    and suggests the best rotation to maximize easy fixtures.

    Args:
        goalkeeper_ids: List of 2-3 goalkeeper IDs to analyze
        from_matchday: Starting matchday (default: current from settings)

    Returns:
        Grid data, statistics, and rotation suggestions
    """
    try:
        ps = get_player_service()
        analyzer = get_rotation_analyzer()

        # Get goalkeeper data
        goalkeepers = []
        for gk_id in goalkeeper_ids:
            try:
                player = ps.get_player_by_id(gk_id)
                if not player:
                    raise HTTPException(status_code=404, detail=f"Goalkeeper {gk_id} not found")

                # Verify it's a goalkeeper
                if not player['ruolo'].startswith('P'):
                    raise HTTPException(status_code=400, detail=f"Player {player['nome']} is not a goalkeeper")

                goalkeepers.append({
                    'id': player['id'],
                    'name': player['nome'],
                    'team': player['squadra']
                })
            except Exception as e:
                print(f"Error getting goalkeeper {gk_id}: {e}")
                raise

        # Analyze rotation
        print(f"Analyzing rotation for {len(goalkeepers)} goalkeepers...")
        result = analyzer.analyze_goalkeeper_rotation(goalkeepers, from_matchday)
        print(f"Analysis complete, result keys: {list(result.keys())}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in analyze_goalkeeper_rotation: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-calendario-csv")
async def upload_calendario_csv(file: UploadFile = File(...)):
    """
    Upload and convert calendario CSV from FBref

    Workflow:
    1. Validate file is .csv
    2. Save to data/Calendario/calendario_raw.csv
    3. Run scripts/convert_calendario_csv.py
    4. Return success with match count
    """
    try:
        # Validate file extension
        if not file.filename or not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="File format not supported. Only .csv files are allowed."
            )

        # Save to expected location
        calendario_raw_path = root_path / "data" / "Calendario" / "calendario_raw.csv"
        calendario_raw_path.parent.mkdir(parents=True, exist_ok=True)

        with open(calendario_raw_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)

        # Run conversion script
        script_path = root_path / "scripts" / "convert_calendario_csv.py"

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=str(root_path),
            timeout=30
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Conversion failed: {result.stderr}"
            )

        # Check output file was created
        calendario_json = root_path / "data" / "Calendario" / "calendario.json"
        if not calendario_json.exists():
            raise HTTPException(
                status_code=500,
                detail="Conversion completed but output file not found"
            )

        # Read to get match count
        with open(calendario_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "success": True,
            "message": "Calendario importato con successo",
            "total_matches": data.get('total_matches', 0),
            "season": data.get('season', 'Unknown')
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/league-calendar")
async def get_league_calendar():
    """
    Restituisce il calendario della lega personale correntemente caricato.

    Il file è condiviso tra Simula Stagione e Asta: questo permette alla pagina
    Asta di usare lo stesso calendario senza obbligare l'utente ad avviare
    prima una simulazione Monte Carlo.
    """
    calendar_path = root_path / "data" / "league_calendar.json"
    if not calendar_path.exists():
        raise HTTPException(status_code=404, detail="Nessun calendario lega caricato.")

    try:
        with open(calendar_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore lettura calendario lega: {e}")


@app.post("/api/upload-calendar")
async def upload_league_calendar(file: UploadFile = File(...)):
    """
    Upload calendario lega fantacalcio (Excel format)

    Expected format: Calendario_Serie-A.xlsx con colonne:
    - Giornata
    - Squadra Casa
    - Squadra Trasferta
    """
    import pandas as pd

    temp_path = None
    try:
        # Validate file extension
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(
                status_code=400,
                detail="Formato file non supportato. Solo file Excel (.xlsx, .xls) o CSV (.csv) sono accettati."
            )

        # Save temporarily
        ext = '.csv' if file.filename.endswith('.csv') else '.xlsx'
        temp_path = root_path / "data" / f"temp_calendar{ext}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)

        # Read and parse file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(temp_path)
        else:
            # Convert Excel to CSV for easier parsing
            df_excel = pd.read_excel(temp_path)
            csv_path = root_path / "data" / "temp_calendar.csv"
            df_excel.to_csv(csv_path, index=False, encoding='utf-8')
            df = pd.read_csv(csv_path)
            csv_path.unlink()  # Delete temp CSV

        # Parse block-style calendar with multiple columns
        # Each block spans 6 columns: matchday header (col 0), 0.0 (col 1), 0 (col 2), opponent (col 3), - (col 4), empty (col 5)
        # Next block starts at col 6
        teams = set()
        matchdays_dict = {}

        for idx, row in df.iterrows():
            # Check all potential matchday columns (0, 6, 12, ...)
            for col_offset in range(0, len(df.columns), 6):
                if col_offset >= len(df.columns):
                    break

                cell_value = str(row.iloc[col_offset]) if col_offset < len(row) and pd.notna(row.iloc[col_offset]) else ''

                # Skip empty, URL, or NaN
                if not cell_value or cell_value == 'nan' or cell_value.startswith('http'):
                    continue

                # Check if matchday header
                if 'giornata' in cell_value.lower() and 'lega' in cell_value.lower():
                    matchday_num = int(''.join(filter(str.isdigit, cell_value)))
                    if matchday_num not in matchdays_dict:
                        matchdays_dict[matchday_num] = []
                    continue

                # Team row - get opponent from col_offset + 3
                opponent_col = col_offset + 3
                if opponent_col < len(row) and pd.notna(row.iloc[opponent_col]):
                    away_team = str(row.iloc[opponent_col]).strip()

                    # Skip invalid entries
                    if away_team in ['-', '0', '0.0', 'nan'] or away_team == cell_value:
                        continue

                    home_team = cell_value.strip()
                    teams.add(home_team)
                    teams.add(away_team)

                    # Find matchday by looking backwards in this column
                    matchday_num = None
                    for check_idx in range(idx, -1, -1):
                        if col_offset >= len(df.columns):
                            break
                        check_cell = str(df.iloc[check_idx, col_offset]) if pd.notna(df.iloc[check_idx, col_offset]) else ''
                        if 'giornata' in check_cell.lower() and 'lega' in check_cell.lower():
                            matchday_num = int(''.join(filter(str.isdigit, check_cell)))
                            break

                    if matchday_num and matchday_num in matchdays_dict:
                        matchdays_dict[matchday_num].append({
                            'home': home_team,
                            'away': away_team
                        })

        # Convert to list format
        matchdays = [
            {
                'matchday': md,
                'fixtures': matchdays_dict[md]
            }
            for md in sorted(matchdays_dict.keys())
        ]

        # Save parsed calendar
        calendar_data = {
            'teams': sorted(list(teams)),
            'matchdays': matchdays,
            'total_matchdays': len(matchdays)
        }

        calendar_json = root_path / "data" / "league_calendar.json"
        with open(calendar_json, 'w', encoding='utf-8') as f:
            json.dump(calendar_data, f, indent=2, ensure_ascii=False)

        # Clean up temp file
        if temp_path and temp_path.exists():
            temp_path.unlink()

        return calendar_data

    except HTTPException:
        raise
    except Exception as e:
        if temp_path and temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulate-season")
async def simulate_season(request: dict):
    """
    Avvia simulazione Monte Carlo stagione fantacalcio
    Il progresso può essere monitorato via GET /api/simulation-progress
    """
    from src.logic.monte_carlo_simulator import MonteCarloSimulator, LeagueSettings

    try:
        # Estrai parametri
        rosa = request.get('rosa', [])
        formation = request.get('formation', '3-4-3')
        my_team = request.get('my_team')
        settings_data = request.get('settings', {})
        n_simulations = request.get('n_simulations', 10)

        if not rosa:
            raise HTTPException(status_code=400, detail="Rosa non fornita")

        if not my_team:
            raise HTTPException(status_code=400, detail="Squadra non selezionata")

        # Reset progress tracker
        total_runs = n_simulations * 3
        print(
            f"[Progress] Inizializzazione: 0/{total_runs} simulazioni",
            flush=True
        )
        progress_tracker.start(
            total_simulations=total_runs,
            total_scenarios=3
        )

        # Carica calendario lega
        calendar_path = root_path / "data" / "league_calendar.json"
        if not calendar_path.exists():
            progress_tracker.set_error("Calendario lega non caricato")
            raise HTTPException(status_code=400, detail="Calendario lega non caricato")

        with open(calendar_path, 'r', encoding='utf-8') as f:
            league_calendar = json.load(f)

        # Carica tutti i giocatori disponibili per generare avversari
        all_players = []
        try:
            # Carica tutti i giocatori dal database
            ps = get_player_service()
            players = ps.get_all_players()

            # Estrai gli ID dei giocatori nella rosa dell'utente
            my_player_ids = set()
            for p in rosa:
                if p.get('player') and p['player'].get('id'):
                    my_player_ids.add(p['player']['id'])

            # Crea database COMPLETO per arricchire la rosa utente
            all_players_complete = []
            for p in players:
                player_id = p.get('id') or p.get('ID')
                all_players_complete.append({
                    'id': player_id,
                    'nome': p.get('nome'),
                    'ruolo': p.get('ruolo'),
                    'squadra': p.get('squadra'),
                    'mv_weighted': p.get('mv_weighted') or 6.0,
                    'fm_weighted': p.get('fm_weighted') or 6.0,  # Le chiavi arrivano minuscole da PlayerService
                    'gf_weighted': p.get('gf_weighted') or 0,
                    'ass_weighted': p.get('ass_weighted') or 0,
                    'amm_weighted': p.get('amm_weighted') or 0,
                    'esp_weighted': p.get('esp_weighted') or 0,
                    'gs_weighted': p.get('gs_weighted') or 0,
                    'rp_weighted': p.get('rp_weighted') or 0,
                    'pv_weighted': p.get('pv_weighted') or 0,
                    'au_weighted': p.get('au_weighted') or 0,  # Autogol
                    'consistency': p.get('consistency') or 0.8,
                    'status': p.get('status') or 'unknown',
                    'overall': p.get('overall') or 50
                    ,'price_percentage': p.get('price_percentage') or 0
                    ,'price_credits': p.get('price_credits') or 0
                })

            # Crea lista separata per avversari (SENZA i giocatori della tua rosa)
            all_players = [p for p in all_players_complete if p['id'] not in my_player_ids]

            print(f"[Simulate] Caricati {len(all_players_complete)} giocatori totali dal database")
            print(f"[Simulate] Disponibili per avversari: {len(all_players)} (esclusi {len(my_player_ids)} della tua rosa)")

        except Exception as e:
            print(f"[Simulate] Warning: impossibile caricare giocatori completi: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: usa solo i giocatori della rosa utente (scenario limitato)
            all_players = [p['player'] for p in rosa if p.get('player')]
            print(f"[Simulate] Fallback: uso {len(all_players)} giocatori dalla rosa utente")

        print(f"[Simulate Season] Giocatori disponibili per avversari: {len(all_players)}")

        # La simulazione usa lo stesso contratto delle altre decisioni di lega.
        from src.data.league_config import LeagueConfig
        league_config = LeagueConfig.from_settings(SettingsService().get_settings())
        # Usa solo i valori persistiti in app_settings.json, ignora quelli dal frontend
        settings = LeagueSettings.from_league_config(league_config, {
            'goal_bonus': league_config.scoring['goal_bonus'],
            'assist_bonus': league_config.scoring['assist_bonus'],
            'yellow_card_malus': league_config.scoring['yellow_card_malus'],
            'red_card_malus': league_config.scoring['red_card_malus'],
            'own_goal_malus': league_config.scoring['own_goal_malus'],
            'goal_threshold': league_config.scoring['goal_threshold'],
            'points_per_goal': league_config.scoring['points_per_goal'],
            'mvp_bonus_enabled': settings_data.get('mvpBonusEnabled', False),
            'clean_sheet_enabled': settings_data.get('cleanSheetEnabled', False),
            'clean_sheet_bonus': league_config.scoring['clean_sheet_bonus'],
            'defense_modifier_enabled': settings_data.get('defenseModifierEnabled', True),
        })

        # Crea simulatore
        simulator = MonteCarloSimulator(
            settings=settings,
            root_path=root_path,
            league_config=league_config,
        )

        # Avvia simulazione (3 scenari × n_simulations)
        print(f"[Simulate Season] Avvio simulazione per {my_team}")
        print(f"  - Rosa utente: {len(rosa)} giocatori")
        print(f"  - Formazione: {formation}")
        print(f"  - Simulazioni per scenario: {n_simulations}")
        print(f"  - Totale: 3 × {n_simulations} = {3 * n_simulations}")
        print(f"  - Giocatori disponibili per avversari: {len(all_players)}")
        print(f"  - Squadre nel calendario: {len(league_calendar.get('teams', []))}")
        print(f"  - Giornate: {len(league_calendar.get('matchdays', []))}")

        import time
        start_time = time.time()

        # Progress callback con Manager.Queue per comunicazione inter-processo
        def progress_callback(scenario_id, completed, total_per_scenario, progress_pct):
            """
            Callback chiamato dai processi figli tramite Manager.Queue.
            Aggiorna progress_tracker per l'API /simulation-progress.
            """
            # Calcola progresso globale: 3 scenari, ogni scenario è 33.33%
            scenario_weight = 100.0 / 3
            scenario_progress = (scenario_id - 1) * scenario_weight
            within_scenario_progress = (completed / total_per_scenario) * scenario_weight
            total_progress = scenario_progress + within_scenario_progress

            progress_tracker.update(
                scenario=scenario_id,
                completed=completed,
                total=total_per_scenario * 3,  # Totale globale
                progress=total_progress
            )

            # Log ogni 50 simulazioni
            if completed % 50 == 0:
                print(f"  [Progress] Scenario {scenario_id}: {completed}/{total_per_scenario} ({progress_pct:.1f}%)", flush=True)

        # Esegui la Monte Carlo in un thread separato.
        # Il simulatore usa ProcessPoolExecutor internamente con Manager.Queue
        # per comunicare il progresso in tempo reale.
        print("[Simulate Season] Avvio Monte Carlo con ProcessPoolExecutor + Manager.Queue...", flush=True)
        print("[Simulate Season] Progress real-time ABILITATO tramite inter-process communication", flush=True)

        results = await asyncio.to_thread(
            simulator.simulate_season,
            rosa=rosa,
            formation=formation,
            league_calendar=league_calendar,
            my_team=my_team,
            all_players=all_players,
            n_simulations=n_simulations,
            progress_callback=progress_callback,
            all_players_complete=all_players_complete
        )

        elapsed = time.time() - start_time
        print(f"[Simulate Season] Completato in {elapsed:.2f} secondi")

        # Marca come completato
        progress_tracker.complete()

        return results

    except HTTPException:
        progress_tracker.set_error("HTTP Error")
        raise
    except Exception as e:
        print(f"[Simulate Season] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        progress_tracker.set_error(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendario")
async def get_calendario():
    """
    Get Serie A calendario (schedule)

    Returns the calendario.json file with all matches
    """
    try:
        calendario_file = root_path / 'data' / 'Calendario' / 'calendario.json'

        if not calendario_file.exists():
            raise HTTPException(
                status_code=404,
                detail="Calendario non trovato. Carica un calendario dalla dashboard."
            )

        with open(calendario_file, 'r', encoding='utf-8') as f:
            calendario_data = json.load(f)

        return calendario_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("Starting FMManager Backend Server")
    print("="*60)

    # Avvia il monitoraggio auto-shutdown (disattivato di default, attiva con --auto-shutdown)
    import sys
    if "--auto-shutdown" in sys.argv:
        print("[Info] Auto-shutdown abilitato - server si spegnerà dopo 60s senza heartbeat")
        session_manager.start_monitoring()
    else:
        print("[Info] Auto-shutdown disabilitato (usa --auto-shutdown per abilitarlo)")

    uvicorn.run("web.backend.main:app", host="0.0.0.0", port=8000, reload=False)
