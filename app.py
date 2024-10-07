
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
	#print(body)
	trigger_id = body["trigger_id"]
	res = client.chat_postMessage(
        channel="C07QFDDS9QW",
        text="help"
    )






#       ###   ##     ##
#     ##  ## ##     ##
#    ###### ##     ##
#   ##  ## ###### ######

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




#		  MMM    MMM      
# 		MM  MM MM  MM
#     MM     MM     MM
#   MMM              MMM

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
					"text": "My category isn't there: DM Nes'et for now, currently fixing this"
				}
				#"accessory": {
				#	"type": "button",
				#	"text": {
				#		"type": "plain_text",
				#		"text": "New Category"
				#	},
				#	"value": "new",
				#	"action_id": "button"
				#}
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
					"text": "My category isn't there: DM Nes'et for now, currently fixing this"
				}
				#"accessory": {
				#	"type": "button",
				#	"text": {
				#		"type": "plain_text",
				#		"text": "New Category"
				#	},
				#	"value": "new",
				#	"action_id": "button"
				#}
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
				"type": "section",
				"text": {
					"type": "plain_text",
					"text": "Work In Progress..."
				}
			}
		]})




def outreach_modal_WIP(trigger_id, client):
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
					"text": "What did you do? (One sentence)"
				}
			},
			{
				"type": "input",
				"element": {
					"type": "datepicker",
					"action_id": "odatepicker",
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
					"text": "How Many Members?"
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
				"type": "input",
				"element": {
					"type": "radio_buttons",
					"options": [
						{
							"text": {
								"type": "plain_text",
								"text": "Outreach in FIRST"
							},
							"value": "in_first"
						},
						{
							"text": {
								"type": "plain_text",
								"text": "Outreach in the Community"
							},
							"value": "in_community"
						},
						{
							"text": {
								"type": "plain_text",
								"text": "Outreach in STEM"
							},
							"value": "in_stem"
						}
					],
					"action_id": "radio_buttons-action"
				},
				"label": {
					"type": "plain_text",
					"text": "Category:"
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
	#print(body)
	trigger_id = body["trigger_id"]
	open_modal(trigger_id, client)

@app.command("/outreach")
def handle_command(ack, body, logger, client):
	ack()
	logger.info(body)
	#print(body)
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
	category = body['view']['state']['values']['yfYF5']['category_action_id']['selected_option']['value']
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
 
@app.view("prog-categories-identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	global p_category
	print(body['view']['state']['values'])
	p_category = body['view']['state']['values']['o63/8']['static_select-action']['selected_option']['value']
	prog_modal(trigger_id, client)

# New category button
@app.action("button")
def handle_some_action(ack, body, logger, client):
	ack()
	logger.info(body)
	view_id = body["view"]["id"]
	new_prog_category(view_id, client)

# New category function
@app.view("n_prog_cat_identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	new_cat = body['view']['state']['values']['0LKHC']['plain_text_input-action']['value']
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
	print(submitted_data)
	
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
			user_info.append({
				response['user']['real_name']
			})       
   
	text_reponses = []
	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'plain_text_input':
				text_reponses.append(action_data['value'])
    
	#category = submitted_data['WYrS1']['static_select-action']['selected_option']['text']['text']
	what_you_did = text_reponses[0]
	what_you_learned = text_reponses[1]

	for block_id, block_data in submitted_data.items():
		for action_id, action_data in block_data.items():
			if action_data['type'] == 'radio_buttons':
				milestone = action_data['selected_option']['value']
	
	#files = submitted_data['input_block_id']['file_input_action_id_1']['files']

	submission_data = {
        "subject": "programming",
		"entry_num": entry_number,
		"entry_time": entry_time,
		"submitting_user": submitting_user,
		"selected_users": user_info,
		"category": p_category,
		"what_you_did": what_you_did,
		"what_you_learned": what_you_learned,
		"milestone": milestone
		#"files":[]
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
	existing_data = []

	if os.path.exists("submission_data.json"):
		with open('submission_data.json', 'r') as json_file:
			existing_data.clear()
			existing_data.append(json.load(json_file))
	else: 
		existing_data = []
	
	existing_data.append(submission_data)

	#write data to json file
	with open('submission_data.json', 'w') as json_file:
		json.dump(existing_data, json_file, indent = 4)
	
	#Send confirmation message
	send_done_msg(client, submitting_user, entry_time)
 

 
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
	print(body['view']['state']['values'])
	m_category = body['view']['state']['values']['o9XoE']['static_select-action']['selected_option']['value']
	mech_modal(trigger_id, client)

# New category button
@app.action("button")
def handle_some_action(ack, body, logger, client):
	ack()
	logger.info(body)
	view_id = body["view"]["id"]
	new_mech_category(view_id, client)

# New category function
@app.view("n_mech_cat_identifier")
def handle_view_submission(ack, body, logger, client):
	ack()
	logger.info(body)
	trigger_id = body["trigger_id"]
	new_cat = body['view']['state']['values']['0LKHC']['plain_text_input-action']['value']
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
	#print(body)
	user_id = body['user']['id']
	submitted_data = body['view']['state']['values']
	print(submitted_data)
	
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
			user_info.append({
				response['user']['real_name']
			})       
	
	#category = submitted_data['WYrS1']['static_select-action']['selected_option']['text']['text']
	what_you_did = submitted_data['owACm']['plain_text_input-action']['value']
	what_you_learned = submitted_data['P3QSg']['plain_text_input-action']['value']
	milestone = submitted_data['K/A5J']['radio_buttons-action']['selected_option']['text']['text']
	files = submitted_data['input_block_id']['file_input_action_id_1']['files']

	submission_data = {
		"subject": "mechanical",
		"entry_num": entry_number,
		"entry_time": entry_time,
		"submitting_user": submitting_user,
		"selected_users": user_info,
		"category": m_category,
		"what_you_did": what_you_did,
		"what_you_learned": what_you_learned,
		"milestone": milestone,
		"files":[]
	}
	
	for file in files:
		file_info = {
			"file_name": file['name'],
			"file_type": file['filetype'],
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
	existing_data = []

	if os.path.exists("submission_data.json"):
		with open('submission_data.json', 'r') as json_file:
			existing_data.clear()
			existing_data.append(json.load(json_file))
	else: 
		existing_data = []
	
	existing_data.append(submission_data)

	#write data to json file
	with open('submission_data.json', 'w') as json_file:
		json.dump(existing_data, json_file, indent = 4)
	
	#Send confirmation message
	send_done_msg(client, submitting_user, entry_time)
	



# Start your app
if __name__ == "__main__":
	app.start(port=int(os.environ.get("PORT", 5000)))