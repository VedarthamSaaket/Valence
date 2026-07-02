from fastapi import APIRouter, Depends
from database.db import get_db
from routers.auth import get_current_user
from security import assert_owns_profile
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

    recent_results = db.execute(
        """SELECT test_type, taken_at, archetype_name, trait_scores, percentiles
           FROM test_results
           WHERE user_id = ?
           ORDER BY taken_at DESC
           LIMIT 8""",
        (current_user["id"],)
    ).fetchall()
    db.close()

    # Ownership check – the WHERE clause already isolates the user's row,
    # but we validate explicitly so any future refactor cannot silently break this.
    if profile:
        assert_owns_profile(dict(profile), current_user["id"])

    completed_tests = []
    if profile:
        completed_tests = json.loads(profile["completed_tests"] or "[]")

    results_formatted = []
    for r in recent_results:
        results_formatted.append({
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