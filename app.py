from pathlib import Path
from dotenv import load_dotenv
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

import json
import ssl
import csv
import os
import hickle as hkl
from datetime import datetime, timezone, timedelta
import requests
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from gsheet import outreach_upload
from upload import main
import gspread
from oauth2client.service_account import ServiceAccountCredentials

global gc, teams_sheet, scouting_sheet
gc = None
teams_sheet = None  
scouting_sheet = None

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED
flask_app = Flask(__name__)
app = App(
	token = os.environ['SLACK_TOKEN'],
	signing_secret = os.environ["SIGNING_SECRET"],
	# ssl = ssl_context
)
handler = SlackRequestHandler(app)
m_category = "default"
p_category = "deafult"
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
	return handler.handle(request)

@flask_app.route('/')
def hello():
	return 'Hello, World!'

# SEND MESSAGES
def send_confirm_msg(client):
	res = client.chat_postMessage(
		channel="C07QFDDS9QW",
		text="API Upload succesful :)"
	)

def send_m_update_msg(client, user_info, what_you_did, file_info):
	attachments = []
	for file in file_info:
		attachment = {
			"fallback": "Image attachment",
			"image_url": file  # Use the URL directly here
		}
		attachments.append(attachment)
	res = client.chat_postMessage(
		channel="C07GPKUFGQL",
		text="**New Entry**:\n" + ", ".join(user_info) + "\n- **What:** " + str(what_you_did) + "\n**Images:** " + ",".join(file_info),
				attachments=attachments
			)
def send_p_update_msg(client, user_info, what_you_did, file_info):
	attachments = []
	for file in file_info:
		attachment = {
			"fallback": "Image attachment",
			"image_url": file  # Use the URL directly here
		}
		attachments.append(attachment)
	res = client.chat_postMessage(
		channel="C07H9UN6VMW",
		text="**New Entry**:\n" + ", ".join(user_info) + "\n- **What:** " + str(what_you_did) + "\n**Images:** " + ",".join(file_info),
				attachments=attachments
			)
	
def outreach_response(client, err):
	res = client.chat_postMessage(
		channel="C07QFDDS9QW",
		text="Outreach:" + str(err)
	)	

def send_done_msg(client, sub_usr, sub_time):
	confirm_msg = sub_usr + " made an Engineering Notebook entry at " + sub_time 
	res = client.chat_postMessage(
		channel="C07QFDDS9QW",
		text=confirm_msg
	)
	upload_subdata(client)
	
def upload_subdata(client):
	res = client.files_upload_v2(
		file="submission_data.json",
		title="My file",
		initial_comment="Submission Data",
  		channel="C07QFDDS9QW"
	)

