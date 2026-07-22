import json
import uuid
from pathlib import Path
from threading import Lock

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

_lock = Lock()


def load():
    if not CONFIG_PATH.exists():
        return {"devices": [], "commands": []}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    tmp_path = CONFIG_PATH.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp_path.replace(CONFIG_PATH)


def _update(mutator):
    """Load data, apply mutator(data) under the lock, save, and return mutator's result."""
    with _lock:
        data = load()
        result = mutator(data)
        save(data)
        return result


def get_device(device_id):
    data = load()
    return next((d for d in data["devices"] if d["id"] == device_id), None)


def get_command(command_id):
    data = load()
    return next((c for c in data["commands"] if c["id"] == command_id), None)


def get_device_commands(device_id):
    data = load()
    device = next((d for d in data["devices"] if d["id"] == device_id), None)
    if device is None:
        return []
    command_map = {c["id"]: c for c in data["commands"]}
    return [command_map[cid] for cid in device["command_ids"] if cid in command_map]


def add_device(name, ip, port):
    def mutate(data):
        device = {
            "id": str(uuid.uuid4()),
            "name": name,
            "ip": ip,
            "port": port,
            "command_ids": [],
        }
        data["devices"].append(device)
        return device

    return _update(mutate)


def update_device(device_id, name, ip, port):
    def mutate(data):
        for device in data["devices"]:
            if device["id"] == device_id:
                device["name"] = name
                device["ip"] = ip
                device["port"] = port
                return device
        raise KeyError(f"Device {device_id} not found")

    return _update(mutate)


def delete_device(device_id):
    def mutate(data):
        data["devices"] = [d for d in data["devices"] if d["id"] != device_id]

    return _update(mutate)


def add_command(name, cmd):
    def mutate(data):
        command = {"id": str(uuid.uuid4()), "name": name, "cmd": cmd}
        data["commands"].append(command)
        return command

    return _update(mutate)


def update_command(command_id, name, cmd):
    def mutate(data):
        for command in data["commands"]:
            if command["id"] == command_id:
                command["name"] = name
                command["cmd"] = cmd
                return command
        raise KeyError(f"Command {command_id} not found")

    return _update(mutate)


def delete_command(command_id):
    def mutate(data):
        data["commands"] = [c for c in data["commands"] if c["id"] != command_id]
        for device in data["devices"]:
            device["command_ids"] = [cid for cid in device["command_ids"] if cid != command_id]

    return _update(mutate)


def assign_command(device_id, command_id):
    def mutate(data):
        for device in data["devices"]:
            if device["id"] == device_id:
                if command_id not in device["command_ids"]:
                    device["command_ids"].append(command_id)
                return device
        raise KeyError(f"Device {device_id} not found")

    return _update(mutate)


def unassign_command(device_id, command_id):
    def mutate(data):
        for device in data["devices"]:
            if device["id"] == device_id:
                device["command_ids"] = [cid for cid in device["command_ids"] if cid != command_id]
                return device
        raise KeyError(f"Device {device_id} not found")

    return _update(mutate)
