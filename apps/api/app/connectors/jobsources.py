"""ATS/VMS and job-board connectors. Each normalizes external postings to a
common dict shape: {title, client, location, description, required_skills,
min_rate, max_rate, visa_requirements, source, external_id}."""
from __future__ import annotations

import httpx

from .base import BaseConnector


class JobSourceConnector(BaseConnector):
    category = "job_source"

    def fetch_jobs(self, query: str = "", limit: int = 10) -> list[dict]:
        if self.is_live:
            return self._fetch_live(query, limit)
        return self._mock(query, limit)

    def _fetch_live(self, query: str, limit: int) -> list[dict]:  # pragma: no cover
        raise NotImplementedError

    def _mock(self, query: str, limit: int) -> list[dict]:
        return [
            {
                "title": f"{(query or 'Senior Engineer').title()} ({self.name})",
                "client": "Confidential",
                "location": "Remote, US",
                "description": f"Sample {self.name} requirement for {query or 'engineering'}.",
                "required_skills": [s for s in (query or "python").split() if s],
                "min_rate": 60.0,
                "max_rate": 95.0,
                "visa_requirements": [],
                "source": self.name,
                "external_id": f"{self.name}-mock-1",
                "_mock": True,
            }
        ][:limit]


class JobDivaConnector(JobSourceConnector):
    name = "jobdiva"
    required_env = ["jobdiva_client_id", "jobdiva_username", "jobdiva_password"]
    note = "🔴 Requires customer JobDiva account. REST v2 + BhRestToken auth."

    def _fetch_live(self, query: str, limit: int) -> list[dict]:  # pragma: no cover
        from ..config import settings

        with httpx.Client(base_url="https://api.jobdiva.com", timeout=20) as c:
            token = c.get(
                "/apiv2/bi/authenticate",
                params={
                    "clientid": settings.jobdiva_client_id,
                    "username": settings.jobdiva_username,
                    "password": settings.jobdiva_password,
                },
            ).text.strip('"')
            rows = c.get(
                "/apiv2/bi/searchJobs",
                params={"q": query, "rows": limit},
                headers={"Authorization": token},
            ).json()
            return [self._normalize(r) for r in rows]

    def _normalize(self, r: dict) -> dict:  # pragma: no cover
        return {
            "title": r.get("title", ""),
            "client": r.get("customerName", ""),
            "location": r.get("city", ""),
            "description": r.get("description", ""),
            "required_skills": r.get("skills", []),
            "min_rate": float(r.get("payRateFrom") or 0),
            "max_rate": float(r.get("payRateTo") or 0),
            "visa_requirements": [],
            "source": self.name,
            "external_id": str(r.get("id", "")),
        }


class BullhornConnector(JobSourceConnector):
    name = "bullhorn"
    required_env = ["bullhorn_client_id", "bullhorn_client_secret", "bullhorn_username", "bullhorn_password"]
    note = "🔴 Requires Bullhorn account. OAuth2 + REST (JobOrder entity)."

    def _fetch_live(self, query: str, limit: int) -> list[dict]:  # pragma: no cover
        from ..config import settings

        # Bullhorn OAuth2: authorize -> token -> REST login -> entity search.
        with httpx.Client(timeout=20, follow_redirects=True) as c:
            auth = c.get(
                "https://auth.bullhornstaffing.com/oauth/authorize",
                params={
                    "client_id": settings.bullhorn_client_id,
                    "response_type": "code",
                    "username": settings.bullhorn_username,
                    "password": settings.bullhorn_password,
                    "action": "Login",
                },
            )
            code = auth.url.params.get("code")
            tok = c.post(
                "https://auth.bullhornstaffing.com/oauth/token",
                params={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.bullhorn_client_id,
                    "client_secret": settings.bullhorn_client_secret,
                },
            ).json()
            login = c.get(
                "https://rest.bullhornstaffing.com/rest-services/login",
                params={"version": "2.0", "access_token": tok["access_token"]},
            ).json()
            rest_url, bh_token = login["restUrl"], login["BhRestToken"]
            rows = c.get(
                f"{rest_url}search/JobOrder",
                params={
                    "BhRestToken": bh_token,
                    "query": f"(title:{query}) AND isOpen:true" if query else "isOpen:true",
                    "fields": "id,title,clientCorporation,address,publicDescription,skills,payRate,salary",
                    "count": limit,
                },
            ).json()
            return [self._normalize(r) for r in rows.get("data", [])]

    def _normalize(self, r: dict) -> dict:
        client = r.get("clientCorporation") or {}
        addr = r.get("address") or {}
        skills = r.get("skills") or {}
        skill_names = [s.get("name", "") for s in skills.get("data", [])] if isinstance(skills, dict) else list(skills)
        pay = float(r.get("payRate") or 0)
        return {
            "title": r.get("title", ""),
            "client": client.get("name", "") if isinstance(client, dict) else str(client),
            "location": ", ".join(p for p in (addr.get("city"), addr.get("state")) if p),
            "description": r.get("publicDescription", ""),
            "required_skills": [s for s in skill_names if s],
            "min_rate": pay,
            "max_rate": float(r.get("salary") or pay),
            "visa_requirements": [],
            "source": self.name,
            "external_id": str(r.get("id", "")),
        }


