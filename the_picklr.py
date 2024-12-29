import hickle as hkl
prog_options = hkl.load('mech_cat')

new_append = {
	"value": "Drivetrain",
	"text": {
		"type": "plain_text",
		"text": "drivetrain"
	}
}
prog_options.append(new_append)
hkl.dump(prog_options, 'mech_cat')
