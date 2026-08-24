import argparse
import json
import os
import random
import socket
import subprocess
import sys
import tempfile
import time


IAC = 0xFF
CMD_WILL = 0xFB
CMD_WONT = 0xFC
CMD_DO = 0xFD
CMD_DONT = 0xFE
CMD_SB = 0xFA
CMD_SE = 0xF0

DEFAULT_REPL = "platforms/boards/renesas-ck_ra6m5.repl"
DEFAULT_UART = "sysbus.sci0"


def strip_telnet(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        b = data[i]
        if b != IAC:
            out.append(b)
            i += 1
            continue
        if i + 1 >= len(data):
            break
        cmd = data[i + 1]
        if cmd == IAC:
            out.append(IAC)
            i += 2
        elif cmd in (CMD_WILL, CMD_WONT, CMD_DO, CMD_DONT):
            i += 3
        elif cmd == CMD_SB:
            end = data.find(bytes([IAC, CMD_SE]), i + 2)
            if end == -1:
                break
            i = end + 2
        else:
            i += 2
    return bytes(out)


def negotiate(first: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(first):
        if first[i] != IAC:
            i += 1
            continue
        if i + 1 >= len(first):
            break
        cmd = first[i + 1]
        opt = first[i + 2] if i + 2 < len(first) else 0
        if cmd == CMD_WILL:
            out.extend([IAC, CMD_DO, opt])
            i += 3
        elif cmd == CMD_DO:
            out.extend([IAC, CMD_WILL, opt])
            i += 3
        else:
            i += 2
    return bytes(out)


def load_platform(elf_path):
    """Mirror how the backend resolves the board, so a local `make test` and
    the hosted simulator agree on what they are running."""
    cfg = {"platform_repl": DEFAULT_REPL, "uart_peripheral": DEFAULT_UART}
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(elf_path)), "platform.json")
    if os.path.isfile(config_path):
        try:
            with open(config_path) as f:
                cfg.update(json.load(f))
        except (OSError, ValueError):
            pass
    repl = cfg.get("platform_repl") or DEFAULT_REPL
    # A repo-relative .repl only counts if it is actually there; otherwise fall
    # back to the board shipped with Renode, which is what the backend does.
    if not os.path.isabs(repl):
        local = os.path.join(os.path.dirname(os.path.abspath(elf_path)), repl)
        repl = local if os.path.isfile(local) else DEFAULT_REPL
    return repl, cfg.get("uart_peripheral") or DEFAULT_UART


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--elf", required=True)
    # No default: an unset --expected means "any UART output passes". The
    # check exists to catch firmware that runs and says nothing, not to
    # police what a student prints.
    parser.add_argument("--expected", default=None)
    parser.add_argument("--renode-bin",
                        default=os.environ.get("RENODE_BIN", "renode"))
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--settle", type=float, default=2.0,
                        help="seconds to keep reading before accepting output")
    args = parser.parse_args()

    port = args.port or random.randint(20000, 40000)
    elf = os.path.abspath(args.elf)
    repl, uart = load_platform(args.elf)
    print(f"platform: {repl}\nuart: {uart}")

    with tempfile.TemporaryDirectory() as tmp:
        resc = os.path.join(tmp, "test.resc")
        with open(resc, "w") as f:
            f.write(
                'using sysbus\n'
                'mach create "test"\n'
                f'machine LoadPlatformDescription @{repl}\n'
                f'emulation CreateServerSocketTerminal {port} "uart"\n'
                f'connector Connect {uart} uart\n'
                f'sysbus LoadELF @{elf}\n'
                'start\n'
            )

        proc = subprocess.Popen(
            [args.renode_bin, "--disable-xwt", "--console",
             "-e", f'include @{resc}'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        try:
            deadline = time.time() + args.timeout
            sock = None
            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                try:
                    sock = socket.create_connection(("127.0.0.1", port), timeout=1)
                    break
                except OSError:
                    time.sleep(0.2)

            if sock is None:
                output, _ = proc.communicate(timeout=5)
                print(output.decode(errors="replace"))
                raise SystemExit(
                    "renode did not open the UART socket or exited early")

            buf = b""
            with sock:
                sock.settimeout(1)
                first = b""
                while time.time() < deadline:
                    try:
                        first = sock.recv(4096)
                    except socket.timeout:
                        continue
                    if first:
                        break
                if not first:
                    print("FAIL: no data from Renode")
                    return 1
                neg = negotiate(first)
                if neg:
                    sock.sendall(neg)
                buf = strip_telnet(first)
                # With no expected string, give the firmware a moment to finish
                # its line rather than passing on the first byte -- the point is
                # to report what it said, not merely that it said something.
                settle = time.time() + args.settle
                while time.time() < deadline:
                    if args.expected is None and time.time() > settle and buf.strip():
                        break
                    try:
                        data = sock.recv(4096)
                    except socket.timeout:
                        if args.expected is None and buf.strip():
                            break
                        continue
                    if not data:
                        break
                    buf += strip_telnet(data)
                    if args.expected is not None and args.expected.encode() in buf:
                        print(f"PASS: found {args.expected!r} on the UART")
                        return 0
                if args.expected is None and buf.strip():
                    shown = buf.decode(errors="replace").strip()
                    print(f"PASS: firmware produced UART output: {shown!r}")
                    return 0
            if args.expected is None:
                print("FAIL: firmware ran but produced no UART output at all. "
                      "It compiled, so check that main() reaches your uart_puts "
                      "call and that the transmit-ready flag is declared volatile.")
            else:
                print(f"FAIL: expected {args.expected!r} "
                      f"but the UART only produced {buf!r}")
            return 1
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    sys.exit(main())
