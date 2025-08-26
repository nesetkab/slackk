import psycopg2
from configparser import ConfigParser
import json

# variables-----------------------------------------------------------------------------------

tables = ["entries", "img", "projects", "status_", "tags", "users"]
relations = [
    ["entries", "entry_author", "users"],
    ["entries", "entry_tags", "tags"],
    ["entries", "entry_imgs", "img"],
    ["projects", "project_entries", "entries"],
    ["projects", "project_tags", "tags"],
    ["projects", "project_status", "status_"],
]


# function------------------------------------------------------------------------------------
def connect(config):
    try:
        print("connecting to server...")
        with psycopg2.connect(**config) as conn:
            print("connected to the postgresql server")
            return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)


def load_config(filename="database.ini", section="postgresql"):
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to postgresql
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception(
            "Section {0} not found in the {1} file".format(section, filename)
        )

    return config


def pull_data(conn, table):
    cur = conn.cursor()
    command = f"SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{table}';"
    cur.execute(command)
    return cur.fetchall()


def clean_tuple(tuple):
    if type(tuple) in [type([]), type(())]:
        tuple = str(tuple)
        for c in [
            ["'(", "("],
            ["None", "'empty'"],
            [",)", ")"],
            ["(", ""],
            [")", ""],
            [",,", ","],
            [",]", "]"],
            ["'", '"'],
            ["False", "false"],
            ["True", "true"],
            ['}"', "}"],
            ["{", '{"'],
            ["}", '"}'],
        ]:
            tuple = tuple.replace(c[0], c[1])
        return json.loads(tuple)
    else:
        return tuple


def clean_design(tuple):
    if type(tuple) in [type([]), type(()), type({})]:
        tuple = str(tuple)
        for c in [
            ["'(", "("],
            ["None", "'empty'"],
            [",)", ")"],
            ["(", ""],
            [")", ""],
            [",,", ","],
            [",]", "]"],
            ["'", '"'],
            ["False", "false"],
            ["True", "true"],
            ['}"', "}"],
            ["{", '{"'],
            ["}", '"}'],
        ]:
            tuple = tuple.replace(c[0], c[1])
        return tuple
    else:
        return tuple


def get_columns(conn):
    cur = conn.cursor()
    columns = {}
    connections = {}
    for t in tables:
        columns[t] = {}
        for c in pull_data(conn, t):
            cur.execute(f"select {clean_tuple(c)} from {t};")
            columns[t][clean_tuple(c)] = cur.fetchall()
    for t in relations:
        connections[t[1]] = {}
        for c in pull_data(conn, clean_tuple(t[1])):
            cur.execute(f"select {clean_tuple(c)} from {t[1]};")
            connections[t[1]][clean_tuple(c)] = cur.fetchall()
    return columns, connections


def pull_row(row, table, conn):
    cur = conn.cursor()
    for c in ["[", "]", "'"]:
        row = row.replace(c, "")
    cur.execute(f"SELECT {row} FROM {table}")
    return cur.fetchall()


def get_data_struct(conn):
    columns, connections = get_columns(conn)
    for column in columns:
        for row in columns[column]:
            columns[column][row] = pull_row(row, column, conn)
    for column in connections:
        for row in connections[column]:
            connections[column][row] = pull_row(row, column, conn)
    return columns, connections


def get_data(data, data2, conn):
    entries = []
    imgs = []
    projects = []
    users = []
    for t in tables:
        match t:
            case "entries":
                entries.append(
                    clean_tuple(
                        [
                            data[t]["entry_id"],
                            data[t]["entry_data"],
                            data2["entry_imgs"]["img_ids"],
                            data2["entry_author"]["user_names"],
                            data2["entry_tags"]["tags"],
                            data[t]["is_milestone"],
                            data2["entry_author"]["creator_name"],
                        ]
                    )
                )
            case "img":
                imgs.append(
                    clean_tuple(
                        [data[t]["img_id"], data[t]["img_name"], data[t]["img_data"]]
                    )
                )
            case "projects":
                projects.append(
                    clean_tuple(
                        [
                            data[t]["project_id"],
                            data[t]["project_name"],
                            data2["project_status"]["status_"],
                            data2["project_tags"]["tags"],
                            data2["project_entries"]["entry_ids"],
                        ]
                    )
                )
            case "users":
                users.append(
                    clean_tuple(
                        [
                            data[t]["user_id"],
                            data[t]["user_name"],
                            data[t]["user_password"],
                        ]
                    )
                )
    return entries, imgs, projects, users


