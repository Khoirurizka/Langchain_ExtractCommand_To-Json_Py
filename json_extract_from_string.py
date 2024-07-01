import json
import re

# Original message string
message = """
Here is the response using the JSON templates:

json_for_answer_user = {
'message': 'The ball is under cup 2.'}

json_command_robot = {
'robot_type': 'j2n6s300',
'robot_id': 0,
'command': 0,
'argument_1': '-',
'argument_2': '-',
'argument_3': '-'}
"""

# Regular expressions to extract JSON strings
json_user_pattern = re.compile(r'json_for_answer_user\s*=\s*({.*?})', re.DOTALL)
json_robot_pattern = re.compile(r'json_command_robot\s*=\s*({.*?})', re.DOTALL)

# Extract JSON strings
json_user_match = json_user_pattern.search(message)
json_robot_match = json_robot_pattern.search(message)

if json_user_match and json_robot_match:
    json_for_answer_user = json.loads(json_user_match.group(1).replace("'", '"'))
    json_command_robot = json.loads(json_robot_match.group(1).replace("'", '"'))
else:
    raise ValueError("JSON objects not found in the message string")

# Print extracted JSON objects
print(json_for_answer_user)
print(json_command_robot)

