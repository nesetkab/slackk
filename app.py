
from pathlib import Path
from dotenv import load_dotenv
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

import json
import os
import hickle as hkl
import datetime
import requests
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
from gsheet import outreach_upload
from upload import main

flask_app = Flask(__name__)
app = App(
	token = os.environ['SLACK_TOKEN'],
	signing_secret = os.environ["SIGNING_SECRET"]
)
handler = SlackRequestHandler(app)

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
	mech_options = hkl.load('mech_cat')
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
					"options": mech_options,
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
					"text": "My category isn't there:"
				},
				"accessory": {
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "New Category"
					},
					"value": "new",
					"action_id": "m_button"
				}
			}
		]
	}
	)
	return res

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
	prog_options = hkl.load('prog_cat')
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
					"options": prog_options,
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
					"text": "My category isn't there: "
				},
				"accessory": {
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "New Category"
					},
					"value": "new",
					"action_id": "p_button"
				}
			}
		]
	}
	)
	return res

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
	new_prog_category(view_id, client)

# New category function
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
	entry_time = datetime.datetime.now()
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
 
	# api worked
	send_confirm_msg(client)
 

 
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
	new_mech_category(view_id, client)

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
	entry_time = datetime.datetime.now()
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
	



# Start your app
if __name__ == "__main__":
	app.start(port=int(os.environ.get("PORT", 5000)))
