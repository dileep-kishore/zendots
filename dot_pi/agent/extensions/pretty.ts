import type { AssistantMessage } from "@earendil-works/pi-ai";
import {
  CustomEditor,
  type ExtensionAPI,
  type ExtensionContext,
  type KeybindingsManager,
} from "@earendil-works/pi-coding-agent";
import type { EditorTheme, TUI } from "@earendil-works/pi-tui";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

const SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
const BAR_WIDTH = 12;

type Totals = { input: number; output: number; cacheRead: number; cacheWrite: number; cost: number };
type GitStat = {
  added: number;
  removed: number;
  staged: number;
  unstaged: number;
  untracked: number;
  ahead: number;
  behind: number;
};

function fitBorder(left: string, width: number, color: (text: string) => string): string {
  if (width <= 0) return "";
  if (width === 1) return color("─");
  left = truncateToWidth(left, Math.max(0, width - 2), "");
  return `${color("─")}${left}${color("─".repeat(Math.max(1, width - visibleWidth(left) - 2)))}${color("─")}`;
}

function fitLine(left: string, right: string, width: number): string {
  if (width <= 0) return "";
  if (!right) return truncateToWidth(left, width, "");

  right = truncateToWidth(right, Math.min(visibleWidth(right), Math.floor(width * 0.45)), "");
  left = truncateToWidth(left, Math.max(0, width - visibleWidth(right) - 1), "");
  const gap = " ".repeat(Math.max(1, width - visibleWidth(left) - visibleWidth(right)));
  return truncateToWidth(`${left}${gap}${right}`, width, "");
}

function compactNumber(value: number): string {
  if (value < 1_000) return `${value}`;
  if (value < 1_000_000) return `${(value / 1_000).toFixed(1)}k`;
  return `${(value / 1_000_000).toFixed(1)}M`;
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1_000);
  return `${Math.floor(totalSeconds / 60)}m ${totalSeconds % 60}s`;
}

function totals(ctx: ExtensionContext): Totals {
  const result: Totals = { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, cost: 0 };

  // ponytail: a branch scan keeps this extension stateless; cache if huge sessions make rendering measurable.
  for (const entry of ctx.sessionManager.getBranch()) {
    if (entry.type !== "message" || entry.message.role !== "assistant") continue;
    const message = entry.message as AssistantMessage;
    result.input += message.usage.input ?? 0;
    result.output += message.usage.output ?? 0;
    result.cacheRead += message.usage.cacheRead ?? 0;
    result.cacheWrite += message.usage.cacheWrite ?? 0;
    result.cost += message.usage.cost.total ?? 0;
  }
  return result;
}

function workflowMode(ctx: ExtensionContext): string | undefined {
  for (const entry of ctx.sessionManager.getEntries().toReversed()) {
    if (entry.type !== "custom" || entry.customType !== "workflow-preset") continue;
    const name = (entry.data as { name?: unknown } | undefined)?.name;
    return typeof name === "string" && name !== "off" ? name : undefined;
  }
}

