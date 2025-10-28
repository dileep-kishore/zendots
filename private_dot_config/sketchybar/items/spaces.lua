local colors = require "colors"
local icons = require "icons"
local settings = require "settings"
local app_icons = require "helpers.app_icons"

local workspaces = {}
local query_all_workspaces =
    "aerospace list-workspaces --all --format '%{workspace}%{monitor-appkit-nsscreen-screens-id}' --json"
local query_visible_workspaces =
    "aerospace list-workspaces --visible --monitor all --format '%{workspace}%{monitor-appkit-nsscreen-screens-id}' --json"
local query_focused_workspace = "aerospace list-workspaces --focused"
local query_open_windows = "aerospace list-windows --monitor all --format '%{workspace}%{app-name}' --json"

local function withWindows(callback)
    sbar.exec(query_visible_workspaces, function(visible)
        sbar.exec(query_open_windows, function(windows)
            local open = {}
            for _, w in ipairs(windows) do
                open[w.workspace] = open[w.workspace] or {}
                table.insert(open[w.workspace], w["app-name"])
            end
            sbar.exec(query_focused_workspace, function(focused)
                callback {
                    open_windows = open,
                    focused_workspaces = focused,
                    visible_workspaces = visible,
                }
            end)
        end)
    end)
end

local function updateWindow(index, args)
    local open_apps = args.open_windows[index] or {}
    local icon_line = ""
    for _, app in ipairs(open_apps) do
        icon_line = icon_line .. " " .. (app_icons[app] or app_icons["Default"])
    end

    local is_focused = (index == args.focused_workspaces)
    local is_visible = false
    local monitor_id

    for _, v in ipairs(args.visible_workspaces) do
        if v.workspace == index then
            is_visible = true
            monitor_id = v["monitor-appkit-nsscreen-screens-id"]
            break
        end
    end

    sbar.animate("tanh", 10, function()
        local no_app = #open_apps == 0
        local label_string = no_app and " —" or icon_line
        local draw = not no_app or is_focused or is_visible

        workspaces[index]:set {
            icon = { drawing = draw },
            label = {
                drawing = draw,
                string = label_string,
                font = "sketchybar-app-font:Regular:16.0",
                y_offset = -1,
            },
            background = { drawing = is_visible },
            display = monitor_id,
            padding_left = draw and 1 or 0,
            padding_right = draw and 1 or 0,
        }
    end)
end

local function updateWindows()
    withWindows(function(args)
        for index in pairs(workspaces) do
            updateWindow(index, args)
        end
    end)
end

local function updateWorkspaceMonitor()
    sbar.exec(query_all_workspaces, function(data)
        local display_map = {}
        for _, entry in ipairs(data) do
            display_map[entry.workspace] = math.floor(entry["monitor-appkit-nsscreen-screens-id"])
        end
        for index, item in pairs(workspaces) do
            item:set { display = display_map[index] }
        end
    end)
end

-- Root toggle item
local root = sbar.add("item", {
    padding_left = -3,
    padding_right = 0,
    icon = {
        padding_left = 8,
        padding_right = 9,
        color = colors.grey,
        string = icons.switch.on,
    },
    label = {
        width = 0,
        padding_right = 8,
        string = "Spaces",
        color = colors.bg1,
    },
    background = {
        color = colors.with_alpha(colors.grey, 0.0),
        border_color = colors.with_alpha(colors.bg1, 0.0),
    },
})

-- Main setup
sbar.exec(query_all_workspaces, function(data)
    for _, entry in ipairs(data) do
        local i = entry.workspace
        local item = sbar.add("item", {
            icon = {
                drawing = false,
                string = tostring(i),
                padding_left = 10,
                padding_right = 5,
                font = { family = settings.font.numbers },
                color = colors.with_alpha(colors.white, 0.6),
                highlight_color = colors.white,
            },
            label = {
                padding_right = 10,
                color = colors.with_alpha(colors.white, 0.6),
                highlight_color = colors.white,
                font = "sketchybar-app-font:Regular:16.0",
                y_offset = -1,
            },
            padding_left = 2,
            padding_right = 2,
            background = {
                color = colors.bg3,
                height = 28,
                drawing = false,
            },
            click_script = "aerospace workspace " .. i,
            blur_radius = 30,
        })

        workspaces[i] = item

        item:subscribe("aerospace_workspace_change", function(env)
            local focused = env.FOCUSED_WORKSPACE
            sbar.animate("tanh", 10, function()
                item:set {
                    icon = { highlight = focused == i },
                    label = { highlight = focused == i },
                    background = { drawing = focused == i },
                }
            end)
        end)

        -- Optional: add bracket or popup visuals if needed here
    end

    -- Focused workspace highlight
    sbar.exec(query_focused_workspace, function(focused)
        focused = focused:match "^%s*(.-)%s*$"
        if workspaces[focused] then
            workspaces[focused]:set {
                icon = { highlight = true },
                label = { highlight = true },
                background = { drawing = true },
            }
        end
    end)

    -- Initial update
    updateWindows()
    updateWorkspaceMonitor()

    -- Events
    root:subscribe("aerospace_focus_change", updateWindows)
    root:subscribe("display_change", function()
        updateWorkspaceMonitor()
        updateWindows()
    end)
    root:subscribe("swap_menus_and_spaces", function()
        local on = root:query().icon.value == icons.switch.on
        root:set { icon = on and icons.switch.off or icons.switch.on }
    end)
    root:subscribe("mouse.clicked", function()
        sbar.trigger "swap_menus_and_spaces"
    end)
end)
