import json

# Initial JSON data
json_command_robot = {
    "robot_type": "j2n6s300",
    "robot_id": 0
}

# Commands to add
cmd = [{"command": 3, "argument_1": "2", "argument_2": "-", "argument_3": "-"},{"command": 2, "argument_1": "2", "argument_2": "-", "argument_3": "-"}]

# Adding commands to json_command_robot
json_command_robot['cmd'] = [cmd_1, cmd_2]

# Convert to JSON string
result_json = json.dumps(json_command_robot, indent=1)

# Print the result
print(result_json)
