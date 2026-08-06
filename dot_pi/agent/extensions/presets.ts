import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import {
  getAgentDir,
  type ExtensionAPI,
  type ExtensionContext,
} from "@earendil-works/pi-coding-agent";

type ThinkingLevel = "off" | "minimal" | "low" | "medium" | "high" | "xhigh" | "max";

type Preset = {
  thinkingLevel?: ThinkingLevel;
  tools?: string[];
  instructions?: string;
};

type Presets = Record<string, Preset>;

const WORKFLOW_PRESETS: Record<string, string> = {
  investigate: "investigate",
  ship: "ship",
  audit: "audit",
  deadline: "deadline",
  finish: "ship",
};

function readPresets(): Presets {
  const path = join(getAgentDir(), "presets.json");
  if (!existsSync(path)) return {};
  const value = JSON.parse(readFileSync(path, "utf8")) as unknown;
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${path} must contain a JSON object`);
  }
  return value as Presets;
}

function readWorkflow(name: string, args: string): string {
  const path = join(getAgentDir(), "workflows", `${name}.md`);
  const template = readFileSync(path, "utf8").trim();
  const input = args.trim();
  return template
    .replaceAll("$ARGUMENTS", input)
    .replaceAll("$@", input)
    .replaceAll("${ARGUMENTS}", input);
}

export default function presetWorkflows(pi: ExtensionAPI) {
  let presets: Presets = {};
  let activeName: string | undefined;
  let activePreset: Preset | undefined;
  let baselineTools: string[] = [];
  let baselineThinking: ThinkingLevel = "high";

  function setStatus(ctx: ExtensionContext): void {
    ctx.ui.setStatus(
      "workflow-preset",
      activeName ? ctx.ui.theme.fg("accent", `mode:${activeName}`) : undefined,
    );
  }

  function applyPreset(
    name: string,
    ctx: ExtensionContext,
    options: { persist: boolean; notify: boolean },
  ): boolean {
    const preset = presets[name];
    if (!preset) return false;

    if (preset.thinkingLevel) pi.setThinkingLevel(preset.thinkingLevel);
    if (preset.tools?.length) {
      const available = new Set(pi.getAllTools().map((tool) => tool.name));
      const enabled = preset.tools.filter((tool) => available.has(tool));
      const missing = preset.tools.filter((tool) => !available.has(tool));
      if (enabled.length) pi.setActiveTools(enabled);
      if (missing.length && options.notify) {
        ctx.ui.notify(`Mode ${name}: unavailable tools: ${missing.join(", ")}`, "warning");
      }
    }

    activeName = name;
    activePreset = preset;
    if (options.persist) pi.appendEntry("workflow-preset", { name });
    setStatus(ctx);
    if (options.notify) ctx.ui.notify(`Mode set to ${name}`, "info");
    return true;
  }

  function clearPreset(ctx: ExtensionContext, persist: boolean): void {
    activeName = undefined;
    activePreset = undefined;
    pi.setThinkingLevel(baselineThinking);
    if (baselineTools.length) pi.setActiveTools(baselineTools);
    if (persist) pi.appendEntry("workflow-preset", { name: "off" });
    setStatus(ctx);
    ctx.ui.notify("Workflow mode cleared", "info");
  }

  async function deliverWorkflow(name: string, args: string, ctx: ExtensionContext): Promise<void> {
    const presetName = WORKFLOW_PRESETS[name];
    if (!applyPreset(presetName, ctx, { persist: true, notify: true })) {
      ctx.ui.notify(`Preset ${presetName} is not configured`, "error");
      return;
    }
    if (!args.trim() && name !== "finish") return;

    let prompt: string;
    try {
      prompt = readWorkflow(name, args);
    } catch (error) {
      ctx.ui.notify(`Cannot load workflow ${name}: ${String(error)}`, "error");
      return;
    }

    if (ctx.isIdle()) pi.sendUserMessage(prompt);
    else pi.sendUserMessage(prompt, { deliverAs: "followUp" });
  }

  pi.registerFlag("preset", {
    description: "Start in a workflow mode: investigate, ship, audit, or deadline",
    type: "string",
  });

  pi.registerCommand("preset", {
    description: "Select a persistent workflow mode",
    getArgumentCompletions: (prefix) =>
      [...Object.keys(presets), "off"]
        .filter((name) => name.startsWith(prefix))
        .map((name) => ({ value: name, label: name })),
    handler: async (args, ctx) => {
      let name = args.trim();
      if (!name && ctx.hasUI) {
        name = (await ctx.ui.select("Workflow mode", [...Object.keys(presets), "off"])) ?? "";
      }
      if (!name) return;
      if (name === "off") {
        clearPreset(ctx, true);
        return;
      }
      if (!applyPreset(name, ctx, { persist: true, notify: true })) {
        ctx.ui.notify(`Unknown mode ${name}`, "error");
      }
    },
  });

  for (const name of Object.keys(WORKFLOW_PRESETS)) {
    pi.registerCommand(name, {
      description:
        name === "finish"
          ? "Verify the current work and report readiness without committing"
          : `Run the ${name} workflow (or switch mode when called without a task)`,
      handler: (args, ctx) => deliverWorkflow(name, args, ctx),
    });
  }

  pi.on("before_agent_start", (event) => {
    if (!activePreset?.instructions) return;
    return { systemPrompt: `${event.systemPrompt}\n\n${activePreset.instructions}` };
  });

  pi.on("session_start", (_event, ctx) => {
    presets = readPresets();
    baselineTools = pi.getActiveTools();
    baselineThinking = pi.getThinkingLevel();

    const requested = pi.getFlag("preset");
    let restored = typeof requested === "string" ? requested : undefined;
    if (!restored) {
      for (const entry of ctx.sessionManager.getEntries()) {
        if (entry.type !== "custom" || entry.customType !== "workflow-preset") continue;
        const name = (entry.data as { name?: unknown } | undefined)?.name;
        if (typeof name === "string") restored = name;
      }
    }

    if (restored && restored !== "off") {
      if (!applyPreset(restored, ctx, { persist: false, notify: false })) {
        ctx.ui.notify(`Saved workflow mode ${restored} no longer exists`, "warning");
      }
    } else {
      setStatus(ctx);
    }
  });
}
