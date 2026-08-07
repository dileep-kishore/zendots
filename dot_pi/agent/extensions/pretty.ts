import type { AssistantMessage } from "@earendil-works/pi-ai";
import {
  CustomEditor,
  type ExtensionAPI,
  type ExtensionContext,
  type KeybindingsManager,
} from "@earendil-works/pi-coding-agent";
import type { Component, EditorTheme, TUI } from "@earendil-works/pi-tui";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

const SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

function fitBorder(
  left: string,
  right: string,
  width: number,
  color: (text: string) => string,
): string {
  if (width <= 0) return "";
  if (width === 1) return color("─");

  while (visibleWidth(left) + visibleWidth(right) + 5 > width && visibleWidth(right)) {
    right = truncateToWidth(right, visibleWidth(right) - 1, "");
  }
  while (visibleWidth(left) + visibleWidth(right) + 5 > width && visibleWidth(left)) {
    left = truncateToWidth(left, visibleWidth(left) - 1, "");
  }

  const gap = "─".repeat(Math.max(1, width - visibleWidth(left) - visibleWidth(right) - 2));
  return `${color("─")}${left}${color(gap)}${right}${color("─")}`;
}

function shortPath(path: string): string {
  const home = process.env.HOME;
  return home && (path === home || path.startsWith(`${home}/`)) ? `~${path.slice(home.length)}` : path;
}

function compactNumber(value: number): string {
  return value < 1_000 ? `${value}` : `${(value / 1_000).toFixed(1)}k`;
}

function usage(ctx: ExtensionContext): string {
  let input = 0;
  let output = 0;
  let cost = 0;

  // ponytail: a branch scan keeps this extension stateless; cache if huge sessions make rendering measurable.
  for (const entry of ctx.sessionManager.getBranch()) {
    if (entry.type !== "message" || entry.message.role !== "assistant") continue;
    const message = entry.message as AssistantMessage;
    input += message.usage.input ?? 0;
    output += message.usage.output ?? 0;
    cost += message.usage.cost.total ?? 0;
  }

  return ` ↑${compactNumber(input)} ↓${compactNumber(output)}${cost ? ` · $${cost.toFixed(2)}` : ""} `;
}

function contextUsage(ctx: ExtensionContext): string {
  const current = ctx.getContextUsage();
  const window = current?.contextWindow ?? ctx.model?.contextWindow;
  return current?.percent !== null && current?.percent !== undefined && window
    ? `${Math.round(current.percent)}%/${compactNumber(window)}`
    : "ctx ?";
}

function workflowMode(ctx: ExtensionContext): string | undefined {
  for (const entry of ctx.sessionManager.getEntries().toReversed()) {
    if (entry.type !== "custom" || entry.customType !== "workflow-preset") continue;
    const name = (entry.data as { name?: unknown } | undefined)?.name;
    return typeof name === "string" && name !== "off" ? name : undefined;
  }
}

class EmptyFooter implements Component {
  render(): string[] {
    return [];
  }
  invalidate(): void {}
}

export default function pretty(pi: ExtensionAPI) {
  let working = false;
  let spinner = 0;
  let timer: ReturnType<typeof setInterval> | undefined;
  let tui: TUI | undefined;
  let branch: string | undefined;

  const stopSpinner = () => {
    if (timer) clearInterval(timer);
    timer = undefined;
  };

  const refreshBranch = async (ctx: ExtensionContext) => {
    const result = await pi.exec("git", ["branch", "--show-current"], { cwd: ctx.cwd }).catch(() => undefined);
    branch = result?.stdout.trim() || undefined;
    tui?.requestRender();
  };

  pi.on("agent_start", () => {
    working = true;
    stopSpinner();
    timer = setInterval(() => {
      spinner = (spinner + 1) % SPINNER.length;
      tui?.requestRender();
    }, 80);
  });

  pi.on("agent_end", () => {
    working = false;
    stopSpinner();
    tui?.requestRender();
  });

  pi.on("turn_end", (_event, ctx) => void refreshBranch(ctx));
  pi.on("session_shutdown", () => {
    stopSpinner();
    tui = undefined;
  });

  pi.on("session_start", (_event, ctx) => {
    if (ctx.mode !== "tui") return;

    ctx.ui.setTitle(`pi · ${ctx.cwd.split("/").pop() || ctx.cwd}`);
    ctx.ui.setWorkingVisible(false);
    ctx.ui.setFooter(() => new EmptyFooter());
    void refreshBranch(ctx);

    class PrettyEditor extends CustomEditor {
      constructor(instance: TUI, theme: EditorTheme, keybindings: KeybindingsManager) {
        super(instance, theme, keybindings, { paddingX: 0 });
        tui = instance;
      }

      render(width: number): string[] {
        const lines = super.render(width);
        if (lines.length < 2) return lines;

        const theme = ctx.ui.theme;
        const mode = workflowMode(ctx);
        const session = pi.getSessionName();
        const identity = ` π${session ? ` · ${session}` : ""}${mode ? ` · ${mode}` : ""} `;
        const activity = working ? ` ${SPINNER[spinner]} working ` : identity;
        const model = ctx.model ? `${ctx.model.provider}/${ctx.model.id}` : "no model";
        const location = `${contextUsage(ctx)} · ${shortPath(ctx.cwd)}${branch ? ` · ${branch}` : ""}`;
        const border = (text: string) => this.borderColor(text);

        lines[0] = fitBorder(
          working ? theme.fg("accent", activity) : theme.fg("muted", activity),
          theme.fg("dim", usage(ctx)),
          width,
          border,
        );
        lines[lines.length - 1] = fitBorder(
          theme.fg("muted", ` ${model} · ${pi.getThinkingLevel()} `),
          theme.fg("dim", ` ${location} `),
          width,
          border,
        );
        return lines;
      }
    }

    ctx.ui.setEditorComponent((instance, theme, keybindings) => new PrettyEditor(instance, theme, keybindings));
  });
}