def getImages(id, images):
    imgs = []
    if len(images[0][0]) != 0 and id != "empty":
        for e in id:
            if e in images[0][0]:
                imgs += [[images[0][1][e - 1], images[0][2][e - 1]]]
    return imgs


def gen_json(data, data2, conn):
    final_json = ""
    entries, imgs, projects, users = get_data(data, data2, conn)

    new_projects = []

    for i in range(len(data["projects"]["project_id"])):
        temp_project = []
        for p in projects[0]:
            temp_project.append(p[i])
        new_projects.append(temp_project)

    for p in new_projects:
        project_entries = ""
        for e in entries:
            if p[4] != "empty":
                for i in range(len(e[0])):
                    if e[0][i] in p[4]:
                        project_entries += (
                            f'"{e[0][i]}":'
                            + str(
                                entry_json(
                                    e[0][i],
                                    e[1][i],
                                    getImages(e[2][i], imgs),
                                    e[3][i],
                                    e[4][i],
                                    str(e[5][i]).lower(),
                                    e[6][i],
                                )
                            )
                            + ","
                        )

        project_entries = clean_tuple(project_entries)

        if project_entries != "":
            project_entries = "{" + project_entries[:-1] + "}"
            project_entries = json.loads(project_entries.replace("'", '"'))
            final_json += (
                '"'
                + str(p[0])
                + '"'
                + ":"
                + str(project_json(p[0], p[1], p[3], p[2], project_entries)).replace(
                    "'", '"'
                )
                + ","
            )

    return clean_tuple("{" + final_json[:-1] + "}")


def convertArray(string):
    array = "{" + string + "}"
    replacements = [["{", '{"'], [",", '","'], ["}", '"}']]
    for i in replacements:
        array = array.replace(i[0], i[1])
    return json.dumps(array)


def enterData(data, conn):
    with open(data, "r") as f:
        try:
            data_json = json.loads(f.read())
        except:
            data_json = json.loads(json.dumps(data))

    cur = conn.cursor()

    if data_json["is_new_project"]:
        command = "SELECT create_project(%s::text, array[%s::text]);"
        cur.execute(command, (data_json["project_name"], data_json["category"]))

    conn.commit()

    for u in range(len(data_json["selected_users"])):
        user = data_json["selected_users"][u]
        command = "SELECT add_user(%s, 'pass');"
        cur.execute(command, (user,))

    conn.commit()

    command = "SELECT create_entry(%s::text,%s::text[],array[%s::text],%s::text[],%s::text[],%s::text,%s);"
    selected_users_str = convertArray(",".join(data_json["selected_users"]))
    files_str = [list(f.values()) for f in data_json["files"]]
    what_did_next_str = json.loads(
        str([data_json["what_did"], data_json["what_next"]]).replace("'", '"')
    )

    cur.execute(
        command,
        (
            data_json["submitting_user"],
            json.loads(selected_users_str),
            (data_json["category"]),
            files_str,
            what_did_next_str,
            data_json["project_name"],
            data_json["milestone"],
        ),
    )

    conn.commit()
    cur.close()


def design_enter(conn, data):
    with open(data, "r") as f:
        data = json.loads(f.read())
    cur = conn.cursor()
    command = "SELECT create_design_entry(%s::text,%s::text,%s::text[],%s::text[]);"
    cur.execute(
        command, (data["name"], data["description"], data["tags"], data["links"])
    )
    conn.commit()
    cur.close()


def pull_design_info(conn):
    cur = conn.cursor()
    command = "SELECT (design_id,name,description,data,tags) FROM design_entry"
    cur.execute(command)
    data = cur.fetchall()
    return clean_design(data)


def filter_data(data, tags):
    entries = {}
    try:
        data = json.loads(data)
    except:
        print("data was not in correct json format")
        return 1
    for project in data:
        for entry in data[project]["entries"]:
            for t in tags:
                if t in data[project]["entries"][str(entry)]["tags"]:
                    entries[str(entry)] = {
                        "project": data[project]["name"],
                        "entry": data[project]["entries"][str(entry)],
                    }
    entries = str(entries).replace("'", '"')
    return clean_tuple(entries)


def extract_json(conn):
    main_tables, relate_tables = get_data_struct(conn)
    json1 = gen_json(main_tables, relate_tables, conn)
    return json1


# JSON -----------------------------------------------------


def project_json(id, name, tags, status, entries):
    return {
        "name": name,  # project name
        "id": id,
        "tags": tags,
        "status": status,
        "entries": entries,
    }


def entry_json(id, data, images, users, tags, milestone, creator):
    return {
        "id": id,
        "creator": creator,
        "users": users,
        "images": images,
        "data": data,
        "tags": tags,
        "milestone": milestone,
    }