export default function pretty(pi: ExtensionAPI) {
  let working = false;
  let spinner = 0;
  let timer: ReturnType<typeof setInterval> | undefined;
  let tui: TUI | undefined;
  let git: GitStat | undefined;
  let activeMs = 0;
  let activeSince: number | undefined;

  const stopSpinner = () => {
    if (timer) clearInterval(timer);
    timer = undefined;
  };

  const refreshGit = async (ctx: ExtensionContext) => {
    const [diffResult, statusResult] = await Promise.all([
      pi.exec("git", ["diff", "--numstat", "HEAD"], { cwd: ctx.cwd }).catch(() => undefined),
      pi.exec("git", ["status", "--porcelain=v2", "--branch"], { cwd: ctx.cwd }).catch(() => undefined),
    ]);
    if (!diffResult || diffResult.code !== 0 || !statusResult || statusResult.code !== 0) {
      git = undefined;
      return;
    }

    const next: GitStat = { added: 0, removed: 0, staged: 0, unstaged: 0, untracked: 0, ahead: 0, behind: 0 };
    for (const line of diffResult.stdout.split("\n")) {
      const [added, removed] = line.split("\t");
      if (added !== "-" && removed !== "-") {
        next.added += Number(added) || 0;
        next.removed += Number(removed) || 0;
      }
    }
    for (const line of statusResult.stdout.split("\n")) {
      const divergence = line.match(/^# branch\.ab \+(\d+) -(\d+)$/);
      if (divergence) {
        next.ahead = Number(divergence[1]);
        next.behind = Number(divergence[2]);
      } else if (line.startsWith("? ")) {
        next.untracked++;
      } else if (/^[12u] /.test(line)) {
        const status = line.slice(2, 4);
        if (status[0] !== ".") next.staged++;
        if (status[1] !== ".") next.unstaged++;
      }
    }
    git = next;
    tui?.requestRender();
  };

  pi.on("agent_start", () => {
    working = true;
    activeSince ??= Date.now();
    stopSpinner();
    timer = setInterval(() => {
      spinner = (spinner + 1) % SPINNER.length;
      tui?.requestRender();
    }, 80);
  });

  pi.on("agent_end", () => {
    working = false;
    if (activeSince !== undefined) activeMs += Date.now() - activeSince;
    activeSince = undefined;
    stopSpinner();
    tui?.requestRender();
  });

  pi.on("turn_end", (_event, ctx) => void refreshGit(ctx));
  pi.on("session_shutdown", () => {
    stopSpinner();
    tui = undefined;
  });

  pi.on("session_start", (_event, ctx) => {
    if (ctx.mode !== "tui") return;

    ctx.ui.setTitle(`pi · ${ctx.cwd.split("/").pop() || ctx.cwd}`);
    ctx.ui.setWorkingVisible(false);
    void refreshGit(ctx);

    ctx.ui.setFooter((instance, theme, footerData) => {
      const unsubscribe = footerData.onBranchChange(() => instance.requestRender());
      tui = instance;

      return {
        dispose: unsubscribe,
        invalidate() {},
        render(width: number): string[] {
          const stats = totals(ctx);
          const context = ctx.getContextUsage();
          const percent = Math.max(0, Math.min(100, Math.round(context?.percent ?? 0)));
          const filled = Math.round((percent / 100) * BAR_WIDTH);
          const level = percent >= 90 ? "error" : percent >= 70 ? "warning" : "success";
          const bar = theme.fg(level, "▓".repeat(filled)) + theme.fg("borderMuted", "░".repeat(BAR_WIDTH - filled));
          const model = ctx.model ? `${ctx.model.id}` : "no model";
          const project = ctx.cwd.split("/").pop() || ctx.cwd;
          const branch = footerData.getGitBranch();
          const statuses = [...footerData.getExtensionStatuses().values()].join(" · ");
          const elapsed = activeMs + (activeSince === undefined ? 0 : Date.now() - activeSince);

          let leftTop = `${theme.fg("accent", `󰧑 ${model}`)} ${theme.fg("thinkingText", pi.getThinkingLevel())}`;
          leftTop += ` ${theme.fg("borderMuted", "│")} ${theme.fg("toolTitle", ` ${project}`)}`;
          if (branch) leftTop += ` ${theme.fg("borderMuted", "│")} ${theme.fg("warning", ` ${branch}`)}`;
          if (git) {
            const state = [
              git.ahead ? theme.fg("success", `↑${git.ahead}`) : "",
              git.behind ? theme.fg("error", `↓${git.behind}`) : "",
              git.staged ? theme.fg("success", `+${git.staged}`) : "",
              git.unstaged ? theme.fg("warning", `!${git.unstaged}`) : "",
              git.untracked ? theme.fg("accent", `?${git.untracked}`) : "",
            ].filter(Boolean);
            if (state.length) leftTop += ` ${theme.fg("borderMuted", "[")}${state.join(" ")}${theme.fg("borderMuted", "]")}`;
            if (git.added || git.removed) {
              leftTop += ` ${theme.fg("success", `+${git.added}`)} ${theme.fg("error", `-${git.removed}`)}`;
            }
          }

          const rightTop = statuses ? `${theme.fg("accent", "✦")} ${statuses}` : "";
          const window = context?.contextWindow ?? ctx.model?.contextWindow;
          const used = context?.tokens ?? 0;
          const leftBottom = `${bar} ${theme.fg("dim", `${percent}%`)} ${theme.fg("borderMuted", "│")} ${theme.fg("muted", `${compactNumber(used)}/${window ? compactNumber(window) : "?"}`)}`;
          const promptTokens = stats.input + stats.cacheRead + stats.cacheWrite;
          const cache = stats.cacheRead && promptTokens
            ? ` ${theme.fg("borderMuted", "│")} ${theme.fg("muted", `󰆼 ${Math.round((stats.cacheRead / promptTokens) * 100)}%`)}`
            : "";
          const cost = stats.cost ? ` ${theme.fg("borderMuted", "│")} ${theme.fg("warning", `$${stats.cost.toFixed(2)}`)}` : "";
          const rightBottom = `${theme.fg("muted", `↑${compactNumber(stats.input)} ↓${compactNumber(stats.output)}`)}${cache}${cost} ${theme.fg("borderMuted", "│")} ${theme.fg("muted", `󱎫 ${formatDuration(elapsed)}`)}`;

          return [fitLine(leftTop, rightTop, width), fitLine(leftBottom, rightBottom, width), ""];
        },
      };
    });

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
        const activity = working ? theme.fg("accent", ` ${SPINNER[spinner]} working `) : theme.fg("muted", identity);
        lines[0] = fitBorder(activity, width, (text) => this.borderColor(text));
        return lines;
      }
    }

    ctx.ui.setEditorComponent((instance, theme, keybindings) => new PrettyEditor(instance, theme, keybindings));
  });
}