@app.command("/help")
def handle_command(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	res = client.chat_postMessage(
		channel="C07QFDDS9QW",
		text="help"
	)

@app.command("/scout")
def handle_command(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	print("scout")
	scout_modal(trigger_id, client)  
	
@app.view("scout-modal-identifier")
def handle_scout_submission(ack, body, logger, client):
	try:
		ack()
		# Set up Google Sheets connection
		scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
		creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
		gc = gspread.authorize(creds)
		
		submitted_data = body['view']['state']['values']
		
		# Get submission time
		submission_time = datetime.now(timezone(timedelta(hours=-7))).strftime('%Y-%m-%d %H:%M:%S')
		
		# Extract data from submission
		team_info = None
		team_name = None
		robot_type = None
		spec_auto = None
		sample_auto = None
		spec_tele = None
		sample_tele = None
		ascent_level = None
		contact_info = None
		notes = None
		
		for block_id, block_data in submitted_data.items():
			for action_id, action_data in block_data.items():
				if action_id == "team_select_action":
					team_info = action_data['selected_option']['value']
					# Get team name from sheet
					sheet = gc.open("Worlds Scouting Spreadsheet 2025").sheet1
					teams_data = sheet.get_all_values()
					for team in teams_data:
						if team[1] == team_info:  # If team number matches
							team_name = team[0]   # Get team name
							break
				elif action_id == "robot_type_action":
					robot_type = action_data['selected_option']['value']
				elif action_id == "spec_auto_action":
					spec_auto = action_data['selected_option']['value']
				elif action_id == "sample_auto_action":
					sample_auto = action_data['selected_option']['value']
				elif action_id == "spec_tele_action":
					spec_tele = action_data['selected_option']['value']
				elif action_id == "sample_tele_action":
					sample_tele = action_data['selected_option']['value']
				elif action_id == "ascent_action":
					ascent_level = action_data['selected_option']['value']
				elif action_id == "contact_action":
					contact_info = action_data['value']
				elif action_id == "notes_action":
					notes = action_data['value']

		# Open scouting worksheet to append data
		scouting_sheet = gc.open("Worlds Scouting Spreadsheet 2025").worksheet("Scouting")
		
		# Append new row with scouting data
		new_row = [
			submission_time,  # Timestamp
			team_info,       # Team Number
			team_name,       # Team Name
			robot_type,      # Robot Type
			spec_auto,       # Specimen Auto
			sample_auto,     # Sample Auto
			spec_tele,       # Specimen Teleop
			sample_tele,     # Sample Teleop
			ascent_level,    # Ascent Level
			contact_info,    # Contact Information
			notes           # Additional Notes
		]
		
		scouting_sheet.append_row(new_row)
		
		# Send formatted scouting report
		client.chat_postMessage(
			channel="C07QFDDS9QW",  
			blocks=[
				{
					"type": "header",
					"text": {
						"type": "plain_text",
						"text": f"Team Scouted: Team {team_info} - {team_name}"
					}
				},
				{
					"type": "section",
					"fields": [
						{
							"type": "mrkdwn",
							"text": f"*Robot Type:* {robot_type}"
						}
					]
				},
				{
					"type": "section",
					"fields": [
						{
							"type": "mrkdwn",
							"text": f"*Specimen Auto:* {spec_auto}\n*Sample Auto:* {sample_auto}"
						},
						{
							"type": "mrkdwn",
							"text": f"*Specimen Teleop:* {spec_tele}\n*Sample Teleop:* {sample_tele}"
						}
					]
				},
				{
					"type": "section",
					"fields": [
						{
							"type": "mrkdwn",
							"text": f"*Ascent Level:* {ascent_level}"
						},
						{
							"type": "mrkdwn",
							"text": f"*Contact:* {contact_info}"
						}
					]
				},
				{
					"type": "section",
					"text": {
						"type": "mrkdwn",
						"text": f"*Additional Notes:*\n{notes}"
					}
				},
				{
					"type": "context",
					"elements": [
						{
							"type": "mrkdwn",
							"text": f"Submitted at {submission_time}"
						}
					]
				}
			]
		)

	except Exception as e:
		logger.error(f"Error saving scouting data: {str(e)}")
		client.chat_postMessage(
			channel="C07QFDDS9QW",
			text=f"Error saving scouting data: {str(e)}"
		)
def get_spec_auto_options():
	return [
		{"text": {"type": "plain_text", "text": "None"}, "value": "none"},
		{"text": {"type": "plain_text", "text": "1+0"}, "value": "1+0"},
		{"text": {"type": "plain_text", "text": "2+0"}, "value": "2+0"},
		{"text": {"type": "plain_text", "text": "3+0"}, "value": "3+0"},
		{"text": {"type": "plain_text", "text": "4+0"}, "value": "4+0"},
		{"text": {"type": "plain_text", "text": "5+0"}, "value": "5+0"},
		{"text": {"type": "plain_text", "text": "5+1"}, "value": "5+1"},
		{"text": {"type": "plain_text", "text": "6+0"}, "value": "6+0"},
		{"text": {"type": "plain_text", "text": "7+0"}, "value": "7+0"}
	]

def get_sample_auto_options():
	return [
		{"text": {"type": "plain_text", "text": "None"}, "value": "none"},
		{"text": {"type": "plain_text", "text": "0+1"}, "value": "0+1"},
		{"text": {"type": "plain_text", "text": "0+2"}, "value": "0+2"},
		{"text": {"type": "plain_text", "text": "0+3"}, "value": "0+3"},
		{"text": {"type": "plain_text", "text": "0+4"}, "value": "0+4"},
		{"text": {"type": "plain_text", "text": "0+5"}, "value": "0+5"},
		{"text": {"type": "plain_text", "text": "0+6"}, "value": "0+6"},
		{"text": {"type": "plain_text", "text": "0+7"}, "value": "0+7"},
		{"text": {"type": "plain_text", "text": "0+8"}, "value": "0+8"}
	]

def get_tele_options():
	options = [
		{"text": {"type": "plain_text", "text": "None"}, "value": "0"}
	]
	
	options.extend([
		{
			"text": {"type": "plain_text", "text": str(i)},
			"value": str(i)
		}
		for i in range(1, 21)  # 1-20 inclusive
	])
	
	return options

def scout_modal(trigger_id, client):
	try:
		global gc  # Add at top of file with other globals
		if not gc:
			scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
			creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
			gc = gspread.authorize(creds)
		
		# 2. Cache the sheet objects
		global teams_sheet, scouting_sheet
		if not teams_sheet:
			teams_sheet = gc.open("Worlds Scouting Spreadsheet 2025").sheet1
			scouting_sheet = gc.open("Worlds Scouting Spreadsheet 2025").worksheet("Scouting")
		
		# 3. Get teams data more efficiently
		all_teams = teams_sheet.get_all_values()[1:]  # Skip header row
		
		# 4. Get scouted teams efficiently 
		scouted_teams = set()
		scouted_data = scouting_sheet.get_all_values()[1:] if scouting_sheet.get_all_values() else []
		scouted_teams = {row[1] for row in scouted_data}  # Use set comprehension
		
		# 5. Create options more efficiently
		team_options = [
			{
				"text": {"type": "plain_text", "text": f"{team[1]} - {team[0]}"},
				"value": str(team[1])
			}
			for team in all_teams 
			if str(team[1]) not in scouted_teams
		][:100]  # Limit to 100 inline

		# Rest of your modal code...
		blocks = [
			{
				"type": "input", 
				"block_id": "team_block",
				"element": {
					"type": "static_select",
					"placeholder": {"type": "plain_text", "text": "Select a team"},
					"options": team_options,
					"action_id": "team_select_action"
				},
				"label": {"type": "plain_text", "text": "Select Team"}
			},
			{
				"type": "input",
				"block_id": "robot_type_block",
				"element": {
					"type": "static_select",
					"placeholder": {"type": "plain_text", "text": "Select robot type"},
					"options": [
						{"text": {"type": "plain_text", "text": "Specimen"}, "value": "specimen"},
						{"text": {"type": "plain_text", "text": "Sample"}, "value": "sample"},
						{"text": {"type": "plain_text", "text": "Both"}, "value": "both"}
					],
					"action_id": "robot_type_action"
				},
				"label": {"type": "plain_text", "text": "Robot Type"}
			},
			{
				"type": "input",
				"block_id": "spec_auto_block",
				"element": {
					"type": "static_select",
					"placeholder": {"type": "plain_text", "text": "Select Specimen Auto"},
					"options": get_spec_auto_options(),
					"action_id": "spec_auto_action"
				},
				"label": {"type": "plain_text", "text": "Specimen Auto"}
			},
			{
				"type": "input",
				"block_id": "sample_auto_block",
				"element": {
					"type": "static_select",
					"placeholder": {"type": "plain_text", "text": "Select Sample Auto"},
					"options": get_sample_auto_options(),
					"action_id": "sample_auto_action"
				},
				"label": {"type": "plain_text", "text": "Sample Auto"}
			},
			{
				"type": "input",
				"block_id": "spec_tele_block",
				"element": {
					"type": "static_select",
					"placeholder": {"type": "plain_text", "text": "Select Specimen Teleop"},
					"options": get_tele_options(),
					"action_id": "spec_tele_action"
				},
				"label": {"type": "plain_text", "text": "Specimen Teleop"}
			},
			{
				"type": "input",
				"block_id": "sample_tele_block",
				"element": {
					"type": "static_select",
					"placeholder": {"type": "plain_text", "text": "Select Sample Teleop"},
					"options": get_tele_options(),
					"action_id": "sample_tele_action"
				},
				"label": {"type": "plain_text", "text": "Sample Teleop"}
			},
			{
				"type": "input",
				"block_id": "ascent_block",
				"element": {
					"type": "static_select",
					"placeholder": {"type": "plain_text", "text": "Select ascent level"},
					"options": [
						{"text": {"type": "plain_text", "text": "None"}, "value": "none"},
						{"text": {"type": "plain_text", "text": "L1"}, "value": "l1"},
						{"text": {"type": "plain_text", "text": "L2"}, "value": "l2"},
						{"text": {"type": "plain_text", "text": "L3"}, "value": "l3"}
					],
					"action_id": "ascent_action"
				},
				"label": {"type": "plain_text", "text": "Ascent Level"}
			},
			{
				"type": "input",
				"block_id": "contact_block",
				"element": {
					"type": "plain_text_input",
					"action_id": "contact_action"
				},
				"label": {"type": "plain_text", "text": "Contact Information"}
			},
			{
				"type": "input",
				"block_id": "notes_block",
				"element": {
					"type": "plain_text_input",
					"multiline": True,
					"action_id": "notes_action"
				},
				"label": {"type": "plain_text", "text": "Additional Notes"}
			}
		]

		res = client.views_open(
			trigger_id=trigger_id,
			view={
				"type": "modal",
				"callback_id": "scout-modal-identifier",
				"title": {"type": "plain_text", "text": "Scout Team"},
				"submit": {"type": "plain_text", "text": "Submit"},
				"close": {"type": "plain_text", "text": "Cancel"},
				"blocks": blocks
			}
		)
		return res
	except Exception as e:
		print(f"Error creating scout modal: {str(e)}")
		raise

@app.options("team_select_action")
def handle_team_selec_options(ack, body, logger):
	print("hello")
	try:
		# Read teams from CSV file
		with open('teams.csv', 'r') as file:
			csv_reader = csv.reader(file)
			next(csv_reader)  # Skip header row if present
			teams_data = list(csv_reader)
		
		# Format teams for Slack dropdown
		options = [
			{
				"text": {
					"type": "plain_text",
					"text": f"{team[1]} - {team[0]}"  # Assuming format: name,number
				},
				"value": str(team[1])
			}
			for team in teams_data
		]
		
		# Send options back to Slack
		ack(options = options)
		logger.info(f"Successfully loaded {len(options)} teams")
		
	except Exception as e:
		logger.error(f"Error in team selection: {str(e)}")
		ack(options = [{"text": {"type": "plain_text", "text": "Error loading teams"}, "value": "error"}])

@app.command("/ftc")
def handle_command(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	toa = ftc(body["text"])
	res = client.chat_postMessage(
		channel=body["channel_id"],
		blocks = [
			{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "Team Info: Team " + str(body["text"])
			}
			},
			{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Team Name:*\n" + toa["data"]["teamByNumber"]["name"]
			}
			}
		]
	)

def ftc(teamNum):
	url = "https://api.ftcscout.org/graphql"
	body = """
	query {
  		teamByNumber(number: """ + str(teamNum) + """) {
			name
			schoolName
			location {
	  			city, state, country
			}
			rookieYear
   			website
  		}
	}
	"""
	response = requests.post(url=url, json={"query": body}) 
	print("response status code: ", response.status_code) 
	if response.status_code == 200: 
		print("response : ", response.content) 
		return response.content





#	   #########      ####				####
#	 ############     ####				####
#	###        ###    ####				####
#	###        ###    ####				####
#	##############    ####				####
#   ##############    ####				####
#   ###        ###    ####				####
#   ###        ###    ##############    ##############
#   ###        ###    ##############    ##############

def open_modal(trigger_id, client):
	res = client.views_open(
		trigger_id=trigger_id,
	view={
		"type": "modal",
		"callback_id": "modal-identifier",
		"submit": {
			"type": "plain_text",
			"text": "Next"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "Create New Entry"
		},
		"blocks": [ 
			{
				"type": "section",
				"text": {
					"type": "plain_text",
					"text": "Choose the category:"
				},
				"accessory": {
					"type": "radio_buttons",
					"action_id": "category_action_id",
					"options": [
						{
							"value": "mech",
							"text": {
								"type": "plain_text",
								"text": "Mechanical"
							}
						},
						{
							"value": "prog",
							"text": {
								"type": "plain_text",
								"text": "Programming"
							}
						},
						{
							"value": "outreach",
							"text": {
								"type": "plain_text",
								"text": "Outreach"
							}
						}
					]
				}
			}
		]
	}
	)
	return res

#			#######
#		#######
#	  ######
#	 ####			
#	####
#	####
#	####
#	####
#	####

def mech_categories(trigger_id, client):
	res = client.views_open(
		trigger_id=trigger_id,
	view={
		"type": "modal",
		"callback_id": "mech-categories-identifier",
		"submit": {
			"type": "plain_text",
			"text": "Next"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "Create New Entry"
		},
		"blocks": [ 
			{
				"type": "input",
				"element": {
					"type": "static_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Select an item"
					},
					"options": [{'value': 'drivetrain', 
				  				'text': {'type': 'plain_text', 'text': 'Drivetrain'}
								}, 
								{'value': 'intake', 
		 						'text': {'type': 'plain_text', 'text': 'Intake'}
								}],
					"action_id": "static_select-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Choose a category:"
				}
			},
			{
				"type": "section",
				"text": {
					"type": "plain_text",
					"text": "My category isn't there: DM Nes'et (this is hardcoded)"
				}
			}
		]
	}
	)
	return res

