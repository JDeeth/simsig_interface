# pylint: disable=all

import asyncio
import json
from simsig_interface import Connection
from stomp import ConnectionListener
from prompt_toolkit import HTML, print_formatted_text, PromptSession  # type: ignore
from prompt_toolkit.patch_stdout import patch_stdout


async def main():
    session = PromptSession()

    addr_port = await session.prompt_async("Address:Port (default localhost:51515): ")
    addr, _, port = addr_port.partition(":")
    if not addr:
        addr = "localhost"
    if not port:
        port = 51515

    connection = Connection(addr, int(port))

    def sim_time():
        return connection.sim.latest_time.strftime("%H:%M:%S")

    class Listener(ConnectionListener):
        def on_message(self, frame):
            payload = json.loads(frame.body)
            if "clock_msg" in payload:
                return
            for msg_type, message in payload.items():
                disp = [f"{sim_time()} {msg_type}"]
                message.pop("area_id", None)
                message.pop("time", None)
                message.pop("clock", None)
                message.pop("msg_type", None)
                if "obj_id" in message and "obj_type" in message:
                    obj_type = message.pop("obj_type")
                    obj_id = message.pop("obj_id")
                    disp.append(f"{obj_type} {obj_id[1:]}")
                for k, v in message.items():
                    v = f"{v}"
                    if v.lower() == "false":
                        disp.append(f"<ansired>{k}</ansired>")
                    elif v.lower() == "true":
                        disp.append(f"<ansigreen>{k}</ansigreen>")
                    else:
                        disp.append(f"<ansigray>{k}:</ansigray> {v}")
                print_formatted_text(HTML(", ".join(disp)))

    connection.set_stomp_listener("console", Listener())

    def toolbar():
        sim = connection.sim.name or "(not connected)"
        return HTML(f"{sim} {sim_time()} {connection.sim.speed_ratio:.1f}x")

    while True:
        with patch_stdout():
            inpt = await session.prompt_async("> ", bottom_toolbar=toolbar)
        inpt = inpt.lower()

        if inpt == "quit":
            connection.disconnect()
            break
        if inpt == "connect":
            connection.connect()
        if inpt == "disconnect":
            connection.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
