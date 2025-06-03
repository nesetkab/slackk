import requests
import json


def fetch_team_stats(team_number):
    """Fetches OPR stats for a single team from ftcscout.org."""
    query = f"""
    query {{
        teamByNumber(number: {team_number}) {{
            name
            events(season: 2024) {{
                stats {{
                    __typename
                    ... on TeamEventStats2024 {{
                        opr {{
                            autoSamplePoints
                            autoSpecimenPoints
                            dcSamplePoints
                            dcSpecimenPoints
                            autoPoints
                            dcPoints
                            totalPointsNp
                            dcParkPointsIndividual
                        }}
                    }}
                }}
            }}
        }}
    }}
    """
    try:
        response = requests.post(
            "https://api.ftcscout.org/graphql", json={"query": query}
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return data.get("data", {}).get("teamByNumber")
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching stats for team {team_number}: {e}")
        return None


def get_best_stats(stats_list):
    """
    Calculates the best stats for a team across all their events.
    """
    best_stats = {
        "totalPointsNp": 0,
        "autoSamplePoints": 0,
        "autoSpecimenPoints": 0,
        "autoPoints": 0,
        "dcSamplePoints": 0,
        "dcSpecimenPoints": 0,
        "dcPoints": 0,
        "dcParkPointsIndividual": 0,
    }
    for event in stats_list:
        if event.get("stats") and event["stats"].get("opr"):
            opr = event["stats"]["opr"]
            for key in best_stats:
                if opr.get(key) is not None:
                    best_stats[key] = max(best_stats[key], float(opr[key]))
    return {key: round(value, 2) for key, value in best_stats.items()}


def ftc(teamNum):
    """
    Fetches general information for a single FTC team.
    """
    url = "https://api.ftcscout.org/graphql"
    body = f"""
    query {{
        teamByNumber(number: {teamNum}) {{
            name
            schoolName
            location {{
                city, state, country
            }}
            rookieYear
            quickStats(season:2024) {{
                tot {{
                  value
                  rank
                }}
            }}
        }}
    }}
    """
    try:
        response = requests.post(url=url, json={"query": body})
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching FTC data for team {teamNum}: {e}")
        return None
