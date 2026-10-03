from fastapi import APIRouter, Depends
from database.db import get_db
from routers.auth import get_current_user
from security import assert_owns_profile
from routers.results import VALID_TESTS
import json

router = APIRouter()


@router.get("/profile")
def get_profile(current_user=Depends(get_current_user)):
    """
    Returns the profile for the authenticated user ONLY.
    IDOR guard: user_id is always taken from the validated session token,
    never from a query parameter or request body.
    """
    db      = get_db()
    profile = db.execute(
        "SELECT * FROM unified_profiles WHERE user_id = ?",
        (current_user["id"],)
    ).fetchone()

    # Full history: the dashboard shows the most recent take by default but
    # exposes an expandable "show all" view over every historical run of
    # every test, so the limit is dropped here.
    recent_results = db.execute(
        """SELECT id, test_type, taken_at, archetype_name, trait_scores, percentiles
           FROM test_results
           WHERE user_id = ?
           ORDER BY taken_at DESC""",
        (current_user["id"],)
    ).fetchall()
    db.close()

    # Ownership check - the WHERE clause already isolates the user's row,
    # but we validate explicitly so any future refactor cannot silently break this.
    if profile:
        assert_owns_profile(dict(profile), current_user["id"])

    completed_tests = []
    if profile:
        completed_tests = json.loads(profile["completed_tests"] or "[]")

    completed_tests = [t for t in completed_tests if t in VALID_TESTS]

    results_formatted = []
    for r in recent_results:
        if r["test_type"] not in VALID_TESTS:
            continue
        results_formatted.append({
            "id":            r["id"],
            "test_type":     r["test_type"],
            "taken_at":      r["taken_at"],
            "archetype_name": r["archetype_name"],
            "trait_scores":  json.loads(r["trait_scores"]),
            "percentiles":   json.loads(r["percentiles"]),
        })

    return {
        "user":              current_user,
        "completed_tests":   completed_tests,
        "total_tests_taken": len(results_formatted),
        "recent_results":    results_formatted,
        "master_archetype":  dict(profile).get("master_archetype_name") if profile else None,
    }