# OLD CODE, CATS ARE HARDCODED NOW !!!
'''
def new_mech_category(view_id, client):
	res = client.views_update(
		view_id=view_id,
	view={
		"type": "modal",
		"callback_id": "n_mech_cat_identifier",
		"submit": {
			"type": "plain_text",
			"text": "Next"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "Create New Entry"
		},
		"blocks": [ 
			{
				"type": "input",
				"element": {
					"type": "plain_text_input",
					"action_id": "plain_text_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Enter New Category Below:"
				}
			}
		]
	}
	)
	return res
'''
def mech_modal(trigger_id, client):
	res = client.views_open(
		trigger_id=trigger_id,
	view={
		"type": "modal",
		"callback_id": "mech-modal-identifier",
		"submit": {
			"type": "plain_text",
			"text": "Submit"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "Create New Entry"
		},
		"blocks": [
			{
				"type": "input",
				"element": {
					"type": "multi_users_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Select People"
					},
					"action_id": "multi_users_select-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Who Was There?"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "plain_text_input",
					"action_id": "plain_text_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "What You Did:"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "plain_text_input",
					"action_id": "plain_text_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "What You Learned:"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "radio_buttons",
					"options": [
						{
							"text": {
								"type": "plain_text",
								"text": "Yes"
							},
							"value": "yes"
						},
						{
							"text": {
								"type": "plain_text",
								"text": "No"
							},
							"value": "no"
						}
					],
					"action_id": "radio_buttons-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Milestone?"
				}
			},
			{
				"type": "input",
				"block_id": "input_block_id",
				"label": {
					"type": "plain_text",
					"text": "Upload Images"
				},
				"element": {
					"type": "file_input",
					"action_id": "file_input_action_id_1",
					"filetypes": [
						"jpg",
						"png",
						"jpeg",
						"heic"
					],
					"max_files": 10
				}
			}
		]
	}
	)
	return res



