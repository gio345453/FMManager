"""Pydantic schemas for API request/response models."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class _BaseSchema(BaseModel):
    # Keep compatibility with evolving backend payloads: adding fields in
    # services will not make the API fail validation.
    model_config = ConfigDict(extra="allow")


# ============================================================================
# PLAYER SCHEMAS
# ============================================================================

class PlayerBase(_BaseSchema):
    id: int
    nome: str
    squadra: str
    ruolo: str
    ruolo_multiple: Optional[str] = None


class PlayerStats(_BaseSchema):
    pv_weighted: Optional[float] = None
    mv_weighted: Optional[float] = None
    fm_weighted: Optional[float] = None
    gf_weighted: Optional[float] = None
    gs_weighted: Optional[float] = None
    rp_weighted: Optional[float] = None
    rc_weighted: Optional[float] = None
    ass_weighted: Optional[float] = None
    amm_weighted: Optional[float] = None
    esp_weighted: Optional[float] = None


class PlayerPrice(_BaseSchema):
    percentage: float
    credits: float
    budget: float


class PlayerListItem(_BaseSchema):
    id: int
    nome: str
    squadra: str
    ruolo: str
    ruolo_multiple: Optional[str] = None
    overall: Optional[int] = None
    fm_weighted: Optional[float] = None
    mv_weighted: Optional[float] = None
    pv_weighted: Optional[float] = None
    gf_weighted: Optional[float] = None
    ass_weighted: Optional[float] = None
    rc_weighted: Optional[float] = None
    # FIX: fields required by PlayerDetail/PlayerService for weighted cards.
    amm_weighted: Optional[float] = None
    esp_weighted: Optional[float] = None
    rp_weighted: Optional[float] = None
    gs_weighted: Optional[float] = None
    price_percentage: Optional[float] = None
    price_credits: Optional[float] = None
    titolarita: Optional[float] = None
    is_favorite: bool = False
    tags: List[str] = Field(default_factory=list)
    note: str = ""


class PlayerDetail(PlayerListItem):
    history: List[Dict[str, Any]] = Field(default_factory=list)
    price_breakdown: Optional[Dict[str, Any]] = None
    fixture_projections: List[Dict[str, Any]] = Field(default_factory=list)


class PlayerNote(_BaseSchema):
    note: str = ""
    tags: List[str] = Field(default_factory=list)


# ============================================================================
# TEAM SCHEMAS
# ============================================================================

class TeamClassifica(_BaseSchema):
    posizione: int
    punti: int
    gol_fatti: int
    gol_subiti: int
    differenza_reti: int


class TeamKeyPlayerFM(_BaseSchema):
    id: Optional[int] = None
    nome: str
    ruolo: str
    fm: float
    pv: int


class TeamKeyPlayerGol(_BaseSchema):
    id: Optional[int] = None
    nome: str
    ruolo: str
    gol: int
    pv: int


class TeamKeyPlayerAssist(_BaseSchema):
    id: Optional[int] = None
    nome: str
    ruolo: str
    assist: int
    pv: int


class TeamGiocatoriChiave(_BaseSchema):
    fm: TeamKeyPlayerFM
    gol: TeamKeyPlayerGol
    assist: TeamKeyPlayerAssist


class TeamRosterPlayer(_BaseSchema):
    id: int
    nome: str
    ruolo: str
    pv: int
    fm: float
    mv: float
    gf: int
    ass: int


class TeamStats(_BaseSchema):
    squadra: str
    classifica: TeamClassifica
    giocatori_chiave: TeamGiocatoriChiave
    reparti: Dict[str, Any]
    totale_giocatori: int
    roster: Optional[List[TeamRosterPlayer]] = None


class TeamListItem(_BaseSchema):
    squadra: str
    posizione: int
    punti: int
    gol_fatti: int
    gol_subiti: int


# ============================================================================
# OPTIMIZER SCHEMAS
# ============================================================================

class BuildRosaRequest(_BaseSchema):
    budget: float = Field(default=500)
    composition: Dict[str, int] = Field(default_factory=lambda: {"P": 3, "D": 8, "C": 8, "A": 6})
    budget_per_role: Dict[str, float] = Field(default_factory=lambda: {"P": 15, "D": 30, "C": 30, "A": 25})
    selected_players: Optional[Dict[int, Dict[str, Any]]] = None
    blacklisted_teams: Optional[List[str]] = None
    custom_credits: Optional[Dict[int, float]] = None
    value_priority: str = "FM"
    price_percentage: float = 100
    blacklisted_player_ids: Optional[List[int]] = None


class BuildRosaPlayer(_BaseSchema):
    position: int
    id: int
    nome: str
    squadra: str
    ruolo: str
    overall: Optional[int] = None
    fm_weighted: Optional[float] = None
    price_percentage: float
    price_credits: float
    tier: Optional[str] = None


class BuildRosaResponse(_BaseSchema):
    success: bool
    players: List[BuildRosaPlayer]
    stats: Dict[str, Any]
    budget_used: float
    budget_remaining: float


# ============================================================================
# GENERIC SCHEMAS
# ============================================================================

class HealthResponse(_BaseSchema):
    status: str
    message: str
    data_loaded: bool
    players_count: int


class ErrorResponse(_BaseSchema):
    error: str
    detail: Optional[str] = None


# ============================================================================
# COMPARISON SCHEMAS
# ============================================================================

class ComparisonPlayer(_BaseSchema):
    id: int
    found: bool
    nome: str
    squadra: str
    ruolo: str
    fm_weighted: Optional[float] = None
    mv_weighted: Optional[float] = None
    overall: Optional[int] = None
    price_percentage: Optional[float] = None
    price_credits: Optional[float] = None
    seasons_count: Optional[int] = None
    pv_weighted: Optional[float] = None
    gf_weighted: Optional[float] = None
    ass_weighted: Optional[float] = None
    gs_weighted: Optional[float] = None
    rp_weighted: Optional[float] = None


class ComparisonStats(_BaseSchema):
    count: int
    avg_fm: float
    avg_mv: float


class ComparisonResponse(_BaseSchema):
    players: List[ComparisonPlayer]
    comparison: ComparisonStats
    budget: float


# ============================================================================
# LINEUP SCHEMAS
# ============================================================================

class LineupRecommendationRequest(_BaseSchema):
    local_date: str
    formation: str = "auto"
    roster: Dict[str, Any]
    options: Dict[str, float] = Field(default_factory=dict)


# ============================================================================
# AUCTION SCHEMAS
# ============================================================================

class AuctionInitializeRequest(_BaseSchema):
    team_names: List[str]
    starting_credits: Optional[int] = None
    composition: Optional[Dict[str, int]] = None
    minimum_price: Optional[int] = None
    bid_increment: Optional[int] = None
    reserve_per_slot: Optional[int] = None
    call_policy: Optional[str] = None


class AuctionOpenPlayerRequest(_BaseSchema):
    player_id: int


class AuctionBidRequest(_BaseSchema):
    team_id: str
    price: int


class AuctionPhaseRequest(_BaseSchema):
    phase: str


class AuctionPlayer(_BaseSchema):
    id: int
    nome: str
    squadra: str
    ruolo: str
    overall: Optional[int] = None
    fvm: Optional[float] = None
    assigned: bool = False
    current_auction: bool = False


class AuctionStateResponse(_BaseSchema):
    version: int = 1
    phase: str = "NOT_STARTED"
    rules: Dict[str, Any] = Field(default_factory=dict)
    teams: List[Dict[str, Any]] = Field(default_factory=list)
    assigned: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    redo: List[Dict[str, Any]] = Field(default_factory=list)
    current_auction: Optional[Dict[str, Any]] = None
    updated_at: Optional[str] = None