class CeipalConnector(JobSourceConnector):
    name = "ceipal"
    required_env = ["ceipal_api_key", "ceipal_email", "ceipal_password"]
    note = "🔴 Requires Ceipal account. getToken + job postings API."

    def _fetch_live(self, query: str, limit: int) -> list[dict]:  # pragma: no cover
        from ..config import settings

        with httpx.Client(base_url="https://api.ceipal.com", timeout=20) as c:
            token = c.post(
                "/v1/createAuthtoken/",
                json={
                    "email": settings.ceipal_email,
                    "password": settings.ceipal_password,
                    "api_key": settings.ceipal_api_key,
                },
            ).json()["access_token"]
            rows = c.get(
                "/v1/getJobPostingsList/",
                params={"keyword": query, "limit": limit},
                headers={"Authorization": f"Bearer {token}"},
            ).json()
            return [self._normalize(r) for r in rows.get("results", [])]

    def _normalize(self, r: dict) -> dict:
        skills = r.get("skills", "")
        skill_list = [s.strip() for s in skills.split(",")] if isinstance(skills, str) else list(skills)
        return {
            "title": r.get("position_title", ""),
            "client": r.get("client", "") or r.get("end_client", ""),
            "location": ", ".join(p for p in (r.get("city"), r.get("state")) if p),
            "description": r.get("public_job_desc", "") or r.get("job_description", ""),
            "required_skills": [s for s in skill_list if s],
            "min_rate": float(r.get("pay_rate_from") or 0),
            "max_rate": float(r.get("pay_rate_to") or 0),
            "visa_requirements": [v.strip() for v in str(r.get("tax_terms", "")).split(",") if v.strip()],
            "source": self.name,
            "external_id": str(r.get("id", "") or r.get("job_code", "")),
        }


class DiceConnector(JobSourceConnector):
    name = "dice"
    required_env = ["dice_api_key"]
    note = "🔴 Use Dice partner/API feed. ⚠️ HTML scraping violates Dice ToS."

    def _fetch_live(self, query: str, limit: int) -> list[dict]:  # pragma: no cover
        from ..config import settings

        with httpx.Client(base_url="https://api.dice.com", timeout=20) as c:
            rows = c.get(
                "/v1/jobs/search",
                params={"q": query, "pageSize": limit},
                headers={"x-api-key": settings.dice_api_key},
            ).json()
            return [self._normalize(r) for r in rows.get("jobs", [])]

    def _normalize(self, r: dict) -> dict:
        rate = r.get("compensation") or {}
        return {
            "title": r.get("title", ""),
            "client": r.get("company", "") or r.get("companyName", ""),
            "location": r.get("location", "") or r.get("jobLocation", ""),
            "description": r.get("summary", "") or r.get("description", ""),
            "required_skills": [s for s in (r.get("skills") or []) if s],
            "min_rate": float(rate.get("min") or 0),
            "max_rate": float(rate.get("max") or 0),
            "visa_requirements": [],
            "source": self.name,
            "external_id": str(r.get("id", "") or r.get("jobId", "")),
        }