#	####    
# 	##  ##
#   #####
#   ##
#   ##

def prog_categories(trigger_id, client):
	res = client.views_open(
		trigger_id=trigger_id,
	view={
		"type": "modal",
		"callback_id": "prog-categories-identifier",
		"submit": {
			"type": "plain_text",
			"text": "Next"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "Create New Entry"
		},
		"blocks": [ 
			{
				"type": "input",
				"element": {
					"type": "static_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Select an item"
					},
					"options": [{'value': 'limelight', 
				  				'text': {'type': 'plain_text', 'text': 'Limelight'}}, 
								{'value': 'roadrunner', 
		 						'text': {'type': 'plain_text', 'text': 'Roadrunner'}
		 						},
						   		{'value': 'autonomous',
								 'text': {'type': 'plain_text', 'text': 'Autonomous'}
								}],
					"action_id": "static_select-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Choose a category:"
				}
			},
			{
				"type": "section",
				"text": {
					"type": "plain_text",
					"text": "My category isn't there: DM Nes'et (this is hardcoded)"
				}
			}
		]
	}
	)
	return res


# OLD CODE, CATS ARE HARDCODED NOW !!!
'''
def new_prog_category(view_id, client):
	res = client.views_update(
		view_id=view_id,
	view={
		"type": "modal",
		"callback_id": "n_prog_cat_identifier",
		"submit": {
			"type": "plain_text",
			"text": "Next"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "Create New Entry"
		},
		"blocks": [ 
			{
				"type": "input",
				"element": {
					"type": "plain_text_input",
					"action_id": "plain_text_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Enter New Category Below:"
				}
			}
		]
	}
	)
	return res
'''


