import hickle as hkl
prog_options = [hkl.load('prog_cat')]

new_append = {
	"value": "roadrunner",
	"text": {
		"type": "plain_text",
		"text": "Roadrunner"
	}
}
prog_options.append(new_append)
hkl.dump(prog_options, 'prog_cat')
