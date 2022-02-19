import json
from protocolInterpreter import actionParser

# https://realpython.com/python-json/
with open("jsonExamples/exampleProtocol.json", "r") as read_file:
    data = json.load(read_file)

    workspace_name = data["workspace"]

    protocol_actions = data["actions"]

    protocol = [actionParser(action) for action in protocol_actions]