def prog_modal(trigger_id, client):
	res = client.views_open(
		trigger_id=trigger_id,
	view={
		"type": "modal",
		"callback_id": "prog-modal-identifier",
		"submit": {
			"type": "plain_text",
			"text": "Submit"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "Create New Entry"
		},
		"blocks": [
			{
				"type": "input",
				"element": {
					"type": "multi_users_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Select People"
					},
					"action_id": "multi_users_select-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Who Was There?"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "plain_text_input",
					"action_id": "plain_text_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "What You Did:"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "plain_text_input",
					"action_id": "plain_text_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "What You Learned:"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "radio_buttons",
					"options": [
						{
							"text": {
								"type": "plain_text",
								"text": "Yes"
							},
							"value": "yes"
						},
						{
							"text": {
								"type": "plain_text",
								"text": "No"
							},
							"value": "no"
						}
					],
					"action_id": "radio_buttons-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Milestone?"
				}
			},
			{
				"type": "section",
				"text": {
					"type": "plain_text",
					"text": "If you have any images: send to #programming-progress"
				}
			}
			#{
			#	"type": "input",
			#	"optional": true,
			#	"block_id": "input_block_id",
			#	"label": {
			#		"type": "plain_text",
			#		"text": "Upload Images"
			#	},
			#	"element": {
			#		"action_id": "file_input_action_id_1",
			#		"filetypes": [
			#			"jpg",
			#			"png",
			#			"jpeg",
			#			"heic"
			#		],
			#		"max_files": 10
			#	}
			#}
		]
	}
	)
	return res


