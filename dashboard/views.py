from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import adb_client, config_store


def dashboard(request):
    data = config_store.load()
    command_map = {c["id"]: c for c in data["commands"]}
    devices = []
    for device in data["devices"]:
        commands = [command_map[cid] for cid in device["command_ids"] if cid in command_map]
        online = adb_client.check_status(device["ip"], device["port"])
        devices.append({**device, "commands": commands, "online": online})
    return render(request, "dashboard/index.html", {"devices": devices})


@require_POST
def run_command(request, device_id, command_id):
    device = config_store.get_device(device_id)
    command = config_store.get_command(command_id)
    if device is None or command is None:
        return JsonResponse({"ok": False, "error": "Unbekanntes Gerät oder Command"}, status=404)
    result = adb_client.run_command(device["ip"], device["port"], command["cmd"])
    return JsonResponse(result)


def config_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_device":
            config_store.add_device(
                request.POST.get("name", "").strip(),
                request.POST.get("ip", "").strip(),
                int(request.POST.get("port", 5555)),
            )
        elif action == "update_device":
            config_store.update_device(
                request.POST.get("device_id"),
                request.POST.get("name", "").strip(),
                request.POST.get("ip", "").strip(),
                int(request.POST.get("port", 5555)),
            )
        elif action == "delete_device":
            config_store.delete_device(request.POST.get("device_id"))
        elif action == "add_command":
            config_store.add_command(
                request.POST.get("name", "").strip(),
                request.POST.get("cmd", "").strip(),
            )
        elif action == "update_command":
            config_store.update_command(
                request.POST.get("command_id"),
                request.POST.get("name", "").strip(),
                request.POST.get("cmd", "").strip(),
            )
        elif action == "delete_command":
            config_store.delete_command(request.POST.get("command_id"))
        elif action == "assign_command":
            config_store.assign_command(
                request.POST.get("device_id"), request.POST.get("command_id")
            )
        elif action == "unassign_command":
            config_store.unassign_command(
                request.POST.get("device_id"), request.POST.get("command_id")
            )
        return redirect("config")

    data = config_store.load()
    return render(
        request,
        "dashboard/config.html",
        {"devices": data["devices"], "commands": data["commands"]},
    )
