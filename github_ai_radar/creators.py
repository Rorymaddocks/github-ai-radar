from __future__ import annotations

import math
from collections import defaultdict

from .models import Creator, CreatorProfile, RankedRepository


def rank_creators(
    items: list[RankedRepository], profiles: dict[str, CreatorProfile] | None = None,
) -> list[Creator]:
    profiles = profiles or {}
    grouped: dict[str, list[RankedRepository]] = defaultdict(list)
    for item in items:
        grouped[item.repository.owner_login].append(item)

    creators: list[Creator] = []
    for login, repos in grouped.items():
        ordered = sorted(repos, key=lambda item: item.score, reverse=True)
        best = ordered[0]
        total_stars = sum(item.repository.stars for item in repos)
        breakouts = sum(item.signal in {"breakout", "hidden gem", "rising"} for item in repos)
        portfolio = min(100.0, math.log2(len(repos) + 1) * 25)
        reach = min(100.0, math.log10(total_stars + 1) / 5 * 100)
        profile = profiles.get(login.lower())
        audience_efficiency = 0.0
        if profile:
            audience_efficiency = min(100.0, math.log10(total_stars / (profile.followers + 50) + 1) * 50)
        creator_score = 0.55 * best.score + 0.20 * portfolio + 0.15 * reach + 0.10 * audience_efficiency
        reasons = [f"{len(repos)} relevant project{'s' if len(repos) != 1 else ''} discovered"]
        if breakouts:
            reasons.append(f"{breakouts} emerging signal{'s' if breakouts != 1 else ''}")
        if best.star_delta:
            reasons.append(f"best project gained {best.star_delta:,} observed stars")
        if profile and audience_efficiency >= 30:
            reasons.append("project traction outpaces existing audience")
        creators.append(Creator(
            login=login,
            html_url=best.repository.owner_url,
            account_type=best.repository.owner_type,
            score=round(creator_score, 1),
            discovered_repositories=len(repos),
            total_stars=total_stars,
            best_repository=best.repository.full_name,
            best_repository_score=best.score,
            breakout_projects=breakouts,
            reasons=tuple(reasons),
            followers=profile.followers if profile else None,
            bio=profile.bio if profile else "",
            profile_created_at=profile.created_at.isoformat() if profile else "",
        ))
    return sorted(creators, key=lambda creator: creator.score, reverse=True)