def outreach_modal(trigger_id, client):
	res = client.views_open(
		trigger_id=trigger_id,
	view={
		"type": "modal",
		"callback_id": "outreach-modal-identifier",
		"submit": {
			"type": "plain_text",
			"text": "Submit"
		},
		"close": {
			"type": "plain_text",
			"text": "Cancel"
		},
		"title": {
			"type": "plain_text",
			"text": "New Outreach Event"
		},
		"blocks": [ 
			{
				"type": "input",
				"element": {
					"type": "plain_text_input",
					"action_id": "plain_text_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Name of outreach"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "datepicker",
					"action_id": "datepicker",
					"placeholder": {
						"type": "plain_text",
						"text": "What Day?"
					},
				},
				"label": {
					"type": "plain_text",
					"text": "Date:"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "multi_users_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Select People"
					},
					"action_id": "multi_users_select-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Which students?"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "number_input",
					"is_decimal_allowed": True,
					"action_id": "number_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "How Many Hours?"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "number_input",
					"is_decimal_allowed": False,
					"action_id": "number_input-action"
				},
				"label": {
					"type": "plain_text",
					"text": "How Many People Affected?"
				}
			},
			{
				"type": "section",
				"text": {
					"type": "plain_text",
					"text": "If you have any images, send them to #outreach-pics!"
				}
			}
		]
	}
	)
	return res


