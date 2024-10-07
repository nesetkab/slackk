import hickle as hkl
prog_options = hkl.load('prog_cat')
print(prog_options)
prog_options = [{
					"value": "limelight",
					"text": {
						"type": "plain_text",
						"text": "Limelight"
					}
				},
                {
					"value": "roadrunner",
					"text": {
						"type": "plain_text",
						"text": "Roadrunner"
					}
				}
]
hkl.dump(prog_options, 'prog_cat')