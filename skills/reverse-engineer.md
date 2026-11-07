# Skill: Reverse-engineer a feature

Use when the user wants to know how a binary, desktop app, Electron app, .NET assembly, or website
does something, and there is no source code to read.
Not for: reading this project's own code (just read it) or debugging a known error (`fix-bugs.md`).

Tool: [REA](https://github.com/morluto/rea) ("Reverse Engineer Anything"), cloned for reference at
`../SPIDERS/rea` next to this project. It is not installed as an MCP tool in this harness yet — that
needs the user's explicit setup (see Steps).

## What it gives you

REA connects an agent to tools for inspecting native binaries, JavaScript/Electron apps, .NET
assemblies, and websites — locally, without the source. Native (binary) analysis can use an existing
Hopper, Ghidra, or IDA install; static JavaScript/Electron analysis needs none. Every answer comes back
with its evidence (the disassembly, the file, the request) and states what is observation vs.
derivation vs. inference vs. unknown — never a bare claim.

## Steps

1. **Check it's set up.** Look for `rea` registered with the agent (`npx rea-agents setup` has been
   run). If it is not, tell the user what setup needs: Node.js + npm, and — only for native binary
   analysis — one of Hopper/Ghidra/IDA (setup can install Hopper with the user's approval). Static
   JS/Electron and website analysis need none of those. Do not run `rea setup` without asking first;
   it writes config files and can install Hopper.
2. **Scope the question.** Get the exact artifact (binary path, app bundle, URL) and the exact feature
   or behavior to explain. REA inspects what you point it at — vague scope produces vague evidence.
3. **Run the matching analysis** through REA's MCP tools or CLI (same workflows either way):
   native binary -> Ghidra/Hopper/IDA bridge; JS/Electron -> static JS analysis; website -> the web
   adapter. Let REA pick ephemeral/read-only analysis — it does not mutate the target (Ghidra uses
   ephemeral databases, IDA access is read-only, nothing is saved back to the binary).
4. **Read the evidence, not just the conclusion.** REA separates observation (what the bytes/response
   show), derivation (what follows directly), inference (a judgment call), and unknown. Carry that
   distinction into your own report — do not flatten an inference into a stated fact.
5. **If you'll build a version of the feature for the user's own project**, base it on the Evidence
   section, and say explicitly which parts are confirmed vs. inferred.

## Checks

- You named the exact artifact and feature, not "how does this app work" in general.
- Nothing was installed or mutated without the user's approval (REA setup, Hopper install).
- The report to the user carries REA's evidence and uncertainty, not a flattened conclusion.
- If REA needed a provider (Ghidra/Hopper/IDA) that isn't installed, you said so instead of guessing.