# Command
@app.command("/en")
def handle_command(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	open_modal(trigger_id, client)

@app.command("/outreach")
def handle_command(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	outreach_modal(trigger_id, client)

# Button handler
@app.action("category_action_id")
def handle_some_action(ack, body, logger):
	ack()
	logger.info(body)
 


@app.view("modal-identifier")
def handle_view_submission_events(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	submitted_data = body['view']['state']['values']
	global new_prog_cat_made
	new_prog_cat_made = False
	global new_mech_cat_made
	new_mech_cat_made = False
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'radio_buttons':
				category = action_data['selected_option']['value']
				print(category)
	if category == 'mech':
		mech_categories(trigger_id, client)
	elif category == 'prog':
		prog_categories(trigger_id, client)
	elif category == 'outreach':
		outreach_modal(trigger_id, client)
  



@app.view("outreach-modal-identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	user_id = body['user']['id']
	submitted_data = body['view']['state']['values']
	print(submitted_data)

	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'plain_text_input':
				what_you_did = action_data['value']
	
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'datepicker':
				date = action_data['selected_date']
				
	user_ids = []
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'multi_users_select':
				user_ids = action_data['selected_users']

	user_info = []
	for user_id in user_ids:
		response = client.users_info(user=user_id)
		if response['ok']:
			user_info.append(
				response['user']['real_name']
			)
	
	num_inputs = []
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'number_input':
				num_inputs.append(action_data['value'])
	indiv_hours = num_inputs[0]
	affected = num_inputs[1]

	team_hours = int(len(user_info)) * int(indiv_hours)


	members = ""
	for i in range(len(user_info)):
		members = members + user_info[i] + ","
	submission_data = [what_you_did,date,members,indiv_hours,team_hours,affected]
 	
	outreach_result = outreach_upload(submission_data, client)
	outreach_response(client, outreach_result)
 
@app.view("prog-categories-identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	global p_category
	submitted_data = body['view']['state']['values']
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'static_select':
				p_category = action_data['selected_option']['value']
	prog_modal(trigger_id, client)

# New category button
@app.action("p_button")
def handle_some_action(ack, body, logger, client):
	ack()
	logger.info(body)
	view_id = body["view"]["id"]
	global new_prog_cat_made
	new_prog_cat_made = True
	#new_prog_category(view_id, client)

'''
@app.view("n_prog_cat_identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	submitted_data = body['view']['state']['values']
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'plain_text_input':
				new_cat = action_data['value']
	prog_options = hkl.load('prog_cat')
	new_value = new_cat.lower()
	new_label = new_cat.capitalize()
	new_append = {
					"value": new_value,
					"text": {
						"type": "plain_text",
						"text": new_label
					}
				}
	prog_options.append(new_append)
	hkl.dump(prog_options, 'prog_cat')
	prog_categories(trigger_id, client)
'''
# Entry
@app.view("prog-modal-identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	#print(body)
	user_id = body['user']['id']
	submitted_data = body['view']['state']['values']
	
	# Keeping track of how many entries
	entry_number = hkl.load('entrys')
	entry_number += 1
	hkl.dump(entry_number, 'entrys')

	# Time when entry was submitted
	entry_time = datetime.now(timezone(timedelta(hours=-7)))
	entry_time = entry_time.strftime('%c')

	user_response = client.users_info(user=user_id)
	if user_response['ok']:
		submitting_user = user_response['user']['real_name']

	user_ids = []
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'multi_users_select':
				user_ids = action_data['selected_users']

	user_info = []
	for user_id in user_ids:
		response = client.users_info(user=user_id)
		if response['ok']:
			user_info.append(
				response['user']['real_name']
			)
   
	text_reponses = []
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'plain_text_input':
				text_reponses.append(action_data['value'])
	
	what_you_did = text_reponses[0]
	what_you_learned = text_reponses[1]

	milestone = "no"
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'radio_buttons':
				milestone = action_data['selected_option']['value']
	if milestone == "yes":
		milestone = True
	elif milestone == "no":
		milestone = False
	
	#files = submitted_data['input_block_id']['file_input_action_id_1']['files']
	submission_data = {
		"is_new_project": new_prog_cat_made,
  		"project_name": p_category,
		"category": "programming",
		"entry_id": entry_number,
		"entry_time": entry_time,
		"submitting_user": submitting_user,
		"selected_users": user_info,
		"what_did": what_you_did,
		"what_learned": what_you_learned,
		"milestone": milestone,
		"files": []
	}
	
	
	#for file in files:
	#	file_info = {
	#		"file_name": file['name'],
	#		"file_type": file['filetype'],
	#		"file_url": file['url_private']
	#	}
	#	submission_data["files"].append(file_info)
		
	def convert_sets_to_lists(obj):
		if isinstance(obj, set):
			return list(obj)
		elif isinstance(obj, dict):
			return {k: convert_sets_to_lists(v) for k, v in obj.items()}
		elif isinstance(obj, list):
			return [convert_sets_to_lists(elem) for elem in obj]
		else:
			return obj
	
	submission_data = convert_sets_to_lists(submission_data)
	#existing_data = []

	#if os.path.exists("submission_data.json"):
	#	with open('submission_data.json', 'r') as json_file:
	#		existing_data.clear()
	#		existing_data.append(json.load(json_file))
	#else: 
	#	existing_data = []
	
	#existing_data.append(submission_data)

	#write data to json file
	with open('submission_data.json', 'w') as json_file:
		json.dump(submission_data, json_file, indent = 4)
	
	#Send confirmation message
	send_done_msg(client, submitting_user, entry_time)

	# api
	main()
	send_files = []
	# api worked
	send_confirm_msg(client)
	send_p_update_msg(client, user_info, what_you_did, send_files)
	
 

 
#		  MMM    MMM      
# 		MM  MM MM  MM
#     MM     MM     MM
#   MMM              MMM

# Categories
@app.view("mech-categories-identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	global m_category
	submitted_data = body['view']['state']['values']
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'static_select':
				m_category = action_data['selected_option']['value']
	mech_modal(trigger_id, client)

# New category button
@app.action("m_button")
def handle_some_action(ack, body, logger, client):
	ack()
	logger.info(body)
	view_id = body["view"]["id"]
	global new_mech_cat_made
	new_mech_cat_made = True
	#new_mech_category(view_id, client)
	
'''
# New category function
@app.view("n_mech_cat_identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	submitted_data = body['view']['state']['values']
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'plain_text_input':
				new_cat = action_data['value']
	mech_options = hkl.load('mech_cat')
	new_value = new_cat.lower()
	new_label = new_cat.capitalize()
	new_append = {
					"value": new_value,
					"text": {
						"type": "plain_text",
						"text": new_label
					}
				}
	mech_options.append(new_append)
	hkl.dump(mech_options, 'mech_cat')
	mech_categories(trigger_id, client)
'''

# Entry
@app.view("mech-modal-identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	user_id = body['user']['id']
	submitted_data = body['view']['state']['values']
	
	# Keeping track of how many entries
	entry_number = hkl.load('entrys')
	entry_number += 1
	hkl.dump(entry_number, 'entrys')

	# Time when entry was submitted
	entry_time = datetime.now(timezone(timedelta(hours=-7)))
	entry_time = entry_time.strftime('%c')

	user_response = client.users_info(user=user_id)
	if user_response['ok']:
		submitting_user = user_response['user']['real_name']

	user_ids = []
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'multi_users_select':
				user_ids = action_data['selected_users']

	user_info = []
	for user_id in user_ids:
		response = client.users_info(user=user_id)
		if response['ok']:
			user_info.append(
				response['user']['real_name']
			)       
	
	#category = submitted_data['WYrS1']['static_select-action']['selected_option']['text']['text']
	text_reponses = []
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'plain_text_input':
				text_reponses.append(action_data['value'])
	
	what_you_did = text_reponses[0]
	what_you_learned = text_reponses[1]

	milestone = "no"
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'radio_buttons':
				milestone = action_data['selected_option']['value']
	if milestone == "yes":
		milestone = True
	elif milestone == "no":
		milestone = False
	
	files = submitted_data['input_block_id']['file_input_action_id_1']['files']

	submission_data = {
		"is_new_project": new_mech_cat_made,
  		"project_name": m_category,
		"category": "mechanical",
		"entry_id": entry_number,
		"entry_time": entry_time,
		"submitting_user": submitting_user,
		"selected_users": user_info,
		"what_did": what_you_did,
		"what_learned": what_you_learned,
		"milestone": milestone,
		"files": []
	}
	send_files = []
	for file in files:
		send_files.append(file['url_private'])
	for file in files:
		file_info = {
			"file_name": file['name'],
			"file_url": file['url_private']
		}
		submission_data["files"].append(file_info)
		
	def convert_sets_to_lists(obj):
		if isinstance(obj, set):
			return list(obj)
		elif isinstance(obj, dict):
			return {k: convert_sets_to_lists(v) for k, v in obj.items()}
		elif isinstance(obj, list):
			return [convert_sets_to_lists(elem) for elem in obj]
		else:
			return obj
	
	submission_data = convert_sets_to_lists(submission_data)
	#existing_data = []

	#if os.path.exists("submission_data.json"):
	#	with open('submission_data.json', 'r') as json_file:
	#		existing_data.clear()
	#		existing_data.append(json.load(json_file))
	#else: 
	#	existing_data = []
	
	#existing_data.append(submission_data)

	#write data to json file
	with open('submission_data.json', 'w') as json_file:
		json.dump(submission_data, json_file, indent = 4)
	
	#Send confirmation message
	send_done_msg(client, submitting_user, entry_time)

	# api
	main()
 
	# api worked
	send_confirm_msg(client)
	send_m_update_msg(client, user_info, what_you_did, send_files)
	





# Start your app
if __name__ == "__main__":
	print("hello")
	app.start(port=int(os.environ.get("PORT", 80)))