class IndeedConnector(JobSourceConnector):
    name = "indeed"
    required_env = ["indeed_publisher_id"]
    note = "🔴 Requires Indeed Publisher ID (Sponsored Jobs / Apply API)."

    def _fetch_live(self, query: str, limit: int) -> list[dict]:  # pragma: no cover
        from ..config import settings

        with httpx.Client(base_url="https://api.indeed.com", timeout=20) as c:
            rows = c.get(
                "/ads/apisearch",
                params={
                    "publisher": settings.indeed_publisher_id,
                    "q": query,
                    "limit": limit,
                    "format": "json",
                    "v": "2",
                },
            ).json()
            return [self._normalize(r) for r in rows.get("results", [])]

    def _normalize(self, r: dict) -> dict:
        return {
            "title": r.get("jobtitle", ""),
            "client": r.get("company", ""),
            "location": r.get("formattedLocation", "")
            or ", ".join(p for p in (r.get("city"), r.get("state")) if p),
            "description": r.get("snippet", ""),
            "required_skills": [],
            "min_rate": 0.0,
            "max_rate": 0.0,
            "visa_requirements": [],
            "source": self.name,
            "external_id": str(r.get("jobkey", "")),
        }


class MonsterConnector(JobSourceConnector):
    name = "monster"
    required_env = ["monster_api_key"]
    note = "🔴 Requires Monster employer API access."

    def _fetch_live(self, query: str, limit: int) -> list[dict]:  # pragma: no cover
        from ..config import settings

        with httpx.Client(base_url="https://api.monster.com", timeout=20) as c:
            rows = c.get(
                "/v2/job/search",
                params={"query": query, "pageSize": limit},
                headers={"Authorization": f"Bearer {settings.monster_api_key}"},
            ).json()
            return [self._normalize(r) for r in rows.get("jobs", [])]

    def _normalize(self, r: dict) -> dict:
        loc = r.get("location") or {}
        salary = r.get("salary") or {}
        return {
            "title": r.get("title", ""),
            "client": r.get("companyName", "") or r.get("company", ""),
            "location": loc.get("displayName", "")
            if isinstance(loc, dict)
            else str(loc),
            "description": r.get("description", ""),
            "required_skills": [s for s in (r.get("skills") or []) if s],
            "min_rate": float(salary.get("min") or 0),
            "max_rate": float(salary.get("max") or 0),
            "visa_requirements": [],
            "source": self.name,
            "external_id": str(r.get("jobId", "") or r.get("id", "")),
        }


class LinkedInConnector(JobSourceConnector):
    name = "linkedin"
    required_env = ["linkedin_access_token"]
    note = "🔴 Requires LinkedIn Talent Solutions partner access. ⚠️ Scraping violates ToS."

    def _fetch_live(self, query: str, limit: int) -> list[dict]:  # pragma: no cover
        from ..config import settings

        with httpx.Client(base_url="https://api.linkedin.com", timeout=20) as c:
            rows = c.get(
                "/v2/jobSearch",
                params={"keywords": query, "count": limit},
                headers={
                    "Authorization": f"Bearer {settings.linkedin_access_token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
            ).json()
            return [self._normalize(r) for r in rows.get("elements", [])]

    def _normalize(self, r: dict) -> dict:
        company = r.get("companyDetails") or {}
        company_name = company.get("name", "") if isinstance(company, dict) else str(company)
        loc = r.get("formattedLocation", "") or r.get("location", "")
        return {
            "title": r.get("title", ""),
            "client": company_name,
            "location": loc,
            "description": r.get("description", {}).get("text", "")
            if isinstance(r.get("description"), dict)
            else r.get("description", ""),
            "required_skills": [s for s in (r.get("skills") or []) if s],
            "min_rate": 0.0,
            "max_rate": 0.0,
            "visa_requirements": [],
            "source": self.name,
            "external_id": str(r.get("entityUrn", "") or r.get("id", "")),
        }


JOB_SOURCES: list[type[JobSourceConnector]] = [
    JobDivaConnector,
    BullhornConnector,
    CeipalConnector,
    DiceConnector,
    IndeedConnector,
    MonsterConnector,
    LinkedInConnector,
]
