# Set up the Unity MCP server

With a Unity MCP server connected, the agent can add scoped registries, install the package, trigger
recompiles, and read the console — so it can install First Look and fix compile errors in one loop.
Without it, the agent writes the code but the user drives Unity by hand and reports errors back.

The recommended server is **CoplayDev Unity MCP**: <https://github.com/CoplayDev/unity-mcp>. It
supports a range of Unity versions and exposes package management (add registry, add package, list
packages), the console, and recompiles.

## Shape of the setup

Follow the repo's README for the exact, current commands and versions — they change between releases,
so prefer the upstream instructions over any hardcoded copy. The setup has four parts:

1. **Install the Unity-side bridge** into the open project (the package the server talks to inside the
   Editor). The repo provides the install method (a Package Manager entry or an installer).
2. **Install and run the MCP server** over **stdio** (the standard transport for a local server the
   client launches itself). stdio means the client starts the server process directly, with no port to
   manage.
3. **Register the server with your AI coding client** — add the server to the client's MCP
   configuration so it launches on start. Use whichever client you run; the repo lists the supported
   ones and the config location for each.
4. **Restart the client** so it picks up the new server and any newly installed skills, then confirm
   the server is connected.

## Verify it works

Before continuing the integration, confirm the server is reachable from the agent:

- List the project's installed packages, or read the Editor console. A successful response means the
  bridge is connected and the active project is the right one.
- If multiple Unity instances are open, make sure the connected one is the project you are integrating.

## What the agent uses it for

- **Add scoped registries** and **install `com.bidmachine.plus`** (see
  [`install.md`](install.md)), including the one-time scoped-registry popup the user closes.
- **List installed packages** to confirm the result and to check whether External Dependency Manager
  is already present.
- **Read the console** after each change to catch duplicate-assembly errors and compile failures, and
  **trigger a recompile** to re-check after a fix.

If the user declines MCP, fall back to the manual path: the agent writes the C# code and gives the
user exact Editor-UI steps to add the two registries and install the package (editing
`Packages/manifest.json` directly only if the user prefers that). The user installs, closes the
scoped-registry popup, and reports console output. Call out that, without the console, the agent
cannot verify the install or fix compile errors in the same loop.
