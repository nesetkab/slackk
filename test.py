from pathlib import Path
from dotenv import load_dotenv
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

import json, time, ssl, csv, os, hickle as hkl, requests, gspread
from datetime import datetime, timezone, timedelta
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from gsheet import outreach_upload
from upload import main
from oauth2client.service_account import ServiceAccountCredentials

global gc, teams_sheet, scouting_sheet
gc = None
teams_sheet = None  
scouting_sheet = None

def fetch_team_stats(team_number):
	"""Fetch OPR stats for a single team"""
	query = """
	query {
		teamByNumber(number: %s) {
			name
			events(season: 2024) {
				stats {
					__typename
					... on TeamEventStats2024 {
						opr {
							autoSamplePoints
							autoSpecimenPoints
							dcSamplePoints
							dcSpecimenPoints
							autoPoints
							dcPoints
							totalPointsNp
							dcParkPointsIndividual
						}
					}
				}
			}
		}
	}
	""" % team_number

	try:
		response = requests.post(
			'https://api.ftcscout.org/graphql',
			json={'query': query}
		)
		data = response.json()
		return data['data']['teamByNumber']
	except Exception as e:
		print(f"Error fetching stats for team {team_number}: {e}")
		return None

def get_best_stats(stats_list):
	try:
		print(f"Processing stats: {json.dumps(stats_list, indent=2)}")
		
		best_stats = {
			'totalPointsNp': 0,
			'autoSamplePoints': 0,
			'autoSpecimenPoints': 0,
			'autoPoints': 0,
			'dcSamplePoints': 0,
			'dcSpecimenPoints': 0,
			'dcPoints': 0,
			'dcParkPointsIndividual': 0
		}
		
		for event in stats_list:
			if event.get('stats') and event['stats'].get('opr'):
				opr = event['stats']['opr']
				print(f"Processing OPR data: {json.dumps(opr, indent=2)}")
				for key in best_stats:
					if opr.get(key) is not None:
						best_stats[key] = max(best_stats[key], float(opr[key]))
		
		return {key: round(value, 2) for key, value in best_stats.items()}
		
	except Exception as e:
		print(f"Error in get_best_stats: {e}")
		raise

def get_current_stats(stats_list):
    try:
        print(f"Processing stats for latest event: {json.dumps(stats_list, indent=2)}")
        
        current_stats = {
            'totalPointsNp': 0,
            'autoSamplePoints': 0,
            'autoSpecimenPoints': 0,
            'autoPoints': 0,
            'dcSamplePoints': 0,
            'dcSpecimenPoints': 0,
            'dcPoints': 0,
            'dcParkPointsIndividual': 0
        }
        
        # Find first event with valid stats (events are in reverse chronological order)
        for event in stats_list:
            if event.get('stats') and event['stats'].get('opr'):
                opr = event['stats']['opr']
                print(f"Found first valid OPR data: {json.dumps(opr, indent=2)}")
                for key in current_stats:
                    if opr.get(key) is not None:
                        current_stats[key] = float(opr[key])
                # Break after finding first valid event
                break
        
        return {key: round(value, 2) for key, value in current_stats.items()}
        
    except Exception as e:
        print(f"Error in get_current_stats: {e}")
        raise

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_path = os.path.join("./", "credentials.json")
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
gc = gspread.authorize(creds)
sheet = gc.open("Worlds Scouting Spreadsheet 2025").sheet1
all_values = sheet.get_all_values()
print(f"Found {len(all_values)} rows in spreadsheet")
		
header_row = ["Name", "Number", "NP OPR", "Auto Sample OPR", "Auto Spec OPR", 
			"Auto OPR", "DC Sample OPR", "DC Specimen OPR", "DC OPR", "Ascent"]
sheet.update('A1:J1', [header_row])

		# Update each team's stats
updated_teams = 0
errors = []
for row_idx, row in enumerate(all_values[1:], start=2):
			try:
				team_number = row[1].strip()  # Column B has team numbers
				if not team_number:
					continue
					
				print(f"Fetching stats for team {team_number}...")
				
				stats = fetch_team_stats(team_number)
				if not stats:
					errors.append(f"No stats found for team {team_number}")
					continue
					
				if not stats.get('events'):
					errors.append(f"No events found for team {team_number}")
					continue

				# Get best stats across all events
				# best_stats = get_best_stats(stats['events'])
				current_stats = get_current_stats(stats['events'])
				#if not best_stats:
				#	errors.append(f"No valid stats for team {team_number}")
				#	continue
				if not current_stats:
					errors.append(f"No valid stats for team {team_number}")
					continue
				
				# Create new row with updated stats
				new_row = [
					stats['name'],                          # Name
					team_number,                            # Number
					current_stats['totalPointsNp'],           # NP OPR
					current_stats['autoSamplePoints'],        # Auto Sample OPR
					current_stats['autoSpecimenPoints'],      # Auto Spec OPR
					current_stats['autoPoints'],              # Auto OPR
					current_stats['dcSamplePoints'],          # DC Sample OPR
					current_stats['dcSpecimenPoints'],        # DC Specimen OPR
					current_stats['dcPoints'],                # DC OPR
					current_stats['dcParkPointsIndividual']   # Ascent
				]
				
				# Update row in spreadsheet
				sheet.update(f'A{row_idx}:J{row_idx}', [new_row])
				updated_teams += 1
				print(f"Updated team {team_number}")
				
				# Sleep briefly to avoid rate limiting
				time.sleep(1)
				
			except Exception as e:
				error_msg = f"Error processing team {team_number}: {str(e)}"
				errors.append(error_msg)
		
		# Send confirmation message